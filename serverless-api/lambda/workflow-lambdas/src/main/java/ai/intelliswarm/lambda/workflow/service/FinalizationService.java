package ai.intelliswarm.lambda.workflow.service;

import ai.intelliswarm.lambda.common.model.Task;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;

/**
 * Service for finalizing task processing.
 * Handles cleanup, metrics publishing, and any post-processing logic.
 */
public class FinalizationService {

    private static final Logger logger = LoggerFactory.getLogger(FinalizationService.class);

    /**
     * Finalize a completed task.
     */
    public void finalize(Task task) {
        logger.info("Finalizing task: {} (type: {}, priority: {})",
                task.getTaskId(), task.getTaskType(), task.getPriority());

        // Calculate processing duration if we have creation time
        if (task.getCreatedAt() != null) {
            long durationMs = Instant.now().toEpochMilli() - task.getCreatedAt().toEpochMilli();
            logger.info("Task {} total duration: {}ms", task.getTaskId(), durationMs);
            task.addMetadata("totalDurationMs", String.valueOf(durationMs));
        }

        // Add finalization metadata
        task.addMetadata("finalizedAt", Instant.now().toString());
        task.addMetadata("finalizedBy", "FinalizationService");

        // Perform cleanup based on task type
        performCleanup(task);

        // Publish metrics
        publishMetrics(task);

        logger.info("Task {} finalization complete", task.getTaskId());
    }

    /**
     * Perform cleanup operations for the task.
     */
    private void performCleanup(Task task) {
        switch (task.getTaskType()) {
            case "FILE_CLEANUP" -> {
                // Clean up any temporary files created during processing
                logger.debug("Cleaning up temporary files for task {}", task.getTaskId());
            }
            case "REPORT_GENERATION" -> {
                // Archive or move generated report
                logger.debug("Archiving report for task {}", task.getTaskId());
            }
            default -> {
                // Generic cleanup
                logger.debug("Generic cleanup for task {}", task.getTaskId());
            }
        }
    }

    /**
     * Publish metrics about the completed task.
     * In a real implementation, this would push to CloudWatch Metrics.
     */
    private void publishMetrics(Task task) {
        // Log metrics that would be published to CloudWatch
        logger.info("METRIC: TaskCompleted - TaskId={}, TaskType={}, Priority={}, Status={}",
                task.getTaskId(),
                task.getTaskType(),
                task.getPriority(),
                task.getStatus());

        if (task.getRetryCount() != null && task.getRetryCount() > 0) {
            logger.info("METRIC: TaskRetried - TaskId={}, RetryCount={}",
                    task.getTaskId(), task.getRetryCount());
        }
    }
}
