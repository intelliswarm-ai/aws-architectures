package ai.intelliswarm.lambda.common.model;

/**
 * Task priority levels for queue ordering.
 */
public enum TaskPriority {
    LOW(0),
    NORMAL(1),
    HIGH(2),
    CRITICAL(3);

    private final int value;

    TaskPriority(int value) {
        this.value = value;
    }

    public int getValue() {
        return value;
    }
}
