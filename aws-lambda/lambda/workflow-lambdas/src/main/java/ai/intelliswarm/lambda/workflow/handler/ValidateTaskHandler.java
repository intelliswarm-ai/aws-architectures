package ai.intelliswarm.lambda.workflow.handler;

import ai.intelliswarm.lambda.common.exception.TaskValidationException;
import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.model.TaskStatus;
import ai.intelliswarm.lambda.common.model.WorkflowInput;
import ai.intelliswarm.lambda.common.model.WorkflowOutput;
import ai.intelliswarm.lambda.workflow.service.ValidationService;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.List;

/**
 * Step Functions Lambda handler for validating task input.
 * First step in the task processing workflow.
 */
public class ValidateTaskHandler implements RequestHandler<WorkflowInput, WorkflowOutput> {

    private static final Logger logger = LoggerFactory.getLogger(ValidateTaskHandler.class);

    private final ValidationService validationService;

    public ValidateTaskHandler() {
        this.validationService = new ValidationService();
    }

    public ValidateTaskHandler(ValidationService validationService) {
        this.validationService = validationService;
    }

    @Override
    public WorkflowOutput handleRequest(WorkflowInput input, Context context) {
        logger.info("Validating task: {} (execution: {})",
                input.getTaskId(), input.getExecutionId());

        Task task = input.getTask();

        try {
            List<String> errors = validationService.validate(task);

            if (!errors.isEmpty()) {
                logger.warn("Task {} failed validation: {}", task.getTaskId(), errors);
                throw new TaskValidationException(task.getTaskId(), errors);
            }

            // Update task status
            task.setStatus(TaskStatus.VALIDATING);

            logger.info("Task {} passed validation", task.getTaskId());

            return WorkflowOutput.builder()
                    .executionId(input.getExecutionId())
                    .taskId(task.getTaskId())
                    .task(task)
                    .success(true)
                    .message("Validation passed")
                    .completedAt(Instant.now())
                    .build();

        } catch (TaskValidationException e) {
            task.setStatus(TaskStatus.FAILED);
            task.setLastError(e.getMessage());
            throw e;
        }
    }
}
