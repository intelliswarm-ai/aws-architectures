package ai.intelliswarm.lambda.common.model;

import java.time.Instant;
import java.util.Map;

/**
 * Result of task processing.
 */
public class TaskResult {

    private String taskId;
    private boolean success;
    private String message;
    private Instant processedAt;
    private long durationMs;
    private Map<String, Object> output;

    public TaskResult() {
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private final TaskResult result = new TaskResult();

        public Builder taskId(String taskId) {
            result.taskId = taskId;
            return this;
        }

        public Builder success(boolean success) {
            result.success = success;
            return this;
        }

        public Builder message(String message) {
            result.message = message;
            return this;
        }

        public Builder processedAt(Instant processedAt) {
            result.processedAt = processedAt;
            return this;
        }

        public Builder durationMs(long durationMs) {
            result.durationMs = durationMs;
            return this;
        }

        public Builder output(Map<String, Object> output) {
            result.output = output;
            return this;
        }

        public TaskResult build() {
            return result;
        }
    }

    public static TaskResult success(String taskId, String message) {
        return builder()
                .taskId(taskId)
                .success(true)
                .message(message)
                .processedAt(Instant.now())
                .build();
    }

    public static TaskResult failure(String taskId, String message) {
        return builder()
                .taskId(taskId)
                .success(false)
                .message(message)
                .processedAt(Instant.now())
                .build();
    }

    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public boolean isSuccess() {
        return success;
    }

    public void setSuccess(boolean success) {
        this.success = success;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Instant getProcessedAt() {
        return processedAt;
    }

    public void setProcessedAt(Instant processedAt) {
        this.processedAt = processedAt;
    }

    public long getDurationMs() {
        return durationMs;
    }

    public void setDurationMs(long durationMs) {
        this.durationMs = durationMs;
    }

    public Map<String, Object> getOutput() {
        return output;
    }

    public void setOutput(Map<String, Object> output) {
        this.output = output;
    }
}
