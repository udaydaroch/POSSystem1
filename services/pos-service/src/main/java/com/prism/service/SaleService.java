package com.prism.service;

import com.prism.dto.SaleDto;
import com.prism.exception.ResourceNotFoundException;
import com.prism.exception.SaleVoidException;
import com.prism.model.Sale;
import com.prism.model.SaleLineItem;
import com.prism.repository.SaleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class SaleService {

    private static final BigDecimal GST_RATE = new BigDecimal("0.15"); // NZ GST 15%
    private static final DateTimeFormatter REF_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd");

    private final SaleRepository saleRepository;
    private final InventoryClient inventoryClient;

    /**
     * Process a new sale. Validates stock with the inventory service,
     * calculates GST, persists, and decrements stock.
     */
    @Transactional
    public Sale createSale(SaleDto.CreateSaleRequest request, String cashierUsername) {
        log.info("Processing sale for cashier={} with {} items", cashierUsername, request.getItems().size());

        Sale sale = new Sale();
        sale.setCashierUsername(cashierUsername);
        sale.setPaymentMethod(request.getPaymentMethod());
        sale.setReferenceNumber(generateReference());

        BigDecimal subtotal = BigDecimal.ZERO;

        for (SaleDto.LineItemRequest itemRequest : request.getItems()) {
            // Fetch product info + validate stock from inventory service
            InventoryClient.ProductInfo product = inventoryClient.getProductOrThrow(itemRequest.getProductId());

            if (product.stockLevel() < itemRequest.getQuantity()) {
                throw new IllegalStateException(
                    "Insufficient stock for product '%s': requested %d, available %d"
                        .formatted(product.name(), itemRequest.getQuantity(), product.stockLevel())
                );
            }

            SaleLineItem line = new SaleLineItem();
            line.setSale(sale);
            line.setProductId(product.id());
            line.setProductName(product.name());
            line.setSku(product.sku());
            line.setQuantity(itemRequest.getQuantity());
            line.setUnitPrice(product.price());
            line.setLineTotal(product.price().multiply(BigDecimal.valueOf(itemRequest.getQuantity())));

            sale.getLineItems().add(line);
            subtotal = subtotal.add(line.getLineTotal());
        }

        // NZ GST calculation — prices are GST-inclusive, so we back it out
        BigDecimal taxAmount = subtotal
            .multiply(GST_RATE)
            .divide(BigDecimal.ONE.add(GST_RATE), 2, RoundingMode.HALF_UP);

        sale.setSubtotal(subtotal.subtract(taxAmount).setScale(2, RoundingMode.HALF_UP));
        sale.setTaxAmount(taxAmount);
        sale.setTotal(subtotal.setScale(2, RoundingMode.HALF_UP));
        sale.setStatus(Sale.SaleStatus.COMPLETED);

        Sale saved = saleRepository.save(sale);

        // Decrement stock for each item
        request.getItems().forEach(item ->
            inventoryClient.decrementStock(item.getProductId(), item.getQuantity())
        );

        log.info("Sale {} completed. Total: ${}", saved.getReferenceNumber(), saved.getTotal());
        return saved;
    }

    public Sale getSale(Long id) {
        return saleRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Sale not found: " + id));
    }

    public List<Sale> getAllSales() {
        return saleRepository.findAll();
    }

    /**
     * Void a sale. Only COMPLETED sales can be voided.
     * Reinstates stock for all line items.
     */
    @Transactional
    public Sale voidSale(Long id, String requestingUser) {
        Sale sale = getSale(id);

        if (sale.getStatus() != Sale.SaleStatus.COMPLETED) {
            throw new SaleVoidException("Only completed sales can be voided. Current status: " + sale.getStatus());
        }

        sale.setStatus(Sale.SaleStatus.VOIDED);
        Sale voided = saleRepository.save(sale);

        // Reinstate stock
        sale.getLineItems().forEach(item ->
            inventoryClient.reinstateStock(item.getProductId(), item.getQuantity())
        );

        log.info("Sale {} voided by {}", sale.getReferenceNumber(), requestingUser);
        return voided;
    }

    private String generateReference() {
        return "PRZ-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }
}
