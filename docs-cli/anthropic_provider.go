package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"docs-cli/pkg/config"
)

// AnthropicProvider implements ModelProvider for Anthropic's API
type AnthropicProvider struct {
	apiKey string
	cache  *EnterpriseCache
}

// NewAnthropicProvider creates a new Anthropic provider with enterprise caching
func NewAnthropicProvider(apiKey string) *AnthropicProvider {
	return &AnthropicProvider{
		apiKey: apiKey,
		cache:  GetProviderCache("anthropic"),
	}
}

// CallModel calls the Anthropic API with the given parameters
func (p *AnthropicProvider) CallModel(ctx context.Context, prompt, model string, maxTokens int, temperature float64) (string, error) {
	providerConfig := config.GetConfig().Providers.Anthropic
	
	// Validate input parameters
	if prompt == "" {
		return "", fmt.Errorf("prompt cannot be empty")
	}
	if temperature < providerConfig.TemperatureRange.Min || temperature > providerConfig.TemperatureRange.Max {
		return "", fmt.Errorf("temperature must be between %.1f and %.1f", providerConfig.TemperatureRange.Min, providerConfig.TemperatureRange.Max)
	}
	if maxTokens <= 0 {
		return "", fmt.Errorf("maxTokens must be positive")
	}

	// Generate cache key
	cacheKey := GenerateCacheKey("anthropic", prompt, model, maxTokens, temperature)

	// Check cache first
	if cached, found := p.cache.Get(cacheKey); found {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").Debug("Cache hit for API call")
		return cached, nil
	}
	
	LogWithContext().WithField("cache_key", cacheKey[:8]+"...").Debug("Cache miss for API call")

	// Create context with timeout
	ctx, cancel := context.WithTimeout(ctx, providerConfig.Timeout)
	defer cancel()

	// Create request payload
	reqBody := map[string]interface{}{
		"model":          model,
		"max_tokens":     maxTokens,
		"temperature":    temperature,
		"stop_sequences": providerConfig.StopSequences,
		"messages": []map[string]interface{}{
			{
				"role":    "user",
				"content": prompt,
			},
		},
	}

	// Marshal request body
	jsonBody, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request body: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, "POST", providerConfig.APIURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", p.apiKey)
	req.Header.Set("Anthropic-Version", providerConfig.APIVersion)

	// Send request
	client := &http.Client{Timeout: providerConfig.Timeout}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("API request failed: %w", err)
	}
	defer resp.Body.Close()

	// Handle non-200 status
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("API returned status %d: %s - %s", resp.StatusCode, resp.Status, string(body))
	}

	// Parse response
	var apiResp map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	// Extract content from response
	content, ok := apiResp["content"].([]interface{})
	if !ok || len(content) == 0 {
		return "", fmt.Errorf("invalid API response format")
	}

	firstContent, ok := content[0].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("invalid content format in API response")
	}

	text, ok := firstContent["text"].(string)
	if !ok {
		return "", fmt.Errorf("text field missing in API response")
	}

	// Cache the response
	if p.cache.Set(cacheKey, text) {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").
			WithField("response_length", len(text)).
			Debug("Response cached successfully")
	} else {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").
			Warn("Failed to cache response (likely too large)")
	}

	return text, nil
}

// Note: generateCacheKey function moved to cache.go as GenerateCacheKey
