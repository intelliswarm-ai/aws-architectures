package ai.intelliswarm.lambda.common.model;

import java.time.Instant;
import java.util.Map;

/**
 * Input model for Step Functions workflow states.
 */
public class WorkflowInput {

    private String executionId;
    private String taskId;
    private Task task;
    private Instant startedAt;
    private Map<String, Object> context;

    public WorkflowInput() {
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private final WorkflowInput input = new WorkflowInput();

        public Builder executionId(String executionId) {
            input.executionId = executionId;
            return this;
        }

        public Builder taskId(String taskId) {
            input.taskId = taskId;
            return this;
        }

        public Builder task(Task task) {
            input.task = task;
            return this;
        }

        public Builder startedAt(Instant startedAt) {
            input.startedAt = startedAt;
            return this;
        }

        public Builder context(Map<String, Object> context) {
            input.context = context;
            return this;
        }

        public WorkflowInput build() {
            return input;
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

    public Instant getStartedAt() {
        return startedAt;
    }

    public void setStartedAt(Instant startedAt) {
        this.startedAt = startedAt;
    }

    public Map<String, Object> getContext() {
        return context;
    }

    public void setContext(Map<String, Object> context) {
        this.context = context;
    }
}
