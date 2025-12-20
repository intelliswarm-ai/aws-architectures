package ai.intelliswarm.lambda.common.model;

import java.time.Instant;
import java.util.Map;

/**
 * Output model for Step Functions workflow states.
 */
public class WorkflowOutput {

    private String executionId;
    private String taskId;
    private Task task;
    private boolean success;
    private String message;
    private Instant completedAt;
    private Map<String, Object> result;

    public WorkflowOutput() {
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private final WorkflowOutput output = new WorkflowOutput();

        public Builder executionId(String executionId) {
            output.executionId = executionId;
            return this;
        }

        public Builder taskId(String taskId) {
            output.taskId = taskId;
            return this;
        }

        public Builder task(Task task) {
            output.task = task;
            return this;
        }

        public Builder success(boolean success) {
            output.success = success;
            return this;
        }

        public Builder message(String message) {
            output.message = message;
            return this;
        }

        public Builder completedAt(Instant completedAt) {
            output.completedAt = completedAt;
            return this;
        }

        public Builder result(Map<String, Object> result) {
            output.result = result;
            return this;
        }

        public WorkflowOutput build() {
            return output;
        }
    }

    public String getExecutionId() {
        return executionId;
    }

    public void setExecutionId(String executionId) {
        this.executionId = executionId;
    }

    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public Task getTask() {
        return task;
    }

    public void setTask(Task task) {
        this.task = task;
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

    public Instant getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(Instant completedAt) {
        this.completedAt = completedAt;
    }

    public Map<String, Object> getResult() {
        return result;
    }

    public void setResult(Map<String, Object> result) {
        this.result = result;
    }
}
