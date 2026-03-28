package com.prism.repository;

import com.prism.model.Sale;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface SaleRepository extends JpaRepository<Sale, Long> {

    Optional<Sale> findByReferenceNumber(String referenceNumber);

    List<Sale> findByCashierUsernameOrderByCreatedAtDesc(String cashierUsername);

    List<Sale> findByStatusOrderByCreatedAtDesc(Sale.SaleStatus status);
}
