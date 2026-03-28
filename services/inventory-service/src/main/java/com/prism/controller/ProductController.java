package com.prism.controller;

import com.prism.dto.ProductDto;
import com.prism.model.Product;
import com.prism.service.InventoryService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/inventory")
@RequiredArgsConstructor
public class ProductController {

    private final InventoryService inventoryService;

    @GetMapping("/products")
    public ResponseEntity<List<ProductDto.ProductResponse>> getAllProducts(
            @RequestParam(required = false) Product.ProductCategory category) {

        List<Product> products = category != null
            ? inventoryService.getByCategory(category)
            : inventoryService.getAllActiveProducts();

        return ResponseEntity.ok(products.stream().map(this::toResponse).toList());
    }

    @GetMapping("/products/{id}")
    public ResponseEntity<ProductDto.ProductResponse> getProduct(@PathVariable Long id) {
        return ResponseEntity.ok(toResponse(inventoryService.getProduct(id)));
    }

    @GetMapping("/products/low-stock")
    @PreAuthorize("hasRole('MANAGER') or hasRole('ADMIN')")
    public ResponseEntity<List<ProductDto.ProductResponse>> getLowStock() {
        return ResponseEntity.ok(
            inventoryService.getLowStockProducts().stream().map(this::toResponse).toList()
        );
    }

    @PostMapping("/products")
    @PreAuthorize("hasRole('MANAGER') or hasRole('ADMIN')")
    public ResponseEntity<ProductDto.ProductResponse> createProduct(
            @Valid @RequestBody ProductDto.CreateProductRequest request) {

        return ResponseEntity
            .status(HttpStatus.CREATED)
            .body(toResponse(inventoryService.createProduct(request)));
    }

    @PutMapping("/products/{id}")
    @PreAuthorize("hasRole('MANAGER') or hasRole('ADMIN')")
    public ResponseEntity<ProductDto.ProductResponse> updateProduct(
            @PathVariable Long id,
            @Valid @RequestBody ProductDto.UpdateProductRequest request) {

        return ResponseEntity.ok(toResponse(inventoryService.updateProduct(id, request)));
    }

    @PatchMapping("/products/{id}/stock")
    public ResponseEntity<ProductDto.ProductResponse> adjustStock(
            @PathVariable Long id,
            @RequestParam int delta,
            @RequestParam(defaultValue = "adjustment") String reason) {

        return ResponseEntity.ok(toResponse(inventoryService.adjustStock(id, delta, reason)));
    }

    @DeleteMapping("/products/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteProduct(@PathVariable Long id) {
        inventoryService.deleteProduct(id);
        return ResponseEntity.noContent().build();
    }

    // ── Mapping ──────────────────────────────────────────────────────────────

    private ProductDto.ProductResponse toResponse(Product p) {
        ProductDto.ProductResponse r = new ProductDto.ProductResponse();
        r.setId(p.getId());
        r.setName(p.getName());
        r.setDescription(p.getDescription());
        r.setSku(p.getSku());
        r.setPrice(p.getPrice());
        r.setStockLevel(p.getStockLevel());
        r.setLowStockThreshold(p.getLowStockThreshold());
        r.setLowStock(p.isLowStock());
        r.setCategory(p.getCategory());
        r.setActive(p.isActive());
        r.setCreatedAt(p.getCreatedAt());
        r.setUpdatedAt(p.getUpdatedAt());
        return r;
    }
}
