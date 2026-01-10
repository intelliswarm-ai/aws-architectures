"""Agent service for Bedrock Agent interactions."""

import uuid
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_bedrock_agent_runtime_client
from src.common.config import get_settings
from src.common.exceptions import AgentError, ValidationError
from src.common.models import (
    AgentAction,
    AgentActionType,
    AgentRequest,
    AgentResponse,
    RetrievalResult,
)

logger = Logger()
tracer = Tracer()


class AgentService:
    """Service for interacting with Bedrock Agents."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_bedrock_agent_runtime_client()

    @tracer.capture_method
    def invoke(self, request: AgentRequest) -> AgentResponse:
        """
        Invoke a Bedrock Agent.

        Args:
            request: Agent request with input text and session info

        Returns:
            AgentResponse with output and citations
        """
        agent_id = request.agent_id or self.settings.agent_id
        agent_alias_id = self.settings.agent_alias_id or "TSTALIASID"

        if not agent_id:
            raise ValidationError(
                message="Agent ID not configured",
                field="agent_id",
            )

        session_id = request.session_id or str(uuid.uuid4())

        logger.info(
            "Invoking Bedrock Agent",
            agent_id=agent_id,
            session_id=session_id,
            input_length=len(request.input_text),
        )

        try:
            # Build invoke request
            invoke_params = {
                "agentId": agent_id,
                "agentAliasId": agent_alias_id,
                "sessionId": session_id,
                "inputText": request.input_text,
            }

            if request.enable_trace:
                invoke_params["enableTrace"] = True

            if request.session_attributes:
                invoke_params["sessionState"] = {
                    "sessionAttributes": request.session_attributes,
                }
                if request.prompt_session_attributes:
                    invoke_params["sessionState"]["promptSessionAttributes"] = (
                        request.prompt_session_attributes
                    )

            # Invoke agent (streaming response)
            response = self.client.invoke_agent(**invoke_params)

            # Process streaming response
            output_text = ""
            citations = []
            actions = []
            trace_data = {}

            for event in response.get("completion", []):
                # Handle text chunks
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        output_text += chunk["bytes"].decode("utf-8")

                    # Extract citations from chunk attribution
                    if "attribution" in chunk:
                        for citation in chunk["attribution"].get("citations", []):
                            for ref in citation.get("retrievedReferences", []):
                                citations.append(self._parse_citation(ref))

                # Handle trace events
                if "trace" in event and request.enable_trace:
                    trace = event["trace"].get("trace", {})
                    self._process_trace(trace, trace_data, actions)

            logger.info(
                "Agent invocation completed",
                session_id=session_id,
                output_length=len(output_text),
                citation_count=len(citations),
            )

            return AgentResponse(
                session_id=session_id,
                output_text=output_text,
                citations=citations,
                actions=actions,
                trace=trace_data if request.enable_trace else None,
            )

        except self.client.exceptions.ResourceNotFoundException:
            raise AgentError(
                message=f"Agent {agent_id} not found",
                agent_id=agent_id,
                reason="not_found",
            )

        except self.client.exceptions.ThrottlingException:
            raise AgentError(
                message="Agent invocation throttled",
                agent_id=agent_id,
                session_id=session_id,
                reason="throttled",
            )

        except self.client.exceptions.ValidationException as e:
            raise ValidationError(
                message=f"Invalid agent request: {str(e)}",
                field="request",
            )

        except Exception as e:
            logger.exception("Agent invocation failed")
            raise AgentError(
                message=f"Agent invocation failed: {str(e)}",
                agent_id=agent_id,
                session_id=session_id,
            )

    def _parse_citation(self, ref: dict[str, Any]) -> RetrievalResult:
        """Parse a citation reference into RetrievalResult."""
        content = ref.get("content", {})
        location = ref.get("location", {})
        metadata = ref.get("metadata", {})

        return RetrievalResult(
            chunk_id=metadata.get("x-amz-bedrock-kb-chunk-id", str(uuid.uuid4())),
            document_id=metadata.get("x-amz-bedrock-kb-document-id", "unknown"),
            content=content.get("text", ""),
            score=ref.get("score", 0.0),
            source_uri=location.get("s3Location", {}).get("uri"),
        )

    def _process_trace(
        self,
        trace: dict[str, Any],
        trace_data: dict[str, Any],
        actions: list[AgentAction],
    ) -> None:
        """Process trace events to extract actions and debug info."""
        # Pre-processing trace
        if "preProcessingTrace" in trace:
            pre = trace["preProcessingTrace"]
            trace_data["preProcessing"] = {
                "inputText": pre.get("modelInvocationInput", {}).get("text", "")[:500],
            }

        # Orchestration trace
        if "orchestrationTrace" in trace:
            orch = trace["orchestrationTrace"]

            # Extract invocation input
            if "modelInvocationInput" in orch:
                trace_data["orchestration"] = {
                    "input": orch["modelInvocationInput"].get("text", "")[:500],
                }

            # Extract rationale
            if "rationale" in orch:
                trace_data["rationale"] = orch["rationale"].get("text", "")

            # Extract action group invocation
            if "invocationInput" in orch:
                inv = orch["invocationInput"]
                if "actionGroupInvocationInput" in inv:
                    ag = inv["actionGroupInvocationInput"]
                    actions.append(
                        AgentAction(
                            action_type=AgentActionType.RETRIEVE,
                            action_group=ag.get("actionGroupName", ""),
                            function_name=ag.get("function", ""),
                            parameters=ag.get("parameters", []),
                        )
                    )

                if "knowledgeBaseLookupInput" in inv:
                    kb = inv["knowledgeBaseLookupInput"]
                    actions.append(
                        AgentAction(
                            action_type=AgentActionType.SEARCH,
                            action_group="KnowledgeBase",
                            function_name="retrieve",
                            parameters={"query": kb.get("text", "")},
                        )
                    )

            # Extract observation (action results)
            if "observation" in orch:
                obs = orch["observation"]
                if "actionGroupInvocationOutput" in obs:
                    if actions:
                        actions[-1].result = obs["actionGroupInvocationOutput"].get("text", "")

        # Post-processing trace
        if "postProcessingTrace" in trace:
            post = trace["postProcessingTrace"]
            trace_data["postProcessing"] = {
                "output": post.get("modelInvocationOutput", {}).get("parsedResponse", {}).get("text", "")[:500],
            }

        # Failure trace
        if "failureTrace" in trace:
            fail = trace["failureTrace"]
            trace_data["failure"] = {
                "reason": fail.get("failureReason", "Unknown"),
            }

    @tracer.capture_method
    def end_session(self, agent_id: str, session_id: str) -> None:
        """
        End an agent session.

        Args:
            agent_id: Agent ID
            session_id: Session ID to end
        """
        agent_alias_id = self.settings.agent_alias_id or "TSTALIASID"

        try:
            # Send empty message with end session action
            self.client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText="",
                endSession=True,
            )

            logger.info(
                "Agent session ended",
                agent_id=agent_id,
                session_id=session_id,
            )

        except Exception as e:
            logger.warning(
                "Failed to end agent session",
                agent_id=agent_id,
                session_id=session_id,
                error=str(e),
            )
