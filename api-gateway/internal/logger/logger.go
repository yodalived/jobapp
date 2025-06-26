package logger

import (
    "bytes"
    "context"
    "encoding/json"
    "log/slog"
    "net/http"
    "os"
    "sync"
    "time"

    "gitea.wkav.cc/tony/jobapp/api-gateway/internal/config"
)

// Init sets up the logger with potentially multiple destinations and resilience patterns.
func Init(cfg config.Config) {
    var handlers []slog.Handler

    // 1. Always add the console handler (text or json)
    opts := &slog.HandlerOptions{Level: parseLogLevel(cfg.LogLevel)}
    switch cfg.LogFormat {
    case "json":
        handlers = append(handlers, slog.NewJSONHandler(os.Stdout, opts))
    default:
        handlers = append(handlers, slog.NewTextHandler(os.Stdout, opts))
    }

    // 2. Conditionally add the resilient HTTP ingestion handler
    if cfg.LogIngestEnabled && cfg.LogIngestURL != "" {
        httpHandler := NewHTTPHandler(cfg, opts)
        handlers = append(handlers, httpHandler)
        slog.Info("Log ingestion enabled", "url", cfg.LogIngestURL, "queue_size", cfg.LogIngestQueueSize)
    }

    // 3. Create a multi-handler that writes to all configured handlers
    multiHandler := NewMultiHandler(handlers...)
    logger := slog.New(multiHandler).With("service", "api-gateway")
    slog.SetDefault(logger)
}

// --- Multi Handler to broadcast logs ---

type MultiHandler struct {
    handlers []slog.Handler
}

func NewMultiHandler(handlers ...slog.Handler) *MultiHandler {
    return &MultiHandler{handlers: handlers}
}

func (h *MultiHandler) Enabled(ctx context.Context, level slog.Level) bool {
    for _, handler := range h.handlers {
        if handler.Enabled(ctx, level) {
            return true
        }
    }
    return false
}

func (h *MultiHandler) Handle(ctx context.Context, r slog.Record) error {
    for _, handler := range h.handlers {
        // We ignore errors here; a failing log handler should not stop others.
        _ = handler.Handle(ctx, r)
    }
    return nil
}

func (h *MultiHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
    newHandlers := make([]slog.Handler, len(h.handlers))
    for i, handler := range h.handlers {
        newHandlers[i] = handler.WithAttrs(attrs)
    }
    return NewMultiHandler(newHandlers...)
}

func (h *MultiHandler) WithGroup(name string) slog.Handler {
    newHandlers := make([]slog.Handler, len(h.handlers))
    for i, handler := range h.handlers {
        newHandlers[i] = handler.WithGroup(name)
    }
    return NewMultiHandler(newHandlers...)
}

// --- Resilient HTTP Handler for log ingestion ---

type HTTPHandler struct {
    opts     slog.HandlerOptions
    client   http.Client
    url      string
    logQueue chan slog.Record
    wg       sync.WaitGroup

    // Circuit Breaker state
    mu                  sync.Mutex
    consecutiveFailures int
    failureThreshold    int
    circuitOpen         bool
    lastFailureTime     time.Time
    retryAfter          time.Duration
}

func NewHTTPHandler(cfg config.Config, opts *slog.HandlerOptions) *HTTPHandler {
    handler := &HTTPHandler{
        opts: *opts,
        url:  cfg.LogIngestURL,
        client: http.Client{
            Timeout: time.Duration(cfg.LogIngestTimeoutMS) * time.Millisecond,
        },
        logQueue:         make(chan slog.Record, cfg.LogIngestQueueSize),
        failureThreshold: cfg.LogIngestFailureThreshold,
        retryAfter:       10 * time.Second, // Cooldown period for circuit breaker
    }

    // Start a dedicated worker goroutine to process the log queue.
    handler.wg.Add(1)
    go handler.worker(cfg)

    return handler
}

// Handle is designed to be non-blocking. It sends the log record to a buffered channel.
func (h *HTTPHandler) Handle(_ context.Context, r slog.Record) error {
    select {
    case h.logQueue <- r:
        // Log successfully queued.
    default:
        // Queue is full, log is dropped to prevent blocking.
        slog.Warn("Log ingestion queue is full. Dropping log record.")
    }
    return nil
}

