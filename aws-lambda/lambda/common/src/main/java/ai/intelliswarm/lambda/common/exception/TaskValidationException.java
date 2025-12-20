package ai.intelliswarm.lambda.common.exception;

import java.util.List;

/**
 * Exception thrown when task validation fails.
 */
public class TaskValidationException extends NonRetryableException {

    private final List<String> validationErrors;

    public TaskValidationException(String message) {
        super(message);
        this.validationErrors = List.of(message);
    }

    public TaskValidationException(String taskId, String message) {
        super(taskId, message);
        this.validationErrors = List.of(message);
    }

    public TaskValidationException(String taskId, List<String> validationErrors) {
        super(taskId, "Validation failed: " + String.join(", ", validationErrors));
        this.validationErrors = validationErrors;
    }

    public List<String> getValidationErrors() {
        return validationErrors;
    }
}
