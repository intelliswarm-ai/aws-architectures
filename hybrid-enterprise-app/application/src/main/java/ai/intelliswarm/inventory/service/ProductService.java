package ai.intelliswarm.inventory.service;

import ai.intelliswarm.inventory.dto.ProductDTO;
import ai.intelliswarm.inventory.exception.DuplicateResourceException;
import ai.intelliswarm.inventory.exception.ResourceNotFoundException;
import ai.intelliswarm.inventory.model.Category;
import ai.intelliswarm.inventory.model.Product;
import ai.intelliswarm.inventory.model.ProductStatus;
import ai.intelliswarm.inventory.model.Supplier;
import ai.intelliswarm.inventory.repository.CategoryRepository;
import ai.intelliswarm.inventory.repository.ProductRepository;
import ai.intelliswarm.inventory.repository.SupplierRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class ProductService {

    private final ProductRepository productRepository;
    private final CategoryRepository categoryRepository;
    private final SupplierRepository supplierRepository;

    public Page<ProductDTO> findAll(Pageable pageable) {
        return productRepository.findAll(pageable).map(this::toDTO);
    }

    @Cacheable(value = "products", key = "#id")
    public ProductDTO findById(UUID id) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", "id", id));
        return toDTO(product);
    }

    public ProductDTO findBySku(String sku) {
        Product product = productRepository.findBySku(sku)
            .orElseThrow(() -> new ResourceNotFoundException("Product", "sku", sku));
        return toDTO(product);
    }

    public Page<ProductDTO> search(String name, UUID categoryId, ProductStatus status, Pageable pageable) {
        return productRepository.searchProducts(name, categoryId, status, pageable).map(this::toDTO);
    }

    public List<ProductDTO> findProductsNeedingReorder() {
        return productRepository.findProductsNeedingReorder().stream().map(this::toDTO).toList();
    }

    @Transactional
    @CacheEvict(value = "products", allEntries = true)
    public ProductDTO create(ProductDTO dto) {
        log.info("Creating product with SKU: {}", dto.getSku());

        if (productRepository.existsBySku(dto.getSku())) {
            throw new DuplicateResourceException("Product", "sku", dto.getSku());
        }

        Product product = toEntity(dto);
        product = productRepository.save(product);

        log.info("Created product: {} with ID: {}", product.getSku(), product.getId());
        return toDTO(product);
    }

    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public ProductDTO update(UUID id, ProductDTO dto) {
        log.info("Updating product with ID: {}", id);

        Product existing = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", "id", id));

        if (!existing.getSku().equals(dto.getSku()) && productRepository.existsBySku(dto.getSku())) {
            throw new DuplicateResourceException("Product", "sku", dto.getSku());
        }

        updateEntityFromDTO(existing, dto);
        existing = productRepository.save(existing);

        return toDTO(existing);
    }

    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public void delete(UUID id) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", "id", id));

        product.setActive(false);
        product.setStatus(ProductStatus.DISCONTINUED);
        productRepository.save(product);
    }

    @Transactional
    @CacheEvict(value = "products", key = "#id")
    public ProductDTO updateStock(UUID id, int quantityChange) {
        Product product = productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product", "id", id));

        int newQuantity = product.getQuantityInStock() + quantityChange;
        if (newQuantity < 0) {
            throw new IllegalArgumentException("Insufficient stock");
        }

        product.setQuantityInStock(newQuantity);
        if (newQuantity == 0) {
            product.setStatus(ProductStatus.OUT_OF_STOCK);
        } else if (product.getStatus() == ProductStatus.OUT_OF_STOCK) {
            product.setStatus(ProductStatus.ACTIVE);
        }

        return toDTO(productRepository.save(product));
    }

    public BigDecimal calculateTotalInventoryValue() {
        BigDecimal total = productRepository.calculateTotalInventoryValue();
        return total != null ? total : BigDecimal.ZERO;
    }

    private ProductDTO toDTO(Product product) {
        return ProductDTO.builder()
            .id(product.getId())
            .sku(product.getSku())
            .name(product.getName())
            .description(product.getDescription())
            .unitPrice(product.getUnitPrice())
            .costPrice(product.getCostPrice())
            .quantityInStock(product.getQuantityInStock())
            .reorderLevel(product.getReorderLevel())
            .reorderQuantity(product.getReorderQuantity())
            .unit(product.getUnit())
            .barcode(product.getBarcode())
            .weightKg(product.getWeightKg())
            .imageUrl(product.getImageUrl())
            .categoryId(product.getCategory() != null ? product.getCategory().getId() : null)
            .categoryName(product.getCategory() != null ? product.getCategory().getName() : null)
            .supplierId(product.getSupplier() != null ? product.getSupplier().getId() : null)
            .supplierName(product.getSupplier() != null ? product.getSupplier().getName() : null)
            .status(product.getStatus())
            .active(product.isActive())
            .createdAt(product.getCreatedAt())
            .updatedAt(product.getUpdatedAt())
            .inventoryValue(product.getInventoryValue())
            .needsReorder(product.needsReorder())
            .build();
    }

    private Product toEntity(ProductDTO dto) {
        Product product = Product.builder()
            .sku(dto.getSku())
            .name(dto.getName())
            .description(dto.getDescription())
            .unitPrice(dto.getUnitPrice())
            .costPrice(dto.getCostPrice())
            .quantityInStock(dto.getQuantityInStock() != null ? dto.getQuantityInStock() : 0)
            .reorderLevel(dto.getReorderLevel() != null ? dto.getReorderLevel() : 10)
            .reorderQuantity(dto.getReorderQuantity() != null ? dto.getReorderQuantity() : 50)
            .unit(dto.getUnit() != null ? dto.getUnit() : "piece")
            .barcode(dto.getBarcode())
            .weightKg(dto.getWeightKg())
            .imageUrl(dto.getImageUrl())
            .status(dto.getStatus() != null ? dto.getStatus() : ProductStatus.ACTIVE)
            .build();

        setRelationships(product, dto);
        return product;
    }

    private void updateEntityFromDTO(Product product, ProductDTO dto) {
        product.setSku(dto.getSku());
        product.setName(dto.getName());
        product.setDescription(dto.getDescription());
        product.setUnitPrice(dto.getUnitPrice());
        product.setCostPrice(dto.getCostPrice());
        product.setQuantityInStock(dto.getQuantityInStock());
        product.setReorderLevel(dto.getReorderLevel());
        product.setReorderQuantity(dto.getReorderQuantity());
        product.setUnit(dto.getUnit());
        product.setBarcode(dto.getBarcode());
        product.setWeightKg(dto.getWeightKg());
        product.setImageUrl(dto.getImageUrl());
        product.setStatus(dto.getStatus());
        product.setActive(dto.isActive());
        setRelationships(product, dto);
    }

    private void setRelationships(Product product, ProductDTO dto) {
        if (dto.getCategoryId() != null) {
            Category category = categoryRepository.findById(dto.getCategoryId())
                .orElseThrow(() -> new ResourceNotFoundException("Category", "id", dto.getCategoryId()));
            product.setCategory(category);
        }
        if (dto.getSupplierId() != null) {
            Supplier supplier = supplierRepository.findById(dto.getSupplierId())
                .orElseThrow(() -> new ResourceNotFoundException("Supplier", "id", dto.getSupplierId()));
            product.setSupplier(supplier);
        }
    }
}
