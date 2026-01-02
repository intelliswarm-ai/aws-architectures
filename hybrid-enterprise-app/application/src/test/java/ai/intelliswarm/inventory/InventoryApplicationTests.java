package ai.intelliswarm.inventory;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("local")
@Tag("unit")
class InventoryApplicationTests {

    @Test
    void contextLoads() {
        // Verify Spring context loads successfully
    }
}
