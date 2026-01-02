package ai.intelliswarm.inventory.repository;

import ai.intelliswarm.inventory.model.Category;
import ai.intelliswarm.inventory.model.Product;
import ai.intelliswarm.inventory.model.ProductStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("local")
@Tag("integration")
class ProductRepositoryTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private ProductRepository productRepository;

    @Autowired
    private CategoryRepository categoryRepository;

    private Category category;
    private Product product;

    @BeforeEach
    void setUp() {
        category = new Category();
        category.setName("Electronics");
        category.setDescription("Electronic devices");
        entityManager.persist(category);

        product = new Product();
        product.setSku("ELEC-001");
        product.setName("Test Product");
        product.setDescription("Test Description");
        product.setUnitPrice(new BigDecimal("99.99"));
        product.setQuantityInStock(5);  // Below reorder level
        product.setReorderLevel(10);
        product.setReorderQuantity(50);
        product.setStatus(ProductStatus.ACTIVE);
        product.setCategory(category);
        entityManager.persist(product);

        Product product2 = new Product();
        product2.setSku("ELEC-002");
        product2.setName("Another Product");
        product2.setUnitPrice(new BigDecimal("149.99"));
        product2.setQuantityInStock(100);  // Above reorder level
        product2.setReorderLevel(10);
        product2.setReorderQuantity(50);
        product2.setStatus(ProductStatus.ACTIVE);
        product2.setCategory(category);
        entityManager.persist(product2);

        entityManager.flush();
    }

    @Test
    void findBySku_shouldReturnProduct() {
        Optional<Product> found = productRepository.findBySku("ELEC-001");

        assertThat(found).isPresent();
        assertThat(found.get().getName()).isEqualTo("Test Product");
    }

    @Test
    void findBySku_whenNotExists_shouldReturnEmpty() {
        Optional<Product> found = productRepository.findBySku("NON-EXISTENT");

        assertThat(found).isEmpty();
    }

    @Test
    void existsBySku_shouldReturnTrue() {
        boolean exists = productRepository.existsBySku("ELEC-001");

        assertThat(exists).isTrue();
    }

    @Test
    void findProductsNeedingReorder_shouldReturnLowStockProducts() {
        List<Product> products = productRepository.findProductsNeedingReorder();

        assertThat(products).hasSize(1);
        assertThat(products.get(0).getSku()).isEqualTo("ELEC-001");
    }

    @Test
    void countProductsNeedingReorder_shouldReturnCount() {
        Long count = productRepository.countProductsNeedingReorder();

        assertThat(count).isEqualTo(1);
    }

    @Test
    void calculateTotalInventoryValue_shouldReturnSum() {
        BigDecimal totalValue = productRepository.calculateTotalInventoryValue();

        // Product 1: 99.99 * 5 = 499.95
        // Product 2: 149.99 * 100 = 14999.00
        // Total: 15498.95
        assertThat(totalValue).isEqualByComparingTo("15498.95");
    }

    @Test
    void findByStatus_shouldReturnActiveProducts() {
        List<Product> activeProducts = productRepository.findByStatus(ProductStatus.ACTIVE);

        assertThat(activeProducts).hasSize(2);
    }

    @Test
    void findByCategoryId_shouldReturnProductsInCategory() {
        List<Product> products = productRepository.findByCategoryId(category.getId());

        assertThat(products).hasSize(2);
    }
}
