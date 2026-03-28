package com.prism.service;

import com.prism.dto.ProductDto;
import com.prism.exception.ResourceNotFoundException;
import com.prism.model.Product;
import com.prism.repository.ProductRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("InventoryService")
class InventoryServiceTest {

    @Mock ProductRepository productRepository;
    @InjectMocks InventoryService inventoryService;

    private Product product;

    @BeforeEach
    void setUp() {
        product = new Product();
        product.setId(1L);
        product.setName("Samsung TV 55\"");
        product.setSku("SAM-TV-55");
        product.setPrice(new BigDecimal("999.00"));
        product.setStockLevel(10);
        product.setActive(true);
    }

    @Test
    @DisplayName("adjustStock — increments correctly")
    void adjustStock_increment() {
        when(productRepository.findById(1L)).thenReturn(Optional.of(product));
        when(productRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        Product updated = inventoryService.adjustStock(1L, 5, "restock");

        assertThat(updated.getStockLevel()).isEqualTo(15);
    }

    @Test
    @DisplayName("adjustStock — decrements correctly")
    void adjustStock_decrement() {
        when(productRepository.findById(1L)).thenReturn(Optional.of(product));
        when(productRepository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        Product updated = inventoryService.adjustStock(1L, -3, "sale");

        assertThat(updated.getStockLevel()).isEqualTo(7);
    }

    @Test
    @DisplayName("adjustStock — throws when stock would go negative")
    void adjustStock_goesNegative_throws() {
        when(productRepository.findById(1L)).thenReturn(Optional.of(product));

        assertThatThrownBy(() -> inventoryService.adjustStock(1L, -99, "sale"))
            .isInstanceOf(RuntimeException.class)
            .hasMessageContaining("stock");

        verify(productRepository, never()).save(any());
    }

    @Test
    @DisplayName("getProduct — throws ResourceNotFoundException for unknown id")
    void getProduct_notFound_throws() {
        when(productRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> inventoryService.getProduct(99L))
            .isInstanceOf(ResourceNotFoundException.class);
    }

    @Test
    @DisplayName("createProduct — rejects duplicate SKU")
    void createProduct_duplicateSku_throws() {
        when(productRepository.existsBySku("SAM-TV-55")).thenReturn(true);

        ProductDto.CreateProductRequest req = new ProductDto.CreateProductRequest();
        req.setSku("SAM-TV-55");
        req.setName("Another TV");
        req.setPrice(new BigDecimal("899.00"));
        req.setStockLevel(5);

        assertThatThrownBy(() -> inventoryService.createProduct(req))
            .isInstanceOf(RuntimeException.class)
            .hasMessageContaining("SAM-TV-55");
    }
}
