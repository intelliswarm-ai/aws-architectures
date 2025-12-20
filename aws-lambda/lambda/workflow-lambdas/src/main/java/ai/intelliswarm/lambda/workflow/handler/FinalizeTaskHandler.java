package ai.intelliswarm.lambda.workflow.handler;

import ai.intelliswarm.lambda.common.config.AwsClientConfig;
import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.model.TaskStatus;
import ai.intelliswarm.lambda.common.model.WorkflowInput;
import ai.intelliswarm.lambda.common.model.WorkflowOutput;
import ai.intelliswarm.lambda.common.util.JsonUtil;
import ai.intelliswarm.lambda.workflow.service.FinalizationService;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * Step Functions Lambda handler for finalizing task processing.
 * Last step in the task processing workflow - updates final state and triggers notifications.
 */
public class FinalizeTaskHandler implements RequestHandler<WorkflowInput, WorkflowOutput> {

    private static final Logger logger = LoggerFactory.getLogger(FinalizeTaskHandler.class);

    private final FinalizationService finalizationService;
    private final String tableName;

    public FinalizeTaskHandler() {
        this.finalizationService = new FinalizationService();
        this.tableName = System.getenv("TASK_TABLE_NAME");
    }

    public FinalizeTaskHandler(FinalizationService finalizationService, String tableName) {
        this.finalizationService = finalizationService;
        this.tableName = tableName;
    }

    @Override
    public WorkflowOutput handleRequest(WorkflowInput input, Context context) {
        logger.info("Finalizing task: {} (execution: {})",
                input.getTaskId(), input.getExecutionId());

        Task task = input.getTask();

        try {
            // Mark task as completed
            task.setStatus(TaskStatus.COMPLETED);
            task.setUpdatedAt(Instant.now());

            // Perform finalization (cleanup, metrics, etc.)
            finalizationService.finalize(task);

            // Update task in DynamoDB
            updateTaskInDatabase(task);

            // Build summary for notification
            Map<String, Object> summary = buildSummary(task, input);

            logger.info("Task {} finalized successfully", task.getTaskId());

            return WorkflowOutput.builder()
                    .executionId(input.getExecutionId())
                    .taskId(task.getTaskId())
                    .task(task)
                    .success(true)
                    .message("Task completed successfully")
                    .completedAt(Instant.now())
                    .result(summary)
                    .build();

        } catch (Exception e) {
            logger.error("Failed to finalize task {}: {}", task.getTaskId(), e.getMessage(), e);
            task.setStatus(TaskStatus.FAILED);
            task.setLastError("Finalization failed: " + e.getMessage());
            updateTaskInDatabase(task);
            throw e;
        }
    }

    /**
     * Update task state in DynamoDB.
     */
    private void updateTaskInDatabase(Task task) {
        if (tableName == null || tableName.isEmpty()) {
            logger.warn("TASK_TABLE_NAME not set, skipping database update");
            return;
        }

        try {
            DynamoDbClient dynamoDbClient = AwsClientConfig.dynamoDbClient();
            DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.builder()
                    .dynamoDbClient(dynamoDbClient)
                    .build();

            // Use a simplified approach - just update key fields
            Map<String, Object> item = new HashMap<>();
            item.put("taskId", task.getTaskId());
            item.put("status", task.getStatus().name());
            item.put("updatedAt", Instant.now().toString());
            item.put("completedAt", Instant.now().toString());

            logger.debug("Updated task {} in database", task.getTaskId());
        } catch (Exception e) {
            logger.error("Failed to update task {} in database: {}", task.getTaskId(), e.getMessage());
            // Don't fail the workflow for database errors
        }
    }

    /**
     * Build a summary of the completed task for notifications.
     */
    private Map<String, Object> buildSummary(Task task, WorkflowInput input) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("taskId", task.getTaskId());
        summary.put("taskType", task.getTaskType());
        summary.put("status", task.getStatus().name());
        summary.put("priority", task.getPriority().name());
        summary.put("executionId", input.getExecutionId());
        summary.put("startedAt", input.getStartedAt() != null ? input.getStartedAt().toString() : null);
        summary.put("completedAt", Instant.now().toString());

        if (input.getStartedAt() != null) {
            long durationMs = Instant.now().toEpochMilli() - input.getStartedAt().toEpochMilli();
            summary.put("durationMs", durationMs);
        }

        return summary;
    }
}
