package ai.intelliswarm.lambda.common.util;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Base64;

/**
 * Utility for generating idempotency keys for Lambda invocations.
 */
public final class IdempotencyKeyGenerator {

    private IdempotencyKeyGenerator() {
        // Utility class
    }

    /**
     * Generate an idempotency key from a task ID.
     */
    public static String fromTaskId(String taskId) {
        return "task-" + taskId;
    }

    /**
     * Generate an idempotency key from a message ID and task ID.
     */
    public static String fromMessageAndTask(String messageId, String taskId) {
        return "msg-" + messageId + "-task-" + taskId;
    }

    /**
     * Generate a hash-based idempotency key from arbitrary input.
     */
    public static String fromInput(String... inputs) {
        String combined = String.join("|", inputs);
        return hash(combined);
    }

    /**
     * Generate a SHA-256 hash of the input, encoded as Base64.
     */
    private static String hash(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hashBytes = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            return Base64.getUrlEncoder().withoutPadding().encodeToString(hashBytes);
        } catch (NoSuchAlgorithmException e) {
            // SHA-256 is always available in standard JDK
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }
}
