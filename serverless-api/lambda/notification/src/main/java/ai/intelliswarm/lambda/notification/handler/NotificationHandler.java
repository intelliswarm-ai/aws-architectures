package ai.intelliswarm.lambda.notification.handler;

import ai.intelliswarm.lambda.common.util.JsonUtil;
import ai.intelliswarm.lambda.notification.model.NotificationMessage;
import ai.intelliswarm.lambda.notification.service.NotificationService;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SNSEvent;
import com.amazonaws.services.lambda.runtime.events.SNSEvent.SNSRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Lambda handler for processing SNS notifications about task completion/failure.
 */
public class NotificationHandler implements RequestHandler<SNSEvent, Void> {

    private static final Logger logger = LoggerFactory.getLogger(NotificationHandler.class);

    private final NotificationService notificationService;

    public NotificationHandler() {
        this.notificationService = new NotificationService();
    }

    public NotificationHandler(NotificationService notificationService) {
        this.notificationService = notificationService;
    }

    @Override
    public Void handleRequest(SNSEvent event, Context context) {
        logger.info("Processing {} SNS records. Request ID: {}",
                event.getRecords().size(), context.getAwsRequestId());

        for (SNSRecord record : event.getRecords()) {
            try {
                processRecord(record);
            } catch (Exception e) {
                logger.error("Failed to process SNS record: {}", record.getSNS().getMessageId(), e);
                // Continue processing other records
            }
        }

        return null;
    }

    private void processRecord(SNSRecord record) {
        String subject = record.getSNS().getSubject();
        String messageBody = record.getSNS().getMessage();
        String topicArn = record.getSNS().getTopicArn();

        logger.info("Processing notification - Topic: {}, Subject: {}",
                topicArn, subject);

        // Determine notification type from topic ARN
        boolean isFailure = topicArn.contains("failure") ||
                           (subject != null && subject.toLowerCase().contains("fail"));

        // Parse the message
        NotificationMessage message = parseMessage(messageBody, subject, isFailure);

        // Send notification via configured channels
        notificationService.send(message);

        logger.info("Notification sent successfully for task: {}", message.getTaskId());
    }

    private NotificationMessage parseMessage(String messageBody, String subject, boolean isFailure) {
        try {
            // Try to parse as structured JSON
            NotificationMessage message = JsonUtil.fromJson(messageBody, NotificationMessage.class);
            message.setFailure(isFailure);
            if (message.getSubject() == null) {
                message.setSubject(subject);
            }
            return message;
        } catch (Exception e) {
            // Fallback for plain text messages
            logger.debug("Could not parse message as JSON, using plain text: {}", e.getMessage());
            return NotificationMessage.builder()
                    .subject(subject)
                    .body(messageBody)
                    .failure(isFailure)
                    .build();
        }
    }
}
