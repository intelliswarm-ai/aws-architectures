package ai.intelliswarm.lambda.common.config;

import software.amazon.awssdk.auth.credentials.EnvironmentVariableCredentialsProvider;
import software.amazon.awssdk.core.SdkSystemSetting;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sqs.SqsClient;

/**
 * AWS client configuration optimized for Lambda cold starts with SnapStart.
 *
 * Key optimizations:
 * - Uses EnvironmentVariableCredentialsProvider (fastest for Lambda)
 * - Uses UrlConnectionHttpClient (lighter than Apache or Netty)
 * - Clients are created as singletons to be reused across invocations
 */
public final class AwsClientConfig {

    private static final Region REGION = Region.of(
            System.getenv(SdkSystemSetting.AWS_REGION.environmentVariable()) != null
                    ? System.getenv(SdkSystemSetting.AWS_REGION.environmentVariable())
                    : "us-east-1"
    );

    private static final EnvironmentVariableCredentialsProvider CREDENTIALS_PROVIDER =
            EnvironmentVariableCredentialsProvider.create();

    // Singleton instances - initialized lazily
    private static volatile DynamoDbClient dynamoDbClient;
    private static volatile SqsClient sqsClient;
    private static volatile SnsClient snsClient;

    private AwsClientConfig() {
        // Utility class
    }

    /**
     * Creates or returns a singleton DynamoDB client.
     */
    public static DynamoDbClient dynamoDbClient() {
        if (dynamoDbClient == null) {
            synchronized (AwsClientConfig.class) {
                if (dynamoDbClient == null) {
                    dynamoDbClient = DynamoDbClient.builder()
                            .region(REGION)
                            .credentialsProvider(CREDENTIALS_PROVIDER)
                            .httpClientBuilder(UrlConnectionHttpClient.builder())
                            .build();
                }
            }
        }
        return dynamoDbClient;
    }

    /**
     * Creates or returns a singleton SQS client.
     */
    public static SqsClient sqsClient() {
        if (sqsClient == null) {
            synchronized (AwsClientConfig.class) {
                if (sqsClient == null) {
                    sqsClient = SqsClient.builder()
                            .region(REGION)
                            .credentialsProvider(CREDENTIALS_PROVIDER)
                            .httpClientBuilder(UrlConnectionHttpClient.builder())
                            .build();
                }
            }
        }
        return sqsClient;
    }

    /**
     * Creates or returns a singleton SNS client.
     */
    public static SnsClient snsClient() {
        if (snsClient == null) {
            synchronized (AwsClientConfig.class) {
                if (snsClient == null) {
                    snsClient = SnsClient.builder()
                            .region(REGION)
                            .credentialsProvider(CREDENTIALS_PROVIDER)
                            .httpClientBuilder(UrlConnectionHttpClient.builder())
                            .build();
                }
            }
        }
        return snsClient;
    }

    /**
     * Returns the configured AWS region.
     */
    public static Region getRegion() {
        return REGION;
    }
}
