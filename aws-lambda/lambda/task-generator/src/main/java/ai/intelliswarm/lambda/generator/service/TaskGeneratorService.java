package ai.intelliswarm.lambda.generator.service;

import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.model.TaskPriority;
import ai.intelliswarm.lambda.common.model.TaskStatus;
import ai.intelliswarm.lambda.generator.repository.TaskQueueRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.UUID;

/**
 * Service responsible for generating tasks based on business logic.
 */
public class TaskGeneratorService {

    private static final Logger logger = LoggerFactory.getLogger(TaskGeneratorService.class);
    private static final int DEFAULT_BATCH_SIZE = 5;
    private static final String[] TASK_TYPES = {
            "DATA_PROCESSING",
            "FILE_CLEANUP",
            "REPORT_GENERATION",
            "NOTIFICATION_DISPATCH",
            "CACHE_REFRESH"
    };

    private final TaskQueueRepository queueRepository;
    private final Random random;
    private final int batchSize;

    public TaskGeneratorService(TaskQueueRepository queueRepository) {
        this(queueRepository, DEFAULT_BATCH_SIZE);
    }

    public TaskGeneratorService(TaskQueueRepository queueRepository, int batchSize) {
        this.queueRepository = queueRepository;
        this.batchSize = batchSize;
        this.random = new Random();
    }

    /**
     * Generate a batch of tasks and queue them for processing.
     *
     * @return Number of tasks generated and queued
     */
    public int generateAndQueueTasks() {
        List<Task> tasks = generateTasks(batchSize);
        logger.info("Generated {} tasks for queuing", tasks.size());

        int queued = queueRepository.sendBatch(tasks);
        logger.info("Successfully queued {} tasks", queued);

        return queued;
    }

    /**
     * Generate a list of tasks.
     */
    private List<Task> generateTasks(int count) {
        List<Task> tasks = new ArrayList<>(count);
        Instant now = Instant.now();

        for (int i = 0; i < count; i++) {
            Task task = createTask(now, i);
            tasks.add(task);
        }

        return tasks;
    }

    /**
     * Create a single task with randomized properties.
     */
    private Task createTask(Instant timestamp, int index) {
        String taskType = TASK_TYPES[random.nextInt(TASK_TYPES.length)];
        TaskPriority priority = TaskPriority.values()[random.nextInt(TaskPriority.values().length)];

        return Task.builder()
                .taskId(UUID.randomUUID().toString())
                .taskType(taskType)
                .status(TaskStatus.QUEUED)
                .priority(priority)
                .payload(generatePayload(taskType, index))
                .createdAt(timestamp)
                .updatedAt(timestamp)
                .scheduledAt(timestamp)
                .retryCount(0)
                .addMetadata("generatedBy", "TaskGeneratorService")
                .addMetadata("batchIndex", String.valueOf(index))
                .addMetadata("timestamp", timestamp.toString())
                .build();
    }

    /**
     * Generate task-type specific payload.
     */
    private String generatePayload(String taskType, int index) {
        return switch (taskType) {
            case "DATA_PROCESSING" -> String.format(
                    "{\"dataSource\": \"source-%d\", \"recordCount\": %d}",
                    index, random.nextInt(1000) + 100
            );
            case "FILE_CLEANUP" -> String.format(
                    "{\"directory\": \"/tmp/cleanup-%d\", \"olderThanDays\": %d}",
                    index, random.nextInt(30) + 1
            );
            case "REPORT_GENERATION" -> String.format(
                    "{\"reportType\": \"daily\", \"format\": \"PDF\", \"recipients\": [\"user-%d@example.com\"]}",
                    index
            );
            case "NOTIFICATION_DISPATCH" -> String.format(
                    "{\"channel\": \"email\", \"templateId\": \"template-%d\", \"recipientCount\": %d}",
                    index, random.nextInt(100) + 1
            );
            case "CACHE_REFRESH" -> String.format(
                    "{\"cacheKey\": \"cache-%d\", \"ttlSeconds\": %d}",
                    index, random.nextInt(3600) + 300
            );
            default -> String.format("{\"taskIndex\": %d}", index);
        };
    }
}
