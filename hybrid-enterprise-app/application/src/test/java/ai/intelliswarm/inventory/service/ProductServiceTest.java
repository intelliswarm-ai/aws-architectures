package ai.intelliswarm.inventory.service;

import ai.intelliswarm.inventory.dto.ProductDTO;
import ai.intelliswarm.inventory.exception.ResourceNotFoundException;
import ai.intelliswarm.inventory.model.Category;
import ai.intelliswarm.inventory.model.Product;
import ai.intelliswarm.inventory.model.ProductStatus;
import ai.intelliswarm.inventory.repository.CategoryRepository;
import ai.intelliswarm.inventory.repository.ProductRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@Tag("unit")
class ProductServiceTest {

    @Mock
    private ProductRepository productRepository;

    @Mock
    private CategoryRepository categoryRepository;

    @InjectMocks
    private ProductService productService;

    private Product product;
    private Category category;
    private UUID productId;
    private UUID categoryId;

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();
        categoryId = UUID.randomUUID();

        category = new Category();
        category.setId(categoryId);
        category.setName("Electronics");

        product = new Product();
        product.setId(productId);
        product.setSku("ELEC-001");
        product.setName("Test Product");
        product.setDescription("Test Description");
        product.setUnitPrice(new BigDecimal("99.99"));
        product.setQuantityInStock(100);
        product.setReorderLevel(10);
        product.setReorderQuantity(50);
        product.setStatus(ProductStatus.ACTIVE);
        product.setCategory(category);
    }

    @Test
    void findAll_shouldReturnPagedProducts() {
        Pageable pageable = PageRequest.of(0, 10);
        Page<Product> productPage = new PageImpl<>(List.of(product));

        when(productRepository.findAll(pageable)).thenReturn(productPage);

        Page<ProductDTO> result = productService.findAll(pageable);

        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getContent().get(0).getSku()).isEqualTo("ELEC-001");
        verify(productRepository).findAll(pageable);
    }

    @Test
    void findById_whenProductExists_shouldReturnProduct() {
        when(productRepository.findById(productId)).thenReturn(Optional.of(product));

        ProductDTO result = productService.findById(productId);

        assertThat(result.getSku()).isEqualTo("ELEC-001");
        assertThat(result.getName()).isEqualTo("Test Product");
    }

    @Test
    void findById_whenProductNotExists_shouldThrowException() {
        when(productRepository.findById(productId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> productService.findById(productId))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("Product");
    }

    @Test
    void findBySku_whenProductExists_shouldReturnProduct() {
        when(productRepository.findBySku("ELEC-001")).thenReturn(Optional.of(product));

        ProductDTO result = productService.findBySku("ELEC-001");

        assertThat(result.getName()).isEqualTo("Test Product");
    }

    @Test
    void create_shouldCreateProduct() {
        ProductDTO dto = new ProductDTO();
        dto.setSku("NEW-001");
        dto.setName("New Product");
        dto.setUnitPrice(new BigDecimal("149.99"));
        dto.setQuantityInStock(50);
        dto.setReorderLevel(5);
        dto.setReorderQuantity(25);
        dto.setCategoryId(categoryId);

        when(productRepository.existsBySku("NEW-001")).thenReturn(false);
        when(categoryRepository.findById(categoryId)).thenReturn(Optional.of(category));
        when(productRepository.save(any(Product.class))).thenReturn(product);

        ProductDTO result = productService.create(dto);

        assertThat(result).isNotNull();
        verify(productRepository).save(any(Product.class));
    }

    @Test
    void updateStock_shouldUpdateQuantity() {
        when(productRepository.findById(productId)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenReturn(product);

        ProductDTO result = productService.updateStock(productId, 10);

        assertThat(result).isNotNull();
        verify(productRepository).save(any(Product.class));
    }

    @Test
    void findProductsNeedingReorder_shouldReturnLowStockProducts() {
        when(productRepository.findProductsNeedingReorder()).thenReturn(List.of(product));

        List<ProductDTO> result = productService.findProductsNeedingReorder();

        assertThat(result).hasSize(1);
    }

    @Test
    void calculateTotalInventoryValue_shouldReturnSum() {
        when(productRepository.calculateTotalInventoryValue()).thenReturn(new BigDecimal("9999.00"));

        BigDecimal result = productService.calculateTotalInventoryValue();

        assertThat(result).isEqualByComparingTo("9999.00");
    }

    @Test
    void delete_shouldDeleteProduct() {
        when(productRepository.findById(productId)).thenReturn(Optional.of(product));

        productService.delete(productId);

        verify(productRepository).delete(product);
    }
}
