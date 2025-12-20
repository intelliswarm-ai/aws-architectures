package ai.intelliswarm.lambda.notification.model;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * Model for notification messages.
 */
public class NotificationMessage {

    private String taskId;
    private String taskType;
    private String status;
    private String subject;
    private String body;
    private boolean failure;
    private Instant timestamp;
    private Map<String, Object> result;
    private List<String> recipients;
    private String channel;

    public NotificationMessage() {
    }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private final NotificationMessage message = new NotificationMessage();

        public Builder taskId(String taskId) {
            message.taskId = taskId;
            return this;
        }

        public Builder taskType(String taskType) {
            message.taskType = taskType;
            return this;
        }

        public Builder status(String status) {
            message.status = status;
            return this;
        }

        public Builder subject(String subject) {
            message.subject = subject;
            return this;
        }

        public Builder body(String body) {
            message.body = body;
            return this;
        }

        public Builder failure(boolean failure) {
            message.failure = failure;
            return this;
        }

        public Builder timestamp(Instant timestamp) {
            message.timestamp = timestamp;
            return this;
        }

        public Builder result(Map<String, Object> result) {
            message.result = result;
            return this;
        }

        public Builder recipients(List<String> recipients) {
            message.recipients = recipients;
            return this;
        }

        public Builder channel(String channel) {
            message.channel = channel;
            return this;
        }

        public NotificationMessage build() {
            return message;
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

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getSubject() {
        return subject;
    }

    public void setSubject(String subject) {
        this.subject = subject;
    }

    public String getBody() {
        return body;
    }

    public void setBody(String body) {
        this.body = body;
    }

    public boolean isFailure() {
        return failure;
    }

    public void setFailure(boolean failure) {
        this.failure = failure;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    public Map<String, Object> getResult() {
        return result;
    }

    public void setResult(Map<String, Object> result) {
        this.result = result;
    }

    public List<String> getRecipients() {
        return recipients;
    }

    public void setRecipients(List<String> recipients) {
        this.recipients = recipients;
    }

    public String getChannel() {
        return channel;
    }

    public void setChannel(String channel) {
        this.channel = channel;
    }
}
