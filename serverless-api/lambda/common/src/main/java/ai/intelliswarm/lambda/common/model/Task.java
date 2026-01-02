package ai.intelliswarm.lambda.common.model;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/**
 * Core domain model representing a task in the automation system.
 */
public class Task {

    private String taskId;
    private String taskType;
    private TaskStatus status;
    private TaskPriority priority;
    private String payload;
    private Instant createdAt;
    private Instant updatedAt;
    private Instant scheduledAt;
    private Integer retryCount;
    private String lastError;
    private Map<String, String> metadata;

    public Task() {
        this.taskId = UUID.randomUUID().toString();
        this.status = TaskStatus.PENDING;
        this.priority = TaskPriority.NORMAL;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
        this.retryCount = 0;
        this.metadata = new HashMap<>();
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private final Task task = new Task();

        public Builder taskId(String taskId) {
            task.taskId = taskId;
            return this;
        }

        public Builder taskType(String taskType) {
            task.taskType = taskType;
            return this;
        }

        public Builder status(TaskStatus status) {
            task.status = status;
            return this;
        }

        public Builder priority(TaskPriority priority) {
            task.priority = priority;
            return this;
        }

        public Builder payload(String payload) {
            task.payload = payload;
            return this;
        }

        public Builder createdAt(Instant createdAt) {
            task.createdAt = createdAt;
            return this;
        }

        public Builder updatedAt(Instant updatedAt) {
            task.updatedAt = updatedAt;
            return this;
        }

        public Builder scheduledAt(Instant scheduledAt) {
            task.scheduledAt = scheduledAt;
            return this;
        }

        public Builder retryCount(Integer retryCount) {
            task.retryCount = retryCount;
            return this;
        }

        public Builder lastError(String lastError) {
            task.lastError = lastError;
            return this;
        }

        public Builder metadata(Map<String, String> metadata) {
            task.metadata = metadata != null ? new HashMap<>(metadata) : new HashMap<>();
            return this;
        }

        public Builder addMetadata(String key, String value) {
            task.metadata.put(key, value);
            return this;
        }

        public Task build() {
            return task;
        }
    }

    // Getters and Setters
    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public String getTaskType() {
        return taskType;
    }

    public void setTaskType(String taskType) {
        this.taskType = taskType;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public void setStatus(TaskStatus status) {
        this.status = status;
        this.updatedAt = Instant.now();
    }

    public TaskPriority getPriority() {
        return priority;
    }

    public void setPriority(TaskPriority priority) {
        this.priority = priority;
    }

    public String getPayload() {
        return payload;
    }

    public void setPayload(String payload) {
        this.payload = payload;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }

    public Instant getScheduledAt() {
        return scheduledAt;
    }

    public void setScheduledAt(Instant scheduledAt) {
        this.scheduledAt = scheduledAt;
    }

    public Integer getRetryCount() {
        return retryCount;
    }

    public void setRetryCount(Integer retryCount) {
        this.retryCount = retryCount;
    }

    public String getLastError() {
        return lastError;
    }

    public void setLastError(String lastError) {
        this.lastError = lastError;
    }

    public Map<String, String> getMetadata() {
        return metadata;
    }

    public void setMetadata(Map<String, String> metadata) {
        this.metadata = metadata != null ? new HashMap<>(metadata) : new HashMap<>();
    }

    public void incrementRetryCount() {
        this.retryCount = (this.retryCount == null ? 0 : this.retryCount) + 1;
        this.updatedAt = Instant.now();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Task task = (Task) o;
        return Objects.equals(taskId, task.taskId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(taskId);
    }

    @Override
    public String toString() {
        return "Task{" +
                "taskId='" + taskId + '\'' +
                ", taskType='" + taskType + '\'' +
                ", status=" + status +
                ", priority=" + priority +
                ", retryCount=" + retryCount +
                '}';
    }
}
