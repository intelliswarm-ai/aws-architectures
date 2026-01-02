package ai.intelliswarm.inventory.repository;

import ai.intelliswarm.inventory.model.Product;
import ai.intelliswarm.inventory.model.ProductStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for Product entity operations.
 * Uses Hibernate with Oracle dialect for on-premises database.
 */
@Repository
public interface ProductRepository extends JpaRepository<Product, UUID>, JpaSpecificationExecutor<Product> {

    Optional<Product> findBySku(String sku);

    Optional<Product> findByBarcode(String barcode);

    List<Product> findByCategory_Id(UUID categoryId);

    List<Product> findBySupplier_Id(UUID supplierId);

    List<Product> findByStatus(ProductStatus status);

    Page<Product> findByNameContainingIgnoreCase(String name, Pageable pageable);

    @Query("SELECT p FROM Product p WHERE p.quantityInStock <= p.reorderLevel AND p.active = true")
    List<Product> findProductsNeedingReorder();

    @Query("""
        SELECT p FROM Product p
        WHERE (:name IS NULL OR LOWER(p.name) LIKE LOWER(CONCAT('%', :name, '%')))
        AND (:categoryId IS NULL OR p.category.id = :categoryId)
        AND (:status IS NULL OR p.status = :status)
        AND p.active = true
        """)
    Page<Product> searchProducts(
        @Param("name") String name,
        @Param("categoryId") UUID categoryId,
        @Param("status") ProductStatus status,
        Pageable pageable
    );

    @Query("SELECT SUM(p.unitPrice * p.quantityInStock) FROM Product p WHERE p.active = true")
    BigDecimal calculateTotalInventoryValue();

    @Query("SELECT COUNT(p) FROM Product p WHERE p.quantityInStock <= p.reorderLevel AND p.active = true")
    Long countProductsNeedingReorder();

    // Oracle-specific native query using FETCH FIRST
    @Query(value = """
        SELECT * FROM PRODUCTS p
        WHERE p.is_active = 1
        AND p.quantity_in_stock > 0
        ORDER BY p.quantity_in_stock DESC
        FETCH FIRST :limit ROWS ONLY
        """, nativeQuery = true)
    List<Product> findTopByStock(@Param("limit") int limit);

    boolean existsBySku(String sku);

    boolean existsByBarcode(String barcode);
}
