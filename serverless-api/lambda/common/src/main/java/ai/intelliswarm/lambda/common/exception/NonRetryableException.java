package ai.intelliswarm.lambda.common.exception;

/**
 * Exception indicating a permanent failure that should not be retried.
 * When thrown during SQS processing, the message will be deleted (not returned to queue).
 */
public class NonRetryableException extends TaskProcessingException {

    public NonRetryableException(String message) {
        super(message);
    }

    public NonRetryableException(String taskId, String message) {
        super(taskId, message);
    }

    public NonRetryableException(String taskId, String message, Throwable cause) {
        super(taskId, message, cause);
    }
}
