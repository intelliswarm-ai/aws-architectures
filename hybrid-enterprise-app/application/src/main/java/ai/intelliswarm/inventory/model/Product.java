package ai.intelliswarm.inventory.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.*;
import lombok.*;

import java.math.BigDecimal;

/**
 * Entity representing a product in the inventory system.
 * Configured for Oracle database with appropriate column types.
 */
@Entity
@Table(name = "PRODUCTS", indexes = {
    @Index(name = "IDX_PRODUCT_SKU", columnList = "sku", unique = true),
    @Index(name = "IDX_PRODUCT_NAME", columnList = "name"),
    @Index(name = "IDX_PRODUCT_CATEGORY", columnList = "category_id"),
    @Index(name = "IDX_PRODUCT_SUPPLIER", columnList = "supplier_id")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Product extends BaseEntity {

    @NotBlank(message = "SKU is required")
    @Size(max = 50)
    @Column(name = "sku", nullable = false, unique = true, length = 50)
    private String sku;

    @NotBlank(message = "Product name is required")
    @Size(max = 200)
    @Column(name = "name", nullable = false, length = 200)
    private String name;

    @Size(max = 2000)
    @Column(name = "description", length = 2000)
    private String description;

    @NotNull(message = "Unit price is required")
    @DecimalMin(value = "0.00")
    @Column(name = "unit_price", nullable = false, precision = 12, scale = 2)
    private BigDecimal unitPrice;

    @DecimalMin(value = "0.00")
    @Column(name = "cost_price", precision = 12, scale = 2)
    private BigDecimal costPrice;

    @NotNull
    @Min(value = 0)
    @Column(name = "quantity_in_stock", nullable = false)
    @Builder.Default
    private Integer quantityInStock = 0;

    @Min(value = 0)
    @Column(name = "reorder_level")
    @Builder.Default
    private Integer reorderLevel = 10;

    @Min(value = 0)
    @Column(name = "reorder_quantity")
    @Builder.Default
    private Integer reorderQuantity = 50;

    @Size(max = 50)
    @Column(name = "unit", length = 50)
    @Builder.Default
    private String unit = "piece";

    @Size(max = 100)
    @Column(name = "barcode", length = 100)
    private String barcode;

    @Column(name = "weight_kg", precision = 10, scale = 3)
    private BigDecimal weightKg;

    @Size(max = 255)
    @Column(name = "image_url", length = 255)
    private String imageUrl;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "supplier_id")
    private Supplier supplier;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 20)
    @Builder.Default
    private ProductStatus status = ProductStatus.ACTIVE;

    public boolean needsReorder() {
        return quantityInStock != null && reorderLevel != null
               && quantityInStock <= reorderLevel;
    }

    public BigDecimal getInventoryValue() {
        if (unitPrice == null || quantityInStock == null) {
            return BigDecimal.ZERO;
        }
        return unitPrice.multiply(BigDecimal.valueOf(quantityInStock));
    }
}
