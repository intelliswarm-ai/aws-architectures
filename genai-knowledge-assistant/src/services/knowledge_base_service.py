"""Knowledge Base service for Bedrock Knowledge Bases operations."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_bedrock_agent_client, get_bedrock_agent_runtime_client
from src.common.config import get_settings
from src.common.exceptions import KnowledgeBaseError, ResourceNotFoundError

logger = Logger()
tracer = Tracer()


class KnowledgeBaseService:
    """Service for managing Bedrock Knowledge Bases."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.agent_client = get_bedrock_agent_client()
        self.runtime_client = get_bedrock_agent_runtime_client()

    @tracer.capture_method
    def retrieve(
        self,
        query: str,
        knowledge_base_id: str | None = None,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant documents from Knowledge Base.

        Args:
            query: Search query
            knowledge_base_id: Knowledge Base ID (uses default if not provided)
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of retrieval results with content and metadata
        """
        knowledge_base_id = knowledge_base_id or self.settings.knowledge_base_id
        top_k = top_k or self.settings.retrieval_top_k

        if not knowledge_base_id:
            raise KnowledgeBaseError(
                message="Knowledge Base ID not configured",
                operation="retrieve",
            )

        retrieval_config = {
            "vectorSearchConfiguration": {
                "numberOfResults": top_k,
            }
        }

        # Add filters if provided
        if filters:
            retrieval_config["vectorSearchConfiguration"]["filter"] = self._build_filter(filters)

        try:
            response = self.runtime_client.retrieve(
                knowledgeBaseId=knowledge_base_id,
                retrievalQuery={"text": query},
                retrievalConfiguration=retrieval_config,
            )

            results = []
            for result in response.get("retrievalResults", []):
                content = result.get("content", {})
                location = result.get("location", {})
                metadata = result.get("metadata", {})

                results.append({
                    "content": content.get("text", ""),
                    "score": result.get("score", 0),
                    "source_uri": location.get("s3Location", {}).get("uri", ""),
                    "metadata": metadata,
                })

            logger.info(
                "Retrieved documents",
                query_length=len(query),
                result_count=len(results),
            )

            return results

        except self.runtime_client.exceptions.ResourceNotFoundException:
            raise ResourceNotFoundError(
                message=f"Knowledge Base {knowledge_base_id} not found",
                resource_type="KnowledgeBase",
                resource_id=knowledge_base_id,
            )
        except Exception as e:
            logger.exception("Retrieval failed")
            raise KnowledgeBaseError(
                message=f"Retrieval failed: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                operation="retrieve",
            )

    @tracer.capture_method
    def retrieve_and_generate(
        self,
        query: str,
        knowledge_base_id: str | None = None,
        model_id: str | None = None,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve documents and generate response using Knowledge Base RAG.

        Args:
            query: User query
            knowledge_base_id: Knowledge Base ID
            model_id: Model ID for generation
            top_k: Number of documents to retrieve

        Returns:
            Dict with generated response and citations
        """
        knowledge_base_id = knowledge_base_id or self.settings.knowledge_base_id
        model_id = model_id or self.settings.bedrock_model_id
        top_k = top_k or self.settings.retrieval_top_k

        if not knowledge_base_id:
            raise KnowledgeBaseError(
                message="Knowledge Base ID not configured",
                operation="retrieve_and_generate",
            )

        try:
            response = self.runtime_client.retrieve_and_generate(
                input={"text": query},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": knowledge_base_id,
                        "modelArn": f"arn:aws:bedrock:{self.settings.aws_region}::foundation-model/{model_id}",
                        "retrievalConfiguration": {
                            "vectorSearchConfiguration": {
                                "numberOfResults": top_k,
                            }
                        },
                    },
                },
            )

            # Extract citations
            citations = []
            for citation in response.get("citations", []):
                for ref in citation.get("retrievedReferences", []):
                    location = ref.get("location", {})
                    citations.append({
                        "content": ref.get("content", {}).get("text", ""),
                        "source_uri": location.get("s3Location", {}).get("uri", ""),
                        "metadata": ref.get("metadata", {}),
                    })

            return {
                "answer": response.get("output", {}).get("text", ""),
                "citations": citations,
                "session_id": response.get("sessionId"),
            }

        except self.runtime_client.exceptions.ResourceNotFoundException:
            raise ResourceNotFoundError(
                message=f"Knowledge Base {knowledge_base_id} not found",
                resource_type="KnowledgeBase",
                resource_id=knowledge_base_id,
            )
        except Exception as e:
            logger.exception("Retrieve and generate failed")
            raise KnowledgeBaseError(
                message=f"Retrieve and generate failed: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                operation="retrieve_and_generate",
            )

    @tracer.capture_method
    def start_ingestion_job(
        self,
        knowledge_base_id: str | None = None,
        data_source_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Start a data source ingestion job.

        Args:
            knowledge_base_id: Knowledge Base ID
            data_source_id: Data Source ID

        Returns:
            Ingestion job details
        """
        knowledge_base_id = knowledge_base_id or self.settings.knowledge_base_id
        data_source_id = data_source_id or self.settings.knowledge_base_data_source_id

        if not knowledge_base_id or not data_source_id:
            raise KnowledgeBaseError(
                message="Knowledge Base ID and Data Source ID required",
                operation="start_ingestion_job",
            )

        try:
            response = self.agent_client.start_ingestion_job(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=data_source_id,
            )

            job = response.get("ingestionJob", {})
            logger.info(
                "Ingestion job started",
                job_id=job.get("ingestionJobId"),
                knowledge_base_id=knowledge_base_id,
            )

            return {
                "ingestionJobId": job.get("ingestionJobId"),
                "status": job.get("status"),
                "startedAt": str(job.get("startedAt", "")),
            }

        except Exception as e:
            logger.exception("Failed to start ingestion job")
            raise KnowledgeBaseError(
                message=f"Failed to start ingestion: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                operation="start_ingestion_job",
            )

    @tracer.capture_method
    def get_ingestion_job_status(
        self,
        knowledge_base_id: str,
        data_source_id: str,
        job_id: str,
    ) -> dict[str, Any]:
        """
        Get the status of an ingestion job.

        Args:
            knowledge_base_id: Knowledge Base ID
            data_source_id: Data Source ID
            job_id: Ingestion job ID

        Returns:
            Job status details
        """
        try:
            response = self.agent_client.get_ingestion_job(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=data_source_id,
                ingestionJobId=job_id,
            )

            job = response.get("ingestionJob", {})
            stats = job.get("statistics", {})

            return {
                "ingestionJobId": job.get("ingestionJobId"),
                "status": job.get("status"),
                "startedAt": str(job.get("startedAt", "")),
                "updatedAt": str(job.get("updatedAt", "")),
                "statistics": {
                    "numberOfDocumentsScanned": stats.get("numberOfDocumentsScanned", 0),
                    "numberOfDocumentsFailed": stats.get("numberOfDocumentsFailed", 0),
                    "numberOfNewDocumentsIndexed": stats.get("numberOfNewDocumentsIndexed", 0),
                    "numberOfModifiedDocumentsIndexed": stats.get("numberOfModifiedDocumentsIndexed", 0),
                    "numberOfDocumentsDeleted": stats.get("numberOfDocumentsDeleted", 0),
                },
                "failureReasons": job.get("failureReasons", []),
            }

        except Exception as e:
            logger.exception("Failed to get job status")
            raise KnowledgeBaseError(
                message=f"Failed to get job status: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                operation="get_ingestion_job",
            )

    @tracer.capture_method
    def list_ingestion_jobs(
        self,
        knowledge_base_id: str | None = None,
        data_source_id: str | None = None,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        List recent ingestion jobs.

        Args:
            knowledge_base_id: Knowledge Base ID
            data_source_id: Data Source ID
            max_results: Maximum number of jobs to return

        Returns:
            List of ingestion jobs
        """
        knowledge_base_id = knowledge_base_id or self.settings.knowledge_base_id
        data_source_id = data_source_id or self.settings.knowledge_base_data_source_id

        try:
            response = self.agent_client.list_ingestion_jobs(
                knowledgeBaseId=knowledge_base_id,
                dataSourceId=data_source_id,
                maxResults=max_results,
                sortBy={"attribute": "STARTED_AT", "order": "DESCENDING"},
            )

            jobs = []
            for job in response.get("ingestionJobSummaries", []):
                jobs.append({
                    "ingestionJobId": job.get("ingestionJobId"),
                    "status": job.get("status"),
                    "startedAt": str(job.get("startedAt", "")),
                    "updatedAt": str(job.get("updatedAt", "")),
                })

            return jobs

        except Exception as e:
            logger.exception("Failed to list ingestion jobs")
            raise KnowledgeBaseError(
                message=f"Failed to list jobs: {str(e)}",
                knowledge_base_id=knowledge_base_id,
                operation="list_ingestion_jobs",
            )

    @tracer.capture_method
    def list_knowledge_bases(self) -> list[dict[str, Any]]:
        """
        List available knowledge bases.

        Returns:
            List of knowledge base summaries
        """
        try:
            response = self.agent_client.list_knowledge_bases(maxResults=100)

            knowledge_bases = []
            for kb in response.get("knowledgeBaseSummaries", []):
                knowledge_bases.append({
                    "knowledgeBaseId": kb.get("knowledgeBaseId"),
                    "name": kb.get("name"),
                    "status": kb.get("status"),
                    "updatedAt": str(kb.get("updatedAt", "")),
                })

            return knowledge_bases

        except Exception as e:
            logger.exception("Failed to list knowledge bases")
            raise KnowledgeBaseError(
                message=f"Failed to list knowledge bases: {str(e)}",
                operation="list_knowledge_bases",
            )

    def _build_filter(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Build filter configuration for retrieval."""
        # Simple AND filter for now
        filter_conditions = []

        for key, value in filters.items():
            if isinstance(value, list):
                filter_conditions.append({
                    "in": {"key": key, "value": value}
                })
            else:
                filter_conditions.append({
                    "equals": {"key": key, "value": value}
                })

        if len(filter_conditions) == 1:
            return filter_conditions[0]

        return {"andAll": filter_conditions}
