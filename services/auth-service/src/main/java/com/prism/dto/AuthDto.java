package com.prism.dto;

import com.prism.model.User;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

import java.time.LocalDateTime;

public class AuthDto {

    @Data
    public static class RegisterRequest {
        @NotBlank
        @Size(min = 3, max = 50)
        private String username;

        @NotBlank
        @Email
        private String email;

        @NotBlank
        @Size(min = 8, message = "Password must be at least 8 characters")
        private String password;

        @NotNull
        private User.Role role;
    }

    @Data
    public static class LoginRequest {
        @NotBlank
        private String username;

        @NotBlank
        private String password;
    }

    @Data
    public static class AuthResponse {
        private String token;
        private String username;
        private String email;
        private User.Role role;
        private long expiresIn;   // ms

        public AuthResponse(String token, String username, String email, User.Role role, long expiresIn) {
            this.token    = token;
            this.username = username;
            this.email    = email;
            this.role     = role;
            this.expiresIn = expiresIn;
        }
    }

    @Data
    public static class UserResponse {
        private Long id;
        private String username;
        private String email;
        private User.Role role;
        private boolean active;
        private LocalDateTime createdAt;
        private LocalDateTime lastLoginAt;
    }
}
