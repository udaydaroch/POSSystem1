package com.prism.service;

import com.prism.dto.AuthDto;
import com.prism.exception.ConflictException;
import com.prism.model.User;
import com.prism.repository.UserRepository;
import com.prism.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("AuthService")
class AuthServiceTest {

    @Mock UserRepository userRepository;
    @Mock PasswordEncoder passwordEncoder;
    @Mock JwtTokenProvider jwtTokenProvider;
    @InjectMocks AuthService authService;

    private AuthDto.RegisterRequest registerRequest;
    private AuthDto.LoginRequest loginRequest;
    private User savedUser;

    @BeforeEach
    void setUp() {
        registerRequest = new AuthDto.RegisterRequest();
        registerRequest.setUsername("cashier1");
        registerRequest.setEmail("cashier1@prism.nz");
        registerRequest.setPassword("Password1!");
        registerRequest.setRole(User.Role.CASHIER);

        loginRequest = new AuthDto.LoginRequest();
        loginRequest.setUsername("cashier1");
        loginRequest.setPassword("Password1!");

        savedUser = new User();
        savedUser.setId(1L);
        savedUser.setUsername("cashier1");
        savedUser.setEmail("cashier1@prism.nz");
        savedUser.setPasswordHash("$2a$12$hashed");
        savedUser.setRole(User.Role.CASHIER);
        savedUser.setActive(true);
    }

    // ── Registration ──────────────────────────────────────────────────────────

    @Test
    @DisplayName("register — returns token on success")
    void register_success() {
        when(userRepository.existsByUsername("cashier1")).thenReturn(false);
        when(userRepository.existsByEmail("cashier1@prism.nz")).thenReturn(false);
        when(passwordEncoder.encode(any())).thenReturn("$2a$12$hashed");
        when(userRepository.save(any())).thenReturn(savedUser);
        when(jwtTokenProvider.generateToken(any())).thenReturn("jwt.token.here");
        when(jwtTokenProvider.getExpirationMs()).thenReturn(86400000L);

        AuthDto.AuthResponse response = authService.register(registerRequest);

        assertThat(response.getToken()).isEqualTo("jwt.token.here");
        assertThat(response.getUsername()).isEqualTo("cashier1");
        assertThat(response.getRole()).isEqualTo(User.Role.CASHIER);
        verify(userRepository).save(any(User.class));
    }

    @Test
    @DisplayName("register — throws ConflictException when username taken")
    void register_duplicateUsername_throws() {
        when(userRepository.existsByUsername("cashier1")).thenReturn(true);

        assertThatThrownBy(() -> authService.register(registerRequest))
            .isInstanceOf(ConflictException.class)
            .hasMessageContaining("cashier1");

        verify(userRepository, never()).save(any());
    }

    @Test
    @DisplayName("register — throws ConflictException when email taken")
    void register_duplicateEmail_throws() {
        when(userRepository.existsByUsername(any())).thenReturn(false);
        when(userRepository.existsByEmail("cashier1@prism.nz")).thenReturn(true);

        assertThatThrownBy(() -> authService.register(registerRequest))
            .isInstanceOf(ConflictException.class)
            .hasMessageContaining("cashier1@prism.nz");
    }

    // ── Login ─────────────────────────────────────────────────────────────────

    @Test
    @DisplayName("login — returns token with valid credentials")
    void login_success() {
        when(userRepository.findByUsername("cashier1")).thenReturn(Optional.of(savedUser));
        when(passwordEncoder.matches("Password1!", "$2a$12$hashed")).thenReturn(true);
        when(jwtTokenProvider.generateToken(savedUser)).thenReturn("jwt.token.here");
        when(jwtTokenProvider.getExpirationMs()).thenReturn(86400000L);

        AuthDto.AuthResponse response = authService.login(loginRequest);

        assertThat(response.getToken()).isEqualTo("jwt.token.here");
        assertThat(response.getUsername()).isEqualTo("cashier1");
    }

    @Test
    @DisplayName("login — throws BadCredentialsException when user not found")
    void login_userNotFound_throws() {
        when(userRepository.findByUsername(any())).thenReturn(Optional.empty());

        assertThatThrownBy(() -> authService.login(loginRequest))
            .isInstanceOf(BadCredentialsException.class);
    }

    @Test
    @DisplayName("login — throws BadCredentialsException with wrong password")
    void login_wrongPassword_throws() {
        when(userRepository.findByUsername("cashier1")).thenReturn(Optional.of(savedUser));
        when(passwordEncoder.matches(any(), any())).thenReturn(false);

        assertThatThrownBy(() -> authService.login(loginRequest))
            .isInstanceOf(BadCredentialsException.class);
    }

    @Test
    @DisplayName("login — throws BadCredentialsException when account disabled")
    void login_inactiveAccount_throws() {
        savedUser.setActive(false);
        when(userRepository.findByUsername("cashier1")).thenReturn(Optional.of(savedUser));

        assertThatThrownBy(() -> authService.login(loginRequest))
            .isInstanceOf(BadCredentialsException.class)
            .hasMessageContaining("disabled");
    }
}
