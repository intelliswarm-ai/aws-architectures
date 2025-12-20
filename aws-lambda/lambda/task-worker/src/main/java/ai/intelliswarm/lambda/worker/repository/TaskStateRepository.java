package ai.intelliswarm.lambda.worker.repository;

import ai.intelliswarm.lambda.common.model.Task;
import ai.intelliswarm.lambda.common.model.TaskPriority;
import ai.intelliswarm.lambda.common.model.TaskStatus;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.Key;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbAttribute;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;

import java.time.Instant;
import java.util.Map;
import java.util.Optional;

/**
 * Repository for persisting task state in DynamoDB.
 */
public class TaskStateRepository {

    private static final Logger logger = LoggerFactory.getLogger(TaskStateRepository.class);

    private final DynamoDbTable<TaskEntity> taskTable;

    public TaskStateRepository(DynamoDbClient dynamoDbClient, String tableName) {
        DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.builder()
                .dynamoDbClient(dynamoDbClient)
                .build();

        this.taskTable = enhancedClient.table(tableName, TableSchema.fromBean(TaskEntity.class));
    }

    /**
     * Save a task to DynamoDB.
     */
    public void save(Task task) {
        TaskEntity entity = TaskEntity.fromDomain(task);
        taskTable.putItem(entity);
        logger.debug("Saved task {} to DynamoDB", task.getTaskId());
    }

    /**
     * Find a task by ID.
     */
    public Optional<Task> findById(String taskId) {
        Key key = Key.builder().partitionValue(taskId).build();
        TaskEntity entity = taskTable.getItem(key);
        return Optional.ofNullable(entity).map(TaskEntity::toDomain);
    }

    /**
     * Update task status.
     */
    public void updateStatus(String taskId, TaskStatus status) {
        findById(taskId).ifPresent(task -> {
            task.setStatus(status);
            save(task);
        });
    }

    /**
     * Delete a task.
     */
    public void delete(String taskId) {
        Key key = Key.builder().partitionValue(taskId).build();
        taskTable.deleteItem(key);
        logger.debug("Deleted task {} from DynamoDB", taskId);
    }

    /**
     * DynamoDB entity for Task.
     */
    @DynamoDbBean
    public static class TaskEntity {

        private String taskId;
        private String taskType;
        private String status;
        private String priority;
        private String payload;
        private String createdAt;
        private String updatedAt;
        private String scheduledAt;
        private Integer retryCount;
        private String lastError;
        private Map<String, String> metadata;
        private Long ttl;

        public TaskEntity() {
        }

        @DynamoDbPartitionKey
        @DynamoDbAttribute("taskId")
        public String getTaskId() {
            return taskId;
        }

        public void setTaskId(String taskId) {
            this.taskId = taskId;
        }

        @DynamoDbAttribute("taskType")
        public String getTaskType() {
            return taskType;
        }

        public void setTaskType(String taskType) {
            this.taskType = taskType;
        }

        @DynamoDbAttribute("status")
        public String getStatus() {
            return status;
        }

        public void setStatus(String status) {
            this.status = status;
        }

        @DynamoDbAttribute("priority")
        public String getPriority() {
            return priority;
        }

        public void setPriority(String priority) {
            this.priority = priority;
        }

        @DynamoDbAttribute("payload")
        public String getPayload() {
            return payload;
        }

        public void setPayload(String payload) {
            this.payload = payload;
        }

        @DynamoDbAttribute("createdAt")
        public String getCreatedAt() {
            return createdAt;
        }

        public void setCreatedAt(String createdAt) {
            this.createdAt = createdAt;
        }

        @DynamoDbAttribute("updatedAt")
        public String getUpdatedAt() {
            return updatedAt;
        }

        public void setUpdatedAt(String updatedAt) {
            this.updatedAt = updatedAt;
        }

        @DynamoDbAttribute("scheduledAt")
        public String getScheduledAt() {
            return scheduledAt;
        }

        public void setScheduledAt(String scheduledAt) {
            this.scheduledAt = scheduledAt;
        }

        @DynamoDbAttribute("retryCount")
        public Integer getRetryCount() {
            return retryCount;
        }

        public void setRetryCount(Integer retryCount) {
            this.retryCount = retryCount;
        }

        @DynamoDbAttribute("lastError")
        public String getLastError() {
            return lastError;
        }

        public void setLastError(String lastError) {
            this.lastError = lastError;
        }

        @DynamoDbAttribute("metadata")
        public Map<String, String> getMetadata() {
            return metadata;
        }

        public void setMetadata(Map<String, String> metadata) {
            this.metadata = metadata;
        }

        @DynamoDbAttribute("ttl")
        public Long getTtl() {
            return ttl;
        }

        public void setTtl(Long ttl) {
            this.ttl = ttl;
        }

        public static TaskEntity fromDomain(Task task) {
            TaskEntity entity = new TaskEntity();
            entity.setTaskId(task.getTaskId());
            entity.setTaskType(task.getTaskType());
            entity.setStatus(task.getStatus() != null ? task.getStatus().name() : null);
            entity.setPriority(task.getPriority() != null ? task.getPriority().name() : null);
            entity.setPayload(task.getPayload());
            entity.setCreatedAt(task.getCreatedAt() != null ? task.getCreatedAt().toString() : null);
            entity.setUpdatedAt(Instant.now().toString());
            entity.setScheduledAt(task.getScheduledAt() != null ? task.getScheduledAt().toString() : null);
            entity.setRetryCount(task.getRetryCount());
            entity.setLastError(task.getLastError());
            entity.setMetadata(task.getMetadata());
            // TTL: 7 days from now
            entity.setTtl(Instant.now().plusSeconds(7 * 24 * 60 * 60).getEpochSecond());
            return entity;
        }

        public Task toDomain() {
            return Task.builder()
                    .taskId(taskId)
                    .taskType(taskType)
                    .status(status != null ? TaskStatus.valueOf(status) : null)
                    .priority(priority != null ? TaskPriority.valueOf(priority) : null)
                    .payload(payload)
                    .createdAt(createdAt != null ? Instant.parse(createdAt) : null)
                    .updatedAt(updatedAt != null ? Instant.parse(updatedAt) : null)
                    .scheduledAt(scheduledAt != null ? Instant.parse(scheduledAt) : null)
                    .retryCount(retryCount)
                    .lastError(lastError)
                    .metadata(metadata)
                    .build();
        }
    }
}
