package com.prism.service;

import com.prism.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;

/**
 * HTTP client for communicating with the inventory-service.
 * Forwards the JWT token from the current request so inventory-service
 * can authenticate the call.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class InventoryClient {

    private final RestTemplate restTemplate;

    @Value("${services.inventory-url}")
    private String inventoryServiceUrl;

    // Build headers with the JWT token from the current security context
    private HttpHeaders authHeaders() {
        HttpHeaders headers = new HttpHeaders();
        var auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getCredentials() != null) {
            headers.setBearerAuth(auth.getCredentials().toString());
        }
        // Credentials are null in our setup — we store the raw token in a thread-local instead
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }

    public ProductInfo getProductOrThrow(Long productId) {
        try {
            // Pass the Authorization header from thread-local token storage
            HttpHeaders headers = new HttpHeaders();
            String token = TokenHolder.getToken();
            if (token != null) headers.setBearerAuth(token);

            ResponseEntity<ProductInfo> response = restTemplate.exchange(
                inventoryServiceUrl + "/api/inventory/products/" + productId,
                HttpMethod.GET,
                new HttpEntity<>(headers),
                ProductInfo.class
            );
            return response.getBody();
        } catch (Exception e) {
            log.error("Failed to fetch product {} from inventory service", productId, e);
            throw new ResourceNotFoundException("Product not found or inventory service unavailable: " + productId);
        }
    }

    public void decrementStock(Long productId, int quantity) {
        try {
            HttpHeaders headers = new HttpHeaders();
            String token = TokenHolder.getToken();
            if (token != null) headers.setBearerAuth(token);

            restTemplate.exchange(
                inventoryServiceUrl + "/api/inventory/products/" + productId + "/stock?delta=-" + quantity,
                HttpMethod.PATCH,
                new HttpEntity<>(headers),
                Void.class
            );
        } catch (Exception e) {
            log.error("Failed to decrement stock for product {}", productId, e);
        }
    }

    public void reinstateStock(Long productId, int quantity) {
        try {
            HttpHeaders headers = new HttpHeaders();
            String token = TokenHolder.getToken();
            if (token != null) headers.setBearerAuth(token);

            restTemplate.exchange(
                inventoryServiceUrl + "/api/inventory/products/" + productId + "/stock?delta=" + quantity,
                HttpMethod.PATCH,
                new HttpEntity<>(headers),
                Void.class
            );
        } catch (Exception e) {
            log.error("Failed to reinstate stock for product {}", productId, e);
        }
    }

    public record ProductInfo(Long id, String name, String sku, BigDecimal price, int stockLevel) {}
}
