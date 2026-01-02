package ai.intelliswarm.inventory.controller;

import ai.intelliswarm.inventory.dto.ProductDTO;
import ai.intelliswarm.inventory.model.ProductStatus;
import ai.intelliswarm.inventory.service.ProductService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ProductController.class)
@Tag("unit")
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ProductService productService;

    private ProductDTO productDTO;
    private UUID productId;

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();

        productDTO = new ProductDTO();
        productDTO.setId(productId);
        productDTO.setSku("ELEC-001");
        productDTO.setName("Test Product");
        productDTO.setDescription("Test Description");
        productDTO.setUnitPrice(new BigDecimal("99.99"));
        productDTO.setQuantityInStock(100);
        productDTO.setReorderLevel(10);
        productDTO.setStatus(ProductStatus.ACTIVE);
    }

    @Test
    @WithMockUser
    void getAllProducts_shouldReturnPagedProducts() throws Exception {
        when(productService.findAll(any(Pageable.class)))
            .thenReturn(new PageImpl<>(List.of(productDTO)));

        mockMvc.perform(get("/api/v1/products"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content[0].sku").value("ELEC-001"));
    }

    @Test
    @WithMockUser
    void getProductById_shouldReturnProduct() throws Exception {
        when(productService.findById(productId)).thenReturn(productDTO);

        mockMvc.perform(get("/api/v1/products/{id}", productId))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Test Product"));
    }

    @Test
    @WithMockUser
    void getProductBySku_shouldReturnProduct() throws Exception {
        when(productService.findBySku("ELEC-001")).thenReturn(productDTO);

        mockMvc.perform(get("/api/v1/products/sku/{sku}", "ELEC-001"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.sku").value("ELEC-001"));
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void createProduct_withAdminRole_shouldCreateProduct() throws Exception {
        when(productService.create(any(ProductDTO.class))).thenReturn(productDTO);

        mockMvc.perform(post("/api/v1/products")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(productDTO)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.sku").value("ELEC-001"));
    }

    @Test
    @WithMockUser(roles = "USER")
    void createProduct_withUserRole_shouldBeForbidden() throws Exception {
        mockMvc.perform(post("/api/v1/products")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(productDTO)))
            .andExpect(status().isForbidden());
    }

    @Test
    @WithMockUser(roles = "ADMIN")
    void deleteProduct_withAdminRole_shouldDelete() throws Exception {
        mockMvc.perform(delete("/api/v1/products/{id}", productId)
                .with(csrf()))
            .andExpect(status().isNoContent());
    }

    @Test
    @WithMockUser
    void getInventoryValue_shouldReturnTotal() throws Exception {
        when(productService.calculateTotalInventoryValue())
            .thenReturn(new BigDecimal("9999.00"));

        mockMvc.perform(get("/api/v1/products/inventory-value"))
            .andExpect(status().isOk())
            .andExpect(content().string("9999.00"));
    }

    @Test
    @WithMockUser
    void getProductsNeedingReorder_shouldReturnList() throws Exception {
        when(productService.findProductsNeedingReorder())
            .thenReturn(List.of(productDTO));

        mockMvc.perform(get("/api/v1/products/reorder"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].sku").value("ELEC-001"));
    }
}
