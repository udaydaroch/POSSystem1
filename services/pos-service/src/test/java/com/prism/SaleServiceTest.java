package com.prism.service;

import com.prism.dto.SaleDto;
import com.prism.exception.ResourceNotFoundException;
import com.prism.model.Sale;
import com.prism.repository.SaleRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("SaleService")
class SaleServiceTest {

    @Mock SaleRepository saleRepository;
    @Mock InventoryClient inventoryClient;
    @InjectMocks SaleService saleService;

    private SaleDto.CreateSaleRequest request;
    private InventoryClient.ProductInfo product;

    @BeforeEach
    void setUp() {
        SaleDto.LineItemRequest item = new SaleDto.LineItemRequest();
        item.setProductId(1L);
        item.setQuantity(2);

        request = new SaleDto.CreateSaleRequest();
        request.setItems(List.of(item));
        request.setPaymentMethod(Sale.PaymentMethod.EFTPOS);

        product = new InventoryClient.ProductInfo(
            1L, "Samsung TV 55\"", "SAM-TV-55",
            new BigDecimal("999.00"), 10
        );
    }

    @Test
    @DisplayName("createSale — computes NZ GST correctly")
    void createSale_gstCalculation() {
        when(inventoryClient.getProductOrThrow(1L)).thenReturn(product);
        when(saleRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        Sale sale = saleService.createSale(request, "cashier1");

        // Total = 2 × $999.00 = $1998.00
        assertThat(sale.getTotal()).isEqualByComparingTo("1998.00");

        // GST (15%) backed out of GST-inclusive price: 1998 × 0.15/1.15 = 260.87
        assertThat(sale.getTaxAmount()).isEqualByComparingTo("260.87");

        // Ex-GST subtotal
        assertThat(sale.getSubtotal()).isEqualByComparingTo("1737.13");

        assertThat(sale.getStatus()).isEqualTo(Sale.SaleStatus.COMPLETED);
        assertThat(sale.getCashierUsername()).isEqualTo("cashier1");
        assertThat(sale.getReferenceNumber()).startsWith("PRZ-");
    }

    @Test
    @DisplayName("createSale — throws when insufficient stock")
    void createSale_insufficientStock_throws() {
        InventoryClient.ProductInfo lowStock = new InventoryClient.ProductInfo(
            1L, "Samsung TV 55\"", "SAM-TV-55", new BigDecimal("999.00"), 1 // only 1 in stock
        );
        when(inventoryClient.getProductOrThrow(1L)).thenReturn(lowStock);

        // Request wants 2, only 1 available
        assertThatThrownBy(() -> saleService.createSale(request, "cashier1"))
            .isInstanceOf(IllegalStateException.class)
            .hasMessageContaining("Insufficient stock");

        verify(saleRepository, never()).save(any());
    }

    @Test
    @DisplayName("createSale — decrements stock after successful sale")
    void createSale_decrementsStock() {
        when(inventoryClient.getProductOrThrow(1L)).thenReturn(product);
        when(saleRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        saleService.createSale(request, "cashier1");

        verify(inventoryClient).decrementStock(1L, 2);
    }

    @Test
    @DisplayName("voidSale — changes status to VOIDED and reinstates stock")
    void voidSale_success() {
        Sale completedSale = new Sale();
        completedSale.setId(1L);
        completedSale.setStatus(Sale.SaleStatus.COMPLETED);
        completedSale.setLineItems(List.of());

        when(saleRepository.findById(1L)).thenReturn(Optional.of(completedSale));
        when(saleRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        Sale voided = saleService.voidSale(1L, "manager1");

        assertThat(voided.getStatus()).isEqualTo(Sale.SaleStatus.VOIDED);
    }

    @Test
    @DisplayName("voidSale — throws when sale not found")
    void voidSale_notFound_throws() {
        when(saleRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> saleService.voidSale(99L, "manager1"))
            .isInstanceOf(ResourceNotFoundException.class);
    }
}
