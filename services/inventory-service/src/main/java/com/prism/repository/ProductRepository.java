package com.prism.repository;

import com.prism.model.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    Optional<Product> findBySku(String sku);

    List<Product> findByActiveTrue();

    List<Product> findByCategoryAndActiveTrue(Product.ProductCategory category);

    // Find products running low on stock
    @Query("SELECT p FROM Product p WHERE p.stockLevel <= p.lowStockThreshold AND p.active = true")
    List<Product> findLowStockProducts();

    boolean existsBySku(String sku);
}
