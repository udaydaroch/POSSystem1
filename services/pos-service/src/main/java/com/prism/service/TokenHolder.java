package com.prism.service;

/**
 * Thread-local storage for the raw JWT token.
 * Populated by JwtAuthFilter so InventoryClient can forward it
 * in service-to-service calls.
 */
public class TokenHolder {
    private static final ThreadLocal<String> TOKEN = new ThreadLocal<>();

    public static void setToken(String token) { TOKEN.set(token); }
    public static String getToken()           { return TOKEN.get(); }
    public static void clear()               { TOKEN.remove(); }
}
