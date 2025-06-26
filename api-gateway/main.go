// api-gateway/main.go

package main

import (
    "fmt"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"

    "gitea.wkav.cc/tony/jobapp/api-gateway/internal/config"
    "gitea.wkav.cc/tony/jobapp/api-gateway/pkg/health"
)

func main() {
    // Load configuration using our dedicated package.
    config.LoadEnv()
    // Get the populated configuration struct.
    cfg := config.Get()

    // Parse the backend URL from the config struct.
    backendUrl, err := url.Parse(cfg.BackendTarget)
    if err != nil {
        log.Fatalf("Failed to parse backend URL from config: %v", err)
    }

    // Create the reverse proxy for all non-health-check requests.
    proxy := httputil.NewSingleHostReverseProxy(backendUrl)

    // Create a new router (serve mux). This is better than using the default
    // http package router as it gives us more control.
    router := http.NewServeMux()

    // Register the health check handler.
    // This route will be handled directly by the gateway.
    router.HandleFunc("/health", health.HealthCheckHandler)

    // Register the reverse proxy to handle all other requests.
    // The "/" pattern acts as a catch-all.
    router.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        proxy.ServeHTTP(w, r)
    })

    // Construct the port string for the server.
    listenAddr := fmt.Sprintf(":%s", cfg.GatewayPort)

    log.Printf("🚀 Starting API Gateway on %s", listenAddr)
    log.Printf("🎯 Proxying all requests to: %s", cfg.BackendTarget)
    log.Printf("❤️  Health check available at: %s/health", listenAddr)

    // Use our new router with the server.
    if err := http.ListenAndServe(listenAddr, router); err != nil {
        log.Fatalf("❌ Failed to start gateway server: %v", err)
    }
}
