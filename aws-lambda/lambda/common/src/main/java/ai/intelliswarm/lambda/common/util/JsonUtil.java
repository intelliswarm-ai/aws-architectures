package ai.intelliswarm.lambda.common.util;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

/**
 * JSON serialization/deserialization utility using Jackson.
 */
public final class JsonUtil {

    private static final ObjectMapper OBJECT_MAPPER = createObjectMapper();

    private JsonUtil() {
        // Utility class
    }

    private static ObjectMapper createObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();

        // Register Java 8 time module for Instant, etc.
        mapper.registerModule(new JavaTimeModule());

        // Configuration
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        mapper.configure(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS, false);
        mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

        return mapper;
    }

    /**
     * Returns the configured ObjectMapper instance.
     */
    public static ObjectMapper getObjectMapper() {
        return OBJECT_MAPPER;
    }

    /**
     * Serialize an object to JSON string.
     */
    public static String toJson(Object object) {
        try {
            return OBJECT_MAPPER.writeValueAsString(object);
        } catch (JsonProcessingException e) {
            throw new JsonSerializationException("Failed to serialize object to JSON", e);
        }
    }

    /**
     * Serialize an object to pretty-printed JSON string.
     */
    public static String toPrettyJson(Object object) {
        try {
            return OBJECT_MAPPER.writerWithDefaultPrettyPrinter().writeValueAsString(object);
        } catch (JsonProcessingException e) {
            throw new JsonSerializationException("Failed to serialize object to JSON", e);
        }
    }

    /**
     * Deserialize a JSON string to an object.
     */
    public static <T> T fromJson(String json, Class<T> clazz) {
        try {
            return OBJECT_MAPPER.readValue(json, clazz);
        } catch (JsonProcessingException e) {
            throw new JsonSerializationException("Failed to deserialize JSON to " + clazz.getSimpleName(), e);
        }
    }

    /**
     * Convert an object to another type (useful for Map to POJO conversion).
     */
    public static <T> T convert(Object source, Class<T> targetClass) {
        return OBJECT_MAPPER.convertValue(source, targetClass);
    }

    /**
     * Exception for JSON serialization/deserialization errors.
     */
    public static class JsonSerializationException extends RuntimeException {
        public JsonSerializationException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
