package ai.intelliswarm.lambda.workflow.service;

import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.util.JsonUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * Service for processing tasks based on their type.
 * This is where the actual business logic would be implemented.
 */
public class ProcessingService {

    private static final Logger logger = LoggerFactory.getLogger(ProcessingService.class);
    private final Random random = new Random();

    /**
     * Process a task based on its type.
     *
     * @return Processing result as a map
     */
    public Map<String, Object> process(Task task) {
        logger.info("Processing task {} of type {}", task.getTaskId(), task.getTaskType());

        // Simulate processing based on task type
        return switch (task.getTaskType()) {
            case "DATA_PROCESSING" -> processDataTask(task);
            case "FILE_CLEANUP" -> processFileCleanupTask(task);
            case "REPORT_GENERATION" -> processReportTask(task);
            case "NOTIFICATION_DISPATCH" -> processNotificationTask(task);
            case "CACHE_REFRESH" -> processCacheRefreshTask(task);
            default -> processGenericTask(task);
        };
    }

    private Map<String, Object> processDataTask(Task task) {
        // Simulate data processing
        simulateWork(100, 500);

        int recordsProcessed = random.nextInt(1000) + 100;
        logger.info("Processed {} records for task {}", recordsProcessed, task.getTaskId());

        Map<String, Object> result = new HashMap<>();
        result.put("recordsProcessed", recordsProcessed);
        result.put("processingType", "DATA_PROCESSING");
        result.put("success", true);
        return result;
    }

    private Map<String, Object> processFileCleanupTask(Task task) {
        // Simulate file cleanup
        simulateWork(50, 200);

        int filesDeleted = random.nextInt(50) + 1;
        long bytesFreed = random.nextLong(1024 * 1024 * 100); // Up to 100MB

        logger.info("Cleaned up {} files ({} bytes) for task {}",
                filesDeleted, bytesFreed, task.getTaskId());

        Map<String, Object> result = new HashMap<>();
        result.put("filesDeleted", filesDeleted);
        result.put("bytesFreed", bytesFreed);
        result.put("processingType", "FILE_CLEANUP");
        result.put("success", true);
        return result;
    }

    private Map<String, Object> processReportTask(Task task) {
        // Simulate report generation
        simulateWork(200, 800);

        String reportId = "RPT-" + System.currentTimeMillis();
        logger.info("Generated report {} for task {}", reportId, task.getTaskId());

        Map<String, Object> result = new HashMap<>();
        result.put("reportId", reportId);
        result.put("format", "PDF");
        result.put("pages", random.nextInt(50) + 1);
        result.put("processingType", "REPORT_GENERATION");
        result.put("success", true);
        return result;
    }

    private Map<String, Object> processNotificationTask(Task task) {
        // Simulate notification dispatch
        simulateWork(20, 100);

        int recipientCount = random.nextInt(100) + 1;
        logger.info("Dispatched notifications to {} recipients for task {}",
                recipientCount, task.getTaskId());

        Map<String, Object> result = new HashMap<>();
        result.put("recipientCount", recipientCount);
        result.put("channel", "email");
        result.put("processingType", "NOTIFICATION_DISPATCH");
        result.put("success", true);
        return result;
    }

    private Map<String, Object> processCacheRefreshTask(Task task) {
        // Simulate cache refresh
        simulateWork(30, 150);

        logger.info("Refreshed cache for task {}", task.getTaskId());

        Map<String, Object> result = new HashMap<>();
        result.put("cacheEntriesRefreshed", random.nextInt(1000) + 10);
        result.put("ttlSeconds", random.nextInt(3600) + 300);
        result.put("processingType", "CACHE_REFRESH");
        result.put("success", true);
        return result;
    }

    private Map<String, Object> processGenericTask(Task task) {
        // Generic processing
        simulateWork(50, 200);

        logger.info("Completed generic processing for task {}", task.getTaskId());

        Map<String, Object> result = new HashMap<>();
        result.put("processingType", "GENERIC");
        result.put("success", true);
        return result;
    }

    /**
     * Simulate work by sleeping for a random duration.
     */
    private void simulateWork(int minMs, int maxMs) {
        try {
            int sleepTime = random.nextInt(maxMs - minMs) + minMs;
            Thread.sleep(sleepTime);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