// worker processes logs from the queue in the background.
func (h *HTTPHandler) worker(cfg config.Config) {
    defer h.wg.Done()
    for record := range h.logQueue {
        if h.isCircuitOpen() {
            continue // Drop log if circuit is open
        }

        err := h.sendWithRetries(record, cfg.LogIngestRetryAttempts)
        if err != nil {
            h.tripCircuit()
        } else {
            h.resetCircuit()
        }
    }
}

// sendWithRetries attempts to send a log, retrying on failure.
func (h *HTTPHandler) sendWithRetries(r slog.Record, maxRetries int) error {
    var lastErr error
    for attempt := 0; attempt < maxRetries; attempt++ {
        lastErr = h.send(r)
        if lastErr == nil {
            return nil // Success
        }
        time.Sleep(time.Duration(50*attempt) * time.Millisecond) // Simple backoff
    }
    slog.Error("Failed to send log after multiple retries", "error", lastErr)
    return lastErr
}

// send performs the actual HTTP request.
func (h *HTTPHandler) send(r slog.Record) error {
    data := make(map[string]interface{})
    data["time"] = r.Time
    data["level"] = r.Level.String()
    data["msg"] = r.Message
    r.Attrs(func(a slog.Attr) bool {
        data[a.Key] = a.Value.Any()
        return true
    })

    payload, err := json.Marshal(data)
    if err != nil {
        return err
    }

    req, err := http.NewRequest(http.MethodPost, h.url, bytes.NewBuffer(payload))
    if err != nil {
        return err
    }
    req.Header.Set("Content-Type", "application/json")

    resp, err := h.client.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    if resp.StatusCode < 200 || resp.StatusCode >= 300 {
        return &slog.Error{Msg: "received non-2xx response: " + resp.Status}
    }
    return nil
}

// --- Circuit Breaker Methods ---

func (h *HTTPHandler) isCircuitOpen() bool {
    h.mu.Lock()
    defer h.mu.Unlock()
    if !h.circuitOpen {
        return false
    }
    // If circuit is open, check if the cooldown period has passed.
    if time.Since(h.lastFailureTime) > h.retryAfter {
        // Allow one "probe" request to go through.
        h.circuitOpen = false
        return false
    }
    return true
}

func (h *HTTPHandler) tripCircuit() {
    h.mu.Lock()
    defer h.mu.Unlock()
    h.consecutiveFailures++
    if h.consecutiveFailures >= h.failureThreshold {
        if !h.circuitOpen {
            slog.Warn("Circuit breaker tripped for log ingestion endpoint.", "url", h.url)
            h.circuitOpen = true
        }
        h.lastFailureTime = time.Now()
    }
}

func (h *HTTPHandler) resetCircuit() {
    h.mu.Lock()
    defer h.mu.Unlock()
    if h.consecutiveFailures > 0 {
        slog.Info("Circuit breaker reset for log ingestion endpoint.")
    }
    h.consecutiveFailures = 0
    h.circuitOpen = false
}

// Close gracefully shuts down the HTTP handler worker.
func (h *HTTPHandler) Close() {
    close(h.logQueue)
    h.wg.Wait()
}

// --- Unchanged Methods ---

func (h *HTTPHandler) Enabled(_ context.Context, level slog.Level) bool {
    return level >= h.opts.Level
}

func (h *HTTPHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
    // This simple handler doesn't support nested attributes for the HTTP endpoint.
    return h
}
func (h *HTTPHandler) WithGroup(name string) slog.Handler {
    // This simple handler doesn't support groups for the HTTP endpoint.
    return h
}

func parseLogLevel(level string) slog.Level {
    switch level {
    case "DEBUG":
        return slog.LevelDebug
    case "INFO":
        return slog.LevelInfo
    case "WARN":
        return slog.LevelWarn
    case "ERROR":
        return slog.LevelError
    default:
        return slog.LevelInfo
    }
}
