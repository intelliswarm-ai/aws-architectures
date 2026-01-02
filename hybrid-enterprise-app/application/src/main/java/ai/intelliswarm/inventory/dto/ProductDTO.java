package ai.intelliswarm.inventory.dto;

import ai.intelliswarm.inventory.model.ProductStatus;
import jakarta.validation.constraints.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProductDTO {

    private UUID id;

    @NotBlank(message = "SKU is required")
    @Size(max = 50)
    private String sku;

    @NotBlank(message = "Product name is required")
    @Size(max = 200)
    private String name;

    @Size(max = 2000)
    private String description;

    @NotNull(message = "Unit price is required")
    @DecimalMin(value = "0.00")
    private BigDecimal unitPrice;

    @DecimalMin(value = "0.00")
    private BigDecimal costPrice;

    @NotNull
    @Min(value = 0)
    private Integer quantityInStock;

    @Min(value = 0)
    private Integer reorderLevel;

    @Min(value = 0)
    private Integer reorderQuantity;

    private String unit;
    private String barcode;
    private BigDecimal weightKg;
    private String imageUrl;

    private UUID categoryId;
    private String categoryName;

    private UUID supplierId;
    private String supplierName;

    private ProductStatus status;
    private boolean active;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    private BigDecimal inventoryValue;
    private boolean needsReorder;
}
