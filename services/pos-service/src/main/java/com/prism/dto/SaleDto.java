package com.prism.dto;

import com.prism.model.Sale;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public class SaleDto {

    // ── Inbound ─────────────────────────────────────────────────────────

    @Data
    public static class CreateSaleRequest {

        @NotEmpty(message = "At least one item is required")
        @Valid
        private List<LineItemRequest> items;

        @NotNull(message = "Payment method is required")
        private Sale.PaymentMethod paymentMethod;
    }

    @Data
    public static class LineItemRequest {

        @NotNull
        private Long productId;

        @Min(value = 1, message = "Quantity must be at least 1")
        private int quantity;
    }

    // ── Outbound ────────────────────────────────────────────────────────

    @Data
    public static class SaleResponse {
        private Long id;
        private String referenceNumber;
        private String cashierUsername;
        private Sale.SaleStatus status;
        private List<LineItemResponse> lineItems;
        private BigDecimal subtotal;
        private BigDecimal taxAmount;
        private BigDecimal total;
        private Sale.PaymentMethod paymentMethod;
        private LocalDateTime createdAt;
    }

    @Data
    public static class LineItemResponse {
        private Long productId;
        private String productName;
        private String sku;
        private int quantity;
        private BigDecimal unitPrice;
        private BigDecimal lineTotal;
    }
}
