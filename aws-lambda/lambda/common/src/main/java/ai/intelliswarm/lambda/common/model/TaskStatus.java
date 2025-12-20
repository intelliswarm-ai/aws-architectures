package ai.intelliswarm.lambda.common.model;

/**
 * Represents the lifecycle status of a task.
 */
public enum TaskStatus {
    PENDING,
    QUEUED,
    IN_PROGRESS,
    VALIDATING,
    PROCESSING,
    COMPLETED,
    FAILED,
    CANCELLED
}
