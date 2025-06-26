package config

import (
    "log"
    "os"
    "path/filepath"
    "strconv"
    "strings"

    "github.com/joho/godotenv"
)

// Config holds all configuration for the application.
type Config struct {
    GatewayPort   string
    BackendTarget string
    // Logging configuration
    LogFormat        string
    LogLevel         string
    LogIngestEnabled bool
    LogIngestURL     string
    // Anti-blocking resilience settings
    LogIngestTimeoutMS          int
    LogIngestQueueSize          int
    LogIngestRetryAttempts      int
    LogIngestLatencyThresholdMS int
    LogIngestFailureThreshold   int
    LogIngestDropPolicy         string
}

var appConfig Config

// LoadEnv loads environment variables and populates the appConfig struct.
func LoadEnv() {
    loadDotEnv()

    ingestEnabled, _ := strconv.ParseBool(getEnv("LOG_INGEST_ENABLED", "false"))
    timeout, _ := strconv.Atoi(getEnv("LOG_INGEST_TIMEOUT_MS", "2000"))
    queueSize, _ := strconv.Atoi(getEnv("LOG_INGEST_QUEUE_SIZE", "1000"))
    retries, _ := strconv.Atoi(getEnv("LOG_INGEST_RETRY_ATTEMPTS", "3"))
    latencyThreshold, _ := strconv.Atoi(getEnv("LOG_INGEST_LATENCY_THRESHOLD_MS", "1000"))
    failureThreshold, _ := strconv.Atoi(getEnv("LOG_INGEST_FAILURE_THRESHOLD", "5"))

    appConfig = Config{
        GatewayPort:                 getEnv("GATEWAY_PORT", "8000"),
        BackendTarget:               getEnv("GATEWAY_BACKEND_TARGET", "http://localhost:8048"),
        LogFormat:                   strings.ToLower(getEnv("LOG_FORMAT", "text")),
        LogLevel:                    strings.ToUpper(getEnv("LOG_LEVEL", "INFO")),
        LogIngestEnabled:            ingestEnabled,
        LogIngestURL:                getEnv("LOG_INGEST_URL", ""),
        LogIngestTimeoutMS:          timeout,
        LogIngestQueueSize:          queueSize,
        LogIngestRetryAttempts:      retries,
        LogIngestLatencyThresholdMS: latencyThreshold,
        LogIngestFailureThreshold:   failureThreshold,
        LogIngestDropPolicy:         strings.ToLower(getEnv("LOG_INGEST_DROP_POLICY", "newest")),
    }

    log.Println("✅ Configuration loaded.")
}

// ... (Get, getEnv, loadDotEnv, findProjectRoot functions remain the same) ...
func Get() Config {
    return appConfig
}

func getEnv(key, fallback string) string {
    if value, ok := os.LookupEnv(key); ok {
        return value
    }
    return fallback
}

func loadDotEnv() {
    envPath := os.Getenv("ENV_FILE_PATH")
    if envPath == "" {
        projectRoot, err := findProjectRoot(".env")
        if err != nil {
            log.Println("Warning: Could not find project root (.env file).")
            return
        }
        envPath = filepath.Join(projectRoot, ".env")
    }
    err := godotenv.Load(envPath)
    if err != nil {
        log.Printf("Warning: Could not load .env file from path %s.", envPath)
    }
}

func findProjectRoot(marker string) (string, error) {
    dir, err := os.Getwd()
    if err != nil {
        return "", err
    }
    for {
        if _, err := os.Stat(filepath.Join(dir, marker)); err == nil {
            return dir, nil
        }
        parent := filepath.Dir(dir)
        if parent == dir {
            return "", os.ErrNotExist
        }
        dir = parent
    }
}
