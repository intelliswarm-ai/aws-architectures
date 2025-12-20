package ai.intelliswarm.lambda.notification.service;

import ai.intelliswarm.lambda.notification.model.NotificationMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Service for sending notifications via multiple channels.
 */
public class NotificationService {

    private static final Logger logger = LoggerFactory.getLogger(NotificationService.class);

    private final String defaultRecipient;
    private final boolean emailEnabled;

    public NotificationService() {
        this.defaultRecipient = System.getenv("NOTIFICATION_EMAIL");
        this.emailEnabled = System.getenv("EMAIL_ENABLED") != null
                && System.getenv("EMAIL_ENABLED").equalsIgnoreCase("true");
    }

    /**
     * Send a notification via configured channels.
     */
    public void send(NotificationMessage message) {
        logger.info("Sending notification for task: {} (failure: {})",
                message.getTaskId(), message.isFailure());

        // Log notification details
        logNotification(message);

        // Send via email if enabled
        if (emailEnabled) {
            sendEmail(message);
        }

        // Send via webhook if configured
        String webhookUrl = System.getenv("NOTIFICATION_WEBHOOK_URL");
        if (webhookUrl != null && !webhookUrl.isEmpty()) {
            sendWebhook(message, webhookUrl);
        }
    }

    /**
     * Log the notification (useful for debugging and audit).
     */
    private void logNotification(NotificationMessage message) {
        String logLevel = message.isFailure() ? "ERROR" : "INFO";

        logger.info("NOTIFICATION [{}]: Task={}, Type={}, Status={}, Subject={}",
                logLevel,
                message.getTaskId(),
                message.getTaskType(),
                message.getStatus(),
                message.getSubject());

        if (message.getBody() != null) {
            logger.debug("Notification body: {}", message.getBody());
        }
    }

    /**
     * Send notification via email (placeholder implementation).
     */
    private void sendEmail(NotificationMessage message) {
        String recipient = defaultRecipient;
        if (message.getRecipients() != null && !message.getRecipients().isEmpty()) {
            recipient = message.getRecipients().get(0);
        }

        if (recipient == null || recipient.isEmpty()) {
            logger.warn("No email recipient configured, skipping email notification");
            return;
        }

        // In a real implementation, this would use SES
        logger.info("EMAIL: Sending to {} - Subject: {}",
                recipient, message.getSubject());

        // Placeholder for SES integration
        // SesClient sesClient = AwsClientConfig.sesClient();
        // sesClient.sendEmail(...)
    }

    /**
     * Send notification via webhook (placeholder implementation).
     */
    private void sendWebhook(NotificationMessage message, String webhookUrl) {
        logger.info("WEBHOOK: Posting to {} for task {}",
                webhookUrl, message.getTaskId());

        // In a real implementation, this would make an HTTP POST request
        // HttpClient client = HttpClient.newHttpClient();
        // client.send(...)
    }
}
