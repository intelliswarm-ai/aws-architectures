package ai.intelliswarm.lambda.generator.repository;

import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.util.JsonUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.MessageAttributeValue;
import software.amazon.awssdk.services.sqs.model.SendMessageBatchRequest;
import software.amazon.awssdk.services.sqs.model.SendMessageBatchRequestEntry;
import software.amazon.awssdk.services.sqs.model.SendMessageBatchResponse;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Repository for publishing tasks to SQS queue.
 */
public class TaskQueueRepository {

    private static final Logger logger = LoggerFactory.getLogger(TaskQueueRepository.class);
    private static final int MAX_BATCH_SIZE = 10; // SQS limit

    private final SqsClient sqsClient;
    private final String queueUrl;

    public TaskQueueRepository(SqsClient sqsClient, String queueUrl) {
        this.sqsClient = sqsClient;
        this.queueUrl = queueUrl;
    }

    /**
     * Send a single task to the queue.
     */
    public void send(Task task) {
        String messageBody = JsonUtil.toJson(task);

        SendMessageRequest request = SendMessageRequest.builder()
                .queueUrl(queueUrl)
                .messageBody(messageBody)
                .messageAttributes(buildMessageAttributes(task))
                .build();

        sqsClient.sendMessage(request);
        logger.debug("Sent task {} to queue", task.getTaskId());
    }

    /**
     * Send multiple tasks to the queue in batches.
     *
     * @return Number of tasks successfully sent
     */
    public int sendBatch(List<Task> tasks) {
        if (tasks == null || tasks.isEmpty()) {
            return 0;
        }

        int successCount = 0;
        List<List<Task>> batches = partition(tasks, MAX_BATCH_SIZE);

        for (List<Task> batch : batches) {
            successCount += sendBatchInternal(batch);
        }

        return successCount;
    }

    /**
     * Send a single batch of up to 10 messages.
     */
    private int sendBatchInternal(List<Task> tasks) {
        List<SendMessageBatchRequestEntry> entries = new ArrayList<>();

        for (int i = 0; i < tasks.size(); i++) {
            Task task = tasks.get(i);
            String messageBody = JsonUtil.toJson(task);

            SendMessageBatchRequestEntry entry = SendMessageBatchRequestEntry.builder()
                    .id(String.valueOf(i))
                    .messageBody(messageBody)
                    .messageAttributes(buildMessageAttributes(task))
                    .build();

            entries.add(entry);
        }

        SendMessageBatchRequest request = SendMessageBatchRequest.builder()
                .queueUrl(queueUrl)
                .entries(entries)
                .build();

        SendMessageBatchResponse response = sqsClient.sendMessageBatch(request);

        int successCount = response.successful().size();
        int failureCount = response.failed().size();

        if (failureCount > 0) {
            logger.warn("Failed to send {} messages to queue", failureCount);
            response.failed().forEach(failure ->
                    logger.warn("Failed message ID {}: {} - {}",
                            failure.id(), failure.code(), failure.message())
            );
        }

        return successCount;
    }

    /**
     * Build message attributes for a task.
     */
    private Map<String, MessageAttributeValue> buildMessageAttributes(Task task) {
        return Map.of(
                "taskId", MessageAttributeValue.builder()
                        .dataType("String")
                        .stringValue(task.getTaskId())
                        .build(),
                "taskType", MessageAttributeValue.builder()
                        .dataType("String")
                        .stringValue(task.getTaskType())
                        .build(),
                "priority", MessageAttributeValue.builder()
                        .dataType("String")
                        .stringValue(task.getPriority().name())
                        .build()
        );
    }

    /**
     * Partition a list into sublists of maximum size.
     */
    private <T> List<List<T>> partition(List<T> list, int size) {
        List<List<T>> partitions = new ArrayList<>();
        for (int i = 0; i < list.size(); i += size) {
            partitions.add(list.subList(i, Math.min(i + size, list.size())));
        }
        return partitions;
    }
}
