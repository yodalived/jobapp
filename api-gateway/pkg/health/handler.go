package health

import (
    "encoding/json"
    "log"
    "net/http"
)

// HealthStatus represents the structure of our health check response.
type HealthStatus struct {
    Status  string `json:"status"`
    Service string `json:"service"`
}

// HealthCheckHandler is an http.Handler that responds with the service's health status.
func HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
    // Ensure we only handle GET requests for this endpoint.
    if r.Method != http.MethodGet {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }

    // Create the response data.
    status := HealthStatus{
        Status:  "ok",
        Service: "api-gateway",
    }

    // Set the content type header to application/json.
    w.Header().Set("Content-Type", "application/json")
    // Write the 200 OK status code.
    w.WriteHeader(http.StatusOK)

    // Encode the status struct directly to the response writer.
    // This is more efficient than marshalling to a byte slice first.
    if err := json.NewEncoder(w).Encode(status); err != nil {
        // If encoding fails, log the error. The headers are already sent,
        // so we can't send a different status code.
        log.Printf("Error encoding health check response: %v", err)
    }
}
