package ai.intelliswarm.lambda.workflow.handler;

import ai.intelliswarm.lambda.common.exception.RetryableException;
import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.model.TaskStatus;
import ai.intelliswarm.lambda.common.model.WorkflowInput;
import ai.intelliswarm.lambda.common.model.WorkflowOutput;
import ai.intelliswarm.lambda.workflow.service.ProcessingService;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.Map;

/**
 * Step Functions Lambda handler for core task processing.
 * Second step in the task processing workflow.
 */
public class ProcessTaskHandler implements RequestHandler<WorkflowInput, WorkflowOutput> {

    private static final Logger logger = LoggerFactory.getLogger(ProcessTaskHandler.class);

    private final ProcessingService processingService;

    public ProcessTaskHandler() {
        this.processingService = new ProcessingService();
    }

    public ProcessTaskHandler(ProcessingService processingService) {
        this.processingService = processingService;
    }

    @Override
    public WorkflowOutput handleRequest(WorkflowInput input, Context context) {
        logger.info("Processing task: {} (type: {}, execution: {})",
                input.getTaskId(), input.getTask().getTaskType(), input.getExecutionId());

        Task task = input.getTask();
        long startTime = System.currentTimeMillis();

        try {
            // Update task status
            task.setStatus(TaskStatus.PROCESSING);

            // Execute task-specific processing
            Map<String, Object> result = processingService.process(task);

            long durationMs = System.currentTimeMillis() - startTime;
            logger.info("Task {} processed successfully in {}ms", task.getTaskId(), durationMs);

            return WorkflowOutput.builder()
                    .executionId(input.getExecutionId())
                    .taskId(task.getTaskId())
                    .task(task)
                    .success(true)
                    .message("Processing completed successfully")
                    .completedAt(Instant.now())
                    .result(result)
                    .build();

        } catch (Exception e) {
            long durationMs = System.currentTimeMillis() - startTime;
            logger.error("Task {} processing failed after {}ms: {}",
                    task.getTaskId(), durationMs, e.getMessage(), e);

            task.incrementRetryCount();
            task.setLastError(e.getMessage());

            throw new RetryableException(task.getTaskId(),
                    "Processing failed: " + e.getMessage(), e);
        }
    }
}
