package com.prism.service;

import com.prism.dto.ProductDto;
import com.prism.exception.DuplicateSkuException;
import com.prism.exception.InsufficientStockException;
import com.prism.exception.ResourceNotFoundException;
import com.prism.model.Product;
import com.prism.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class InventoryService {

    private final ProductRepository productRepository;

    public List<Product> getAllActiveProducts() {
        return productRepository.findByActiveTrue();
    }

    public List<Product> getByCategory(Product.ProductCategory category) {
        return productRepository.findByCategoryAndActiveTrue(category);
    }

    public Product getProduct(Long id) {
        return productRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + id));
    }

    public List<Product> getLowStockProducts() {
        return productRepository.findLowStockProducts();
    }

    @Transactional
    public Product createProduct(ProductDto.CreateProductRequest request) {
        if (productRepository.existsBySku(request.getSku())) {
            throw new DuplicateSkuException("SKU already exists: " + request.getSku());
        }

        Product product = new Product();
        product.setName(request.getName());
        product.setDescription(request.getDescription());
        product.setSku(request.getSku().toUpperCase());
        product.setPrice(request.getPrice());
        product.setStockLevel(request.getStockLevel());
        product.setLowStockThreshold(request.getLowStockThreshold());
        product.setCategory(request.getCategory());

        Product saved = productRepository.save(product);
        log.info("Created product {} (SKU: {})", saved.getName(), saved.getSku());
        return saved;
    }

    @Transactional
    public Product updateProduct(Long id, ProductDto.UpdateProductRequest request) {
        Product product = getProduct(id);

        if (request.getName()              != null) product.setName(request.getName());
        if (request.getDescription()       != null) product.setDescription(request.getDescription());
        if (request.getPrice()             != null) product.setPrice(request.getPrice());
        if (request.getLowStockThreshold() != null) product.setLowStockThreshold(request.getLowStockThreshold());
        if (request.getCategory()          != null) product.setCategory(request.getCategory());
        if (request.getActive()            != null) product.setActive(request.getActive());

        return productRepository.save(product);
    }

    /**
     * Adjust stock level. Positive delta = restock, negative = reduction.
     * Called by POS service after a sale, or by staff doing a manual adjustment.
     */
    @Transactional
    public Product adjustStock(Long id, int delta, String reason) {
        Product product = getProduct(id);
        int newLevel = product.getStockLevel() + delta;

        if (newLevel < 0) {
            throw new InsufficientStockException(
                "Insufficient stock for %s. Current: %d, requested reduction: %d"
                    .formatted(product.getName(), product.getStockLevel(), Math.abs(delta))
            );
        }

        product.setStockLevel(newLevel);
        Product saved = productRepository.save(product);

        log.info("Stock adjusted for {} (SKU: {}): {} → {} | reason: {}",
            product.getName(), product.getSku(),
            product.getStockLevel(), newLevel, reason);

        if (saved.isLowStock()) {
            log.warn("LOW STOCK ALERT: {} (SKU: {}) is at {} units",
                saved.getName(), saved.getSku(), saved.getStockLevel());
        }

        return saved;
    }

    @Transactional
    public void deleteProduct(Long id) {
        Product product = getProduct(id);
        product.setActive(false);   // Soft delete — preserve history
        productRepository.save(product);
        log.info("Product {} soft-deleted", product.getSku());
    }
}
