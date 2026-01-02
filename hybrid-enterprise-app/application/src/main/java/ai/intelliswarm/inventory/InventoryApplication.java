package ai.intelliswarm.inventory;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.scheduling.annotation.EnableAsync;

/**
 * Main application class for the Inventory Management System.
 *
 * This application demonstrates a traditional enterprise Java stack
 * migrated to AWS Elastic Beanstalk with hybrid architecture:
 * - Spring Boot 3.2 with embedded Tomcat
 * - Hibernate 6.x for JPA/ORM with Oracle dialect
 * - JasperReports for PDF/Excel reporting
 * - Oracle database hosted on-premises (connected via VPN/Direct Connect)
 */
@SpringBootApplication
@EnableJpaAuditing
@EnableCaching
@EnableAsync
public class InventoryApplication {

    public static void main(String[] args) {
        SpringApplication.run(InventoryApplication.class, args);
    }
}
