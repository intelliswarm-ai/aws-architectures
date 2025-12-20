package ai.intelliswarm.lambda.worker.service;

import ai.intelliswarm.lambda.common.config.AwsClientConfig;
import ai.intelliswarm.lambda.common.exception.NonRetryableException;
import ai.intelliswarm.lambda.common.exception.RetryableException;
import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.model.TaskStatus;
import ai.intelliswarm.lambda.common.model.WorkflowInput;
import ai.intelliswarm.lambda.common.util.JsonUtil;
import ai.intelliswarm.lambda.worker.repository.TaskStateRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awssdk.services.sfn.SfnClient;
import software.amazon.awssdk.services.sfn.model.StartExecutionRequest;
import software.amazon.awssdk.services.sfn.model.StartExecutionResponse;

import java.time.Instant;
import java.util.UUID;

/**
 * Service responsible for processing tasks.
 * Updates task state and triggers Step Functions workflow.
 */
public class TaskProcessorService {

    private static final Logger logger = LoggerFactory.getLogger(TaskProcessorService.class);
    private static final int MAX_RETRY_COUNT = 3;

    private final TaskStateRepository stateRepository;
    private final SfnClient sfnClient;
    private final String stateMachineArn;

    public TaskProcessorService(TaskStateRepository stateRepository, String stateMachineArn) {
        this.stateRepository = stateRepository;
        this.sfnClient = SfnClient.builder()
                .region(AwsClientConfig.getRegion())
                .build();
        this.stateMachineArn = stateMachineArn;
    }

    /**
     * Constructor for testing.
     */
    public TaskProcessorService(TaskStateRepository stateRepository, SfnClient sfnClient, String stateMachineArn) {
        this.stateRepository = stateRepository;
        this.sfnClient = sfnClient;
        this.stateMachineArn = stateMachineArn;
    }

    /**
     * Process a task by updating state and triggering workflow.
     */
    public void process(Task task) {
        validateTask(task);
        checkRetryLimit(task);

        // Update task status to IN_PROGRESS
        task.setStatus(TaskStatus.IN_PROGRESS);
        stateRepository.save(task);

        try {
            // Trigger Step Functions workflow for complex processing
            String executionArn = triggerWorkflow(task);
            logger.info("Started workflow execution: {}", executionArn);

            // Update task with execution reference
            task.addMetadata("executionArn", executionArn);
            stateRepository.save(task);

        } catch (Exception e) {
            handleProcessingError(task, e);
        }
    }

    /**
     * Validate the task before processing.
     */
    private void validateTask(Task task) {
        if (task.getTaskId() == null || task.getTaskId().isEmpty()) {
            throw new NonRetryableException("Task ID is required");
        }

        if (task.getTaskType() == null || task.getTaskType().isEmpty()) {
            throw new NonRetryableException(task.getTaskId(), "Task type is required");
        }
    }

    /**
     * Check if the task has exceeded retry limit.
     */
    private void checkRetryLimit(Task task) {
        if (task.getRetryCount() != null && task.getRetryCount() >= MAX_RETRY_COUNT) {
            task.setStatus(TaskStatus.FAILED);
            task.setLastError("Exceeded maximum retry count of " + MAX_RETRY_COUNT);
            stateRepository.save(task);

            throw new NonRetryableException(task.getTaskId(),
                    "Task exceeded maximum retry count: " + MAX_RETRY_COUNT);
        }
    }

    /**
     * Trigger Step Functions workflow for the task.
     */
    private String triggerWorkflow(Task task) {
        WorkflowInput workflowInput = WorkflowInput.builder()
                .executionId(UUID.randomUUID().toString())
                .taskId(task.getTaskId())
                .task(task)
                .startedAt(Instant.now())
                .build();

        String inputJson = JsonUtil.toJson(workflowInput);

        StartExecutionRequest request = StartExecutionRequest.builder()
                .stateMachineArn(stateMachineArn)
                .name("task-" + task.getTaskId() + "-" + System.currentTimeMillis())
                .input(inputJson)
                .build();

        StartExecutionResponse response = sfnClient.startExecution(request);
        return response.executionArn();
    }

    /**
     * Handle errors during task processing.
     */
    private void handleProcessingError(Task task, Exception e) {
        task.incrementRetryCount();
        task.setLastError(e.getMessage());
        task.setStatus(TaskStatus.PENDING);
        stateRepository.save(task);

        logger.error("Error processing task {}. Retry count: {}",
                task.getTaskId(), task.getRetryCount(), e);

        throw new RetryableException(task.getTaskId(),
                "Failed to process task: " + e.getMessage(), e);
    }
}
