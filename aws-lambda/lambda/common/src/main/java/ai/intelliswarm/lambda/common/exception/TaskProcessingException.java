package ai.intelliswarm.lambda.common.exception;

/**
 * Base exception for task processing errors.
 */
public class TaskProcessingException extends RuntimeException {

    private final String taskId;

    public TaskProcessingException(String message) {
        super(message);
        this.taskId = null;
    }

    public TaskProcessingException(String taskId, String message) {
        super(message);
        this.taskId = taskId;
    }

    public TaskProcessingException(String taskId, String message, Throwable cause) {
        super(message, cause);
        this.taskId = taskId;
    }

    public String getTaskId() {
        return taskId;
    }
}
