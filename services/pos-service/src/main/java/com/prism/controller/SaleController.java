package com.prism.controller;

import com.prism.dto.SaleDto;
import com.prism.model.Sale;
import com.prism.model.SaleLineItem;
import com.prism.service.SaleService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/pos")
@RequiredArgsConstructor
public class SaleController {

    private final SaleService saleService;

    @PostMapping("/sale")
    public ResponseEntity<SaleDto.SaleResponse> createSale(
            @Valid @RequestBody SaleDto.CreateSaleRequest request) {

        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        Sale sale = saleService.createSale(request, username);
        return ResponseEntity.status(HttpStatus.CREATED).body(toResponse(sale));
    }

    @GetMapping("/sale/{id}")
    public ResponseEntity<SaleDto.SaleResponse> getSale(@PathVariable Long id) {
        return ResponseEntity.ok(toResponse(saleService.getSale(id)));
    }

    @GetMapping("/sales")
    public ResponseEntity<List<SaleDto.SaleResponse>> getAllSales() {
        return ResponseEntity.ok(
            saleService.getAllSales().stream().map(this::toResponse).toList()
        );
    }

    @PostMapping("/sale/{id}/void")
    public ResponseEntity<SaleDto.SaleResponse> voidSale(@PathVariable Long id) {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        Sale voided = saleService.voidSale(id, username);
        return ResponseEntity.ok(toResponse(voided));
    }

    // ── Mapping ──────────────────────────────────────────────────────────

    private SaleDto.SaleResponse toResponse(Sale sale) {
        SaleDto.SaleResponse r = new SaleDto.SaleResponse();
        r.setId(sale.getId());
        r.setReferenceNumber(sale.getReferenceNumber());
        r.setCashierUsername(sale.getCashierUsername());
        r.setStatus(sale.getStatus());
        r.setSubtotal(sale.getSubtotal());
        r.setTaxAmount(sale.getTaxAmount());
        r.setTotal(sale.getTotal());
        r.setPaymentMethod(sale.getPaymentMethod());
        r.setCreatedAt(sale.getCreatedAt());
        r.setLineItems(sale.getLineItems().stream().map(this::toLineResponse).toList());
        return r;
    }

    private SaleDto.LineItemResponse toLineResponse(SaleLineItem item) {
        SaleDto.LineItemResponse r = new SaleDto.LineItemResponse();
        r.setProductId(item.getProductId());
        r.setProductName(item.getProductName());
        r.setSku(item.getSku());
        r.setQuantity(item.getQuantity());
        r.setUnitPrice(item.getUnitPrice());
        r.setLineTotal(item.getLineTotal());
        return r;
    }
}
