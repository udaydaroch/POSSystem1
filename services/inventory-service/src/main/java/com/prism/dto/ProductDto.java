package com.prism.dto;

import com.prism.model.Product;
import jakarta.validation.constraints.*;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class ProductDto {

    @Data
    public static class CreateProductRequest {
        @NotBlank(message = "Product name is required")
        private String name;

        private String description;

        @NotBlank(message = "SKU is required")
        private String sku;

        @NotNull @DecimalMin("0.01")
        private BigDecimal price;

        @Min(0)
        private int stockLevel;

        @Min(1)
        private int lowStockThreshold = 5;

        @NotNull
        private Product.ProductCategory category;
    }

    @Data
    public static class UpdateProductRequest {
        private String name;
        private String description;

        @DecimalMin("0.01")
        private BigDecimal price;

        @Min(1)
        private Integer lowStockThreshold;

        private Product.ProductCategory category;
        private Boolean active;
    }

    @Data
    public static class StockAdjustRequest {
        @NotNull
        private Integer delta;   // positive = restock, negative = sale/shrinkage

        private String reason;
    }

    @Data
    public static class ProductResponse {
        private Long id;
        private String name;
        private String description;
        private String sku;
        private BigDecimal price;
        private int stockLevel;
        private int lowStockThreshold;
        private boolean lowStock;
        private Product.ProductCategory category;
        private boolean active;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;
    }
}
