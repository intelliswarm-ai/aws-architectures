package ai.intelliswarm.lambda.generator.handler;

import ai.intelliswarm.lambda.common.config.AwsClientConfig;
import ai.intelliswarm.lambda.generator.repository.TaskQueueRepository;
import ai.intelliswarm.lambda.generator.service.TaskGeneratorService;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.ScheduledEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Lambda handler triggered by EventBridge on a schedule.
 * Generates tasks and publishes them to SQS for processing.
 */
public class TaskGeneratorHandler implements RequestHandler<ScheduledEvent, Void> {

    private static final Logger logger = LoggerFactory.getLogger(TaskGeneratorHandler.class);

    private final TaskGeneratorService taskGeneratorService;

    /**
     * Default constructor used by Lambda runtime.
     * Initializes AWS clients and services.
     */
    public TaskGeneratorHandler() {
        TaskQueueRepository queueRepository = new TaskQueueRepository(
                AwsClientConfig.sqsClient(),
                System.getenv("TASK_QUEUE_URL")
        );
        this.taskGeneratorService = new TaskGeneratorService(queueRepository);
    }

    /**
     * Constructor for testing with dependency injection.
     */
    public TaskGeneratorHandler(TaskGeneratorService taskGeneratorService) {
        this.taskGeneratorService = taskGeneratorService;
    }

    @Override
    public Void handleRequest(ScheduledEvent event, Context context) {
        logger.info("Task generation triggered. Event time: {}, Request ID: {}",
                event.getTime(), context.getAwsRequestId());

        try {
            int tasksGenerated = taskGeneratorService.generateAndQueueTasks();
            logger.info("Successfully generated and queued {} tasks", tasksGenerated);
        } catch (Exception e) {
            logger.error("Failed to generate tasks", e);
            throw e;
        }

        return null;
    }
}
