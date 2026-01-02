package ai.intelliswarm.inventory.repository;

import ai.intelliswarm.inventory.model.Supplier;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface SupplierRepository extends JpaRepository<Supplier, UUID> {

    Optional<Supplier> findByCode(String code);

    Page<Supplier> findByNameContainingIgnoreCase(String name, Pageable pageable);

    @Query("SELECT s FROM Supplier s WHERE s.active = true ORDER BY s.name")
    List<Supplier> findAllActive();

    boolean existsByCode(String code);
}
