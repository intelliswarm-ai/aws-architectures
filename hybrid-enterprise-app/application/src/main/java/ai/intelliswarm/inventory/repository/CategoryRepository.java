package ai.intelliswarm.inventory.repository;

import ai.intelliswarm.inventory.model.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface CategoryRepository extends JpaRepository<Category, UUID> {

    Optional<Category> findByCode(String code);

    List<Category> findByParentCategoryIsNullOrderByDisplayOrder();

    @Query("SELECT c FROM Category c WHERE c.active = true ORDER BY c.displayOrder, c.name")
    List<Category> findAllActiveOrdered();

    boolean existsByCode(String code);
}
