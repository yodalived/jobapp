package main

import (
	"context"
	"fmt"
	"time"

	"github.com/sony/gobreaker"
	"docs-cli/pkg/config"
)

// getResilienceConfig returns resilience configuration from enterprise config
func getResilienceConfig() config.ResilienceConfig {
	return config.GetConfig().Application.Resilience
}

var (
	// Circuit breakers for different providers
	anthropicBreaker *gobreaker.CircuitBreaker
	openaiBreaker    *gobreaker.CircuitBreaker
	defaultBreaker   *gobreaker.CircuitBreaker
)

func init() {
	resilienceConfig := getResilienceConfig()
	cbConfig := resilienceConfig.CircuitBreaker
	
	settings := gobreaker.Settings{
		Name:        "anthropic",
		MaxRequests: cbConfig.MaxRequests,
		Interval:    cbConfig.Interval,
		Timeout:     cbConfig.Timeout,
		ReadyToTrip: func(counts gobreaker.Counts) bool {
			return counts.ConsecutiveFailures >= cbConfig.FailureThreshold
		},
		OnStateChange: func(name string, from gobreaker.State, to gobreaker.State) {
			LogWithContext().WithField("circuit_breaker", name).
				WithField("from_state", from.String()).
				WithField("to_state", to.String()).
				Info("Circuit breaker state changed")
		},
	}
	
	anthropicBreaker = gobreaker.NewCircuitBreaker(settings)
	
	settings.Name = "openai"
	openaiBreaker = gobreaker.NewCircuitBreaker(settings)
	
	settings.Name = "default"
	defaultBreaker = gobreaker.NewCircuitBreaker(settings)
}

// GetCircuitBreaker returns the appropriate circuit breaker for a provider
func GetCircuitBreaker(provider string) *gobreaker.CircuitBreaker {
	switch provider {
	case "anthropic":
		return anthropicBreaker
	case "openai":
		return openaiBreaker
	default:
		return defaultBreaker
	}
}

// RetryableFunc is a function that can be retried
type RetryableFunc func() (interface{}, error)

// RetryConfig holds retry configuration
type RetryConfig struct {
	MaxRetries       int
	InitialDelay     time.Duration
	MaxDelay         time.Duration
	BackoffMultiplier float64
	ShouldRetry      func(error) bool
}

// DefaultRetryConfig returns the default retry configuration
func DefaultRetryConfig() RetryConfig {
	resilienceConfig := getResilienceConfig()
	retryConfig := resilienceConfig.Retry
	
	return RetryConfig{
		MaxRetries:       retryConfig.MaxAttempts,
		InitialDelay:     retryConfig.InitialDelay,
		MaxDelay:         retryConfig.MaxDelay,
		BackoffMultiplier: retryConfig.BackoffMultiplier,
		ShouldRetry:      DefaultShouldRetry,
	}
}

// DefaultShouldRetry determines if an error should trigger a retry
func DefaultShouldRetry(err error) bool {
	if err == nil {
		return false
	}
	
	errStr := err.Error()
	
	// Retry on temporary network errors
	retryableErrors := []string{
		"timeout",
		"connection refused",
		"connection reset",
		"temporary failure",
		"service unavailable",
		"server is currently overloaded",
		"rate limit",
		"too many requests",
		"context deadline exceeded",
	}
	
	for _, retryable := range retryableErrors {
		if contains(errStr, retryable) {
			return true
		}
	}
	
	// Don't retry on authentication errors
	nonRetryableErrors := []string{
		"authentication_error",
		"invalid_request_error",
		"permission_error",
		"not_found_error",
	}
	
	for _, nonRetryable := range nonRetryableErrors {
		if contains(errStr, nonRetryable) {
			return false
		}
	}
	
	// Default to retry for unknown errors
	return true
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && 
		   (s == substr || len(s) > len(substr) && 
		   (s[:len(substr)] == substr || s[len(s)-len(substr):] == substr ||
		   len(s) > len(substr)*2 && findInString(s, substr)))
}

func findInString(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// RetryWithBackoff executes a function with exponential backoff retry
func RetryWithBackoff(ctx context.Context, fn RetryableFunc, config RetryConfig) (interface{}, error) {
	var lastErr error
	delay := config.InitialDelay
	
	for attempt := 0; attempt <= config.MaxRetries; attempt++ {
		if attempt > 0 {
			LogWithContext().WithField("attempt", attempt).
				WithField("delay_ms", delay.Milliseconds()).
				Info("Retrying operation after delay")
			
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(delay):
				// Continue with retry
			}
		}
		
		start := time.Now()
		result, err := fn()
		duration := time.Since(start)
		
		if err == nil {
			if attempt > 0 {
				LogWithContext().WithField("attempt", attempt).
					WithField("duration_ms", duration.Milliseconds()).
					Info("Operation succeeded after retry")
			}
			return result, nil
		}
		
		lastErr = err
		
		LogWithContext().WithError(err).
			WithField("attempt", attempt).
			WithField("duration_ms", duration.Milliseconds()).
			Info("Operation failed")
		
		// Check if we should retry this error
		if !config.ShouldRetry(err) {
			LogWithContext().WithError(err).
				Info("Error is not retryable, stopping")
			break
		}
		
		// Don't retry if this was the last attempt
		if attempt == config.MaxRetries {
			break
		}
		
		// Calculate next delay with exponential backoff
		delay = time.Duration(float64(delay) * config.BackoffMultiplier)
		if delay > config.MaxDelay {
			delay = config.MaxDelay
		}
	}
	
	return nil, fmt.Errorf("operation failed after %d attempts: %w", config.MaxRetries+1, lastErr)
}

// CallWithCircuitBreaker executes a function with circuit breaker protection
func CallWithCircuitBreaker(breaker *gobreaker.CircuitBreaker, fn RetryableFunc) (interface{}, error) {
	return breaker.Execute(func() (interface{}, error) {
		return fn()
	})
}

// ResilientAPICall combines retry logic with circuit breaker for API calls
func ResilientAPICall(ctx context.Context, provider string, fn RetryableFunc) (interface{}, error) {
	breaker := GetCircuitBreaker(provider)
	config := DefaultRetryConfig()
	
	// Wrap the function with circuit breaker
	wrappedFn := func() (interface{}, error) {
		return CallWithCircuitBreaker(breaker, fn)
	}
	
	return RetryWithBackoff(ctx, wrappedFn, config)
}

// MonitorCircuitBreakers logs circuit breaker status periodically
func MonitorCircuitBreakers() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			logCircuitBreakerStatus("anthropic", anthropicBreaker)
			logCircuitBreakerStatus("openai", openaiBreaker)
			logCircuitBreakerStatus("default", defaultBreaker)
		}
	}
}

func logCircuitBreakerStatus(name string, breaker *gobreaker.CircuitBreaker) {
	state := breaker.State()
	counts := breaker.Counts()
	
	LogWithContext().WithField("circuit_breaker", name).
		WithField("state", state.String()).
		WithField("requests", counts.Requests).
		WithField("total_successes", counts.TotalSuccesses).
		WithField("total_failures", counts.TotalFailures).
		WithField("consecutive_successes", counts.ConsecutiveSuccesses).
		WithField("consecutive_failures", counts.ConsecutiveFailures).
		Info("Circuit breaker status")
}