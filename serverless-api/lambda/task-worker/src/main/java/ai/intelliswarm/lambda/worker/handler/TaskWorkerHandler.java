package ai.intelliswarm.lambda.worker.handler;

import ai.intelliswarm.lambda.common.config.AwsClientConfig;
import ai.intelliswarm.lambda.common.exception.NonRetryableException;
import ai.intelliswarm.lambda.common.exception.RetryableException;
import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.util.JsonUtil;
import ai.intelliswarm.lambda.worker.repository.TaskStateRepository;
import ai.intelliswarm.lambda.worker.service.TaskProcessorService;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSBatchResponse;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import com.amazonaws.services.lambda.runtime.events.SQSEvent.SQSMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * Lambda handler for processing tasks from SQS queue.
 * Implements partial batch failure - only failed messages are returned to the queue.
 */
public class TaskWorkerHandler implements RequestHandler<SQSEvent, SQSBatchResponse> {

    private static final Logger logger = LoggerFactory.getLogger(TaskWorkerHandler.class);

    private final TaskProcessorService processorService;

    /**
     * Default constructor used by Lambda runtime.
     */
    public TaskWorkerHandler() {
        TaskStateRepository stateRepository = new TaskStateRepository(
                AwsClientConfig.dynamoDbClient(),
                System.getenv("TASK_TABLE_NAME")
        );
        String stateMachineArn = System.getenv("STATE_MACHINE_ARN");
        this.processorService = new TaskProcessorService(stateRepository, stateMachineArn);
    }

    /**
     * Constructor for testing with dependency injection.
     */
    public TaskWorkerHandler(TaskProcessorService processorService) {
        this.processorService = processorService;
    }

    @Override
    public SQSBatchResponse handleRequest(SQSEvent event, Context context) {
        logger.info("Processing {} messages. Request ID: {}",
                event.getRecords().size(), context.getAwsRequestId());

        List<SQSBatchResponse.BatchItemFailure> failures = new ArrayList<>();

        for (SQSMessage message : event.getRecords()) {
            try {
                processMessage(message);
            } catch (RetryableException e) {
                logger.warn("Retryable error processing message {}: {}",
                        message.getMessageId(), e.getMessage());
                failures.add(new SQSBatchResponse.BatchItemFailure(message.getMessageId()));
            } catch (NonRetryableException e) {
                // Non-retryable errors - message will be deleted, logged for alerting
                logger.error("Non-retryable error processing message {}. Task will not be retried.",
                        message.getMessageId(), e);
            } catch (Exception e) {
                // Unexpected errors - treat as retryable
                logger.error("Unexpected error processing message {}",
                        message.getMessageId(), e);
                failures.add(new SQSBatchResponse.BatchItemFailure(message.getMessageId()));
            }
        }

        int successCount = event.getRecords().size() - failures.size();
        logger.info("Batch processing complete. Success: {}, Failures: {}",
                successCount, failures.size());

        return SQSBatchResponse.builder()
                .withBatchItemFailures(failures)
                .build();
    }

    /**
     * Process a single SQS message containing a task.
     */
    private void processMessage(SQSMessage message) {
        logger.debug("Processing message: {}", message.getMessageId());

        Task task = JsonUtil.fromJson(message.getBody(), Task.class);
        logger.info("Processing task: {} (type: {}, priority: {})",
                task.getTaskId(), task.getTaskType(), task.getPriority());

        processorService.process(task);

        logger.info("Task {} processed successfully", task.getTaskId());
    }
}
