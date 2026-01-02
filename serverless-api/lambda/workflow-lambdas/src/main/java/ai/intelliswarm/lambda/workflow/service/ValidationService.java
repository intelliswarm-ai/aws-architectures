package ai.intelliswarm.lambda.workflow.service;

import ai.intelliswarm.lambda.common.model.Task;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * Service for validating tasks before processing.
 */
public class ValidationService {

    private static final Logger logger = LoggerFactory.getLogger(ValidationService.class);
    private static final int MAX_PAYLOAD_SIZE = 256 * 1024; // 256KB

    /**
     * Validate a task and return list of validation errors.
     *
     * @return Empty list if validation passes, otherwise list of error messages
     */
    public List<String> validate(Task task) {
        List<String> errors = new ArrayList<>();

        // Required field validations
        if (task.getTaskId() == null || task.getTaskId().trim().isEmpty()) {
            errors.add("Task ID is required");
        }

        if (task.getTaskType() == null || task.getTaskType().trim().isEmpty()) {
            errors.add("Task type is required");
        }

        if (task.getPriority() == null) {
            errors.add("Task priority is required");
        }

        // Payload validation
        if (task.getPayload() != null && task.getPayload().length() > MAX_PAYLOAD_SIZE) {
            errors.add("Payload exceeds maximum size of " + MAX_PAYLOAD_SIZE + " bytes");
        }

        // Task type specific validation
        if (task.getTaskType() != null) {
            validateTaskType(task, errors);
        }

        if (!errors.isEmpty()) {
            logger.warn("Task {} validation failed with {} errors", task.getTaskId(), errors.size());
        }

        return errors;
    }

    /**
     * Validate task type specific requirements.
     */
    private void validateTaskType(Task task, List<String> errors) {
        switch (task.getTaskType()) {
            case "DATA_PROCESSING" -> validateDataProcessingTask(task, errors);
            case "REPORT_GENERATION" -> validateReportGenerationTask(task, errors);
            case "NOTIFICATION_DISPATCH" -> validateNotificationTask(task, errors);
            default -> {
                // Generic task types don't require additional validation
            }
        }
    }

    private void validateDataProcessingTask(Task task, List<String> errors) {
        if (task.getPayload() == null || task.getPayload().trim().isEmpty()) {
            errors.add("DATA_PROCESSING tasks require a payload with data source information");
        }
    }

    private void validateReportGenerationTask(Task task, List<String> errors) {
        if (task.getPayload() == null || !task.getPayload().contains("reportType")) {
            errors.add("REPORT_GENERATION tasks require a payload with reportType");
        }
    }

    private void validateNotificationTask(Task task, List<String> errors) {
        if (task.getPayload() == null || !task.getPayload().contains("channel")) {
            errors.add("NOTIFICATION_DISPATCH tasks require a payload with channel");
        }
    }
}
