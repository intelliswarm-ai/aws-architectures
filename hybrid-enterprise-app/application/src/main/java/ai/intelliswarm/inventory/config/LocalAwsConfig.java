package ai.intelliswarm.inventory.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import software.amazon.awssdk.services.s3.S3Client;

import static org.mockito.Mockito.mock;

/**
 * Local AWS configuration with mocked clients.
 * Used for local development without AWS credentials.
 */
@Configuration
@Profile("local")
public class LocalAwsConfig {

    @Bean
    public S3Client s3Client() {
        // Return a mock S3 client for local development
        return mock(S3Client.class);
    }
}
