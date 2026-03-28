package com.prism.security;

import com.prism.model.User;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;

/**
 * Issues JWT tokens. Other services only verify — they never need this class.
 * The token embeds the username as subject and the user's role in a "roles" claim
 * so downstream services can enforce role-based access without a database call.
 */
@Component
public class JwtTokenProvider {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.expiration-ms}")
    private long expirationMs;

    public String generateToken(User user) {
        Date now    = new Date();
        Date expiry = new Date(now.getTime() + expirationMs);

        return Jwts.builder()
            .subject(user.getUsername())
            .issuedAt(now)
            .expiration(expiry)
            .claim("roles", List.of(user.getRole().asSpringRole()))
            .claim("email", user.getEmail())
            .signWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8)))
            .compact();
    }

    public long getExpirationMs() {
        return expirationMs;
    }
}
