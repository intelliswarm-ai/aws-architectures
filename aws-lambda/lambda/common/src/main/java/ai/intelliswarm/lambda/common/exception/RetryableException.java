package ai.intelliswarm.lambda.common.exception;

/**
 * Exception indicating a transient failure that can be retried.
 * When thrown during SQS processing, the message will be returned to the queue.
 */
public class RetryableException extends TaskProcessingException {

    private final int suggestedDelaySeconds;

    public RetryableException(String message) {
        super(message);
        this.suggestedDelaySeconds = 0;
    }

    public RetryableException(String taskId, String message) {
        super(taskId, message);
        this.suggestedDelaySeconds = 0;
    }

    public RetryableException(String taskId, String message, Throwable cause) {
        super(taskId, message, cause);
        this.suggestedDelaySeconds = 0;
    }

    public RetryableException(String taskId, String message, int suggestedDelaySeconds) {
        super(taskId, message);
        this.suggestedDelaySeconds = suggestedDelaySeconds;
    }

    public int getSuggestedDelaySeconds() {
        return suggestedDelaySeconds;
    }
}
