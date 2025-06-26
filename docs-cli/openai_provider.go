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

// OpenAIProvider implements ModelProvider for OpenAI's API
type OpenAIProvider struct {
	apiKey string
	cache  *EnterpriseCache
}

// OpenAI API request/response structures
type OpenAIRequest struct {
	Model       string            `json:"model"`
	Messages    []OpenAIMessage   `json:"messages"`
	MaxTokens   int               `json:"max_tokens"`
	Temperature float64           `json:"temperature"`
	Stream      bool              `json:"stream"`
}

type OpenAIMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type OpenAIResponse struct {
	ID      string         `json:"id"`
	Object  string         `json:"object"`
	Created int64          `json:"created"`
	Model   string         `json:"model"`
	Choices []OpenAIChoice `json:"choices"`
	Usage   OpenAIUsage    `json:"usage"`
}

type OpenAIChoice struct {
	Index        int           `json:"index"`
	Message      OpenAIMessage `json:"message"`
	FinishReason string        `json:"finish_reason"`
}

type OpenAIUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// NewOpenAIProvider creates a new OpenAI provider with enterprise caching
func NewOpenAIProvider(apiKey string) *OpenAIProvider {
	return &OpenAIProvider{
		apiKey: apiKey,
		cache:  GetProviderCache("openai"),
	}
}

// CallModel calls the OpenAI API with the given parameters
func (p *OpenAIProvider) CallModel(ctx context.Context, prompt, model string, maxTokens int, temperature float64) (string, error) {
	providerConfig := config.GetConfig().Providers.OpenAI
	
	// Validate input parameters
	if prompt == "" {
		return "", fmt.Errorf("prompt cannot be empty")
	}
	if temperature < providerConfig.TemperatureRange.Min || temperature > providerConfig.TemperatureRange.Max {
		return "", fmt.Errorf("temperature must be between %.1f and %.1f for OpenAI", providerConfig.TemperatureRange.Min, providerConfig.TemperatureRange.Max)
	}
	if maxTokens <= 0 {
		return "", fmt.Errorf("maxTokens must be positive")
	}

	// Generate cache key
	cacheKey := GenerateCacheKey("openai", prompt, model, maxTokens, temperature)

	// Check cache first
	if cached, found := p.cache.Get(cacheKey); found {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").Debug("Cache hit for OpenAI API call")
		return cached, nil
	}
	
	LogWithContext().WithField("cache_key", cacheKey[:8]+"...").Debug("Cache miss for OpenAI API call")

	// Create context with timeout
	ctx, cancel := context.WithTimeout(ctx, providerConfig.Timeout)
	defer cancel()

	// Create request payload optimized for OpenAI
	reqBody := OpenAIRequest{
		Model:       model,
		MaxTokens:   maxTokens,
		Temperature: temperature,
		Stream:      false, // Disable streaming for simplicity
		Messages: []OpenAIMessage{
			{
				Role:    "system",
				Content: "You are a technical documentation expert. Generate high-quality, practical documentation.",
			},
			{
				Role:    "user",
				Content: prompt,
			},
		},
	}

	// Marshal request body
	jsonBody, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal OpenAI request body: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, "POST", providerConfig.APIURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create OpenAI request: %w", err)
	}

	// Set headers for OpenAI API
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+p.apiKey)

	// Send request
	client := &http.Client{Timeout: providerConfig.Timeout}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("OpenAI API request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read OpenAI response: %w", err)
	}

	// Handle non-200 status codes
	if resp.StatusCode != http.StatusOK {
		// Check for specific OpenAI error patterns
		if resp.StatusCode == 429 {
			LogWithContext().Warn("OpenAI rate limit exceeded")
			return "", fmt.Errorf("OpenAI rate limit exceeded, please try again later")
		}
		if resp.StatusCode == 401 {
			return "", fmt.Errorf("OpenAI authentication failed - check API key")
		}
		if resp.StatusCode == 400 {
			return "", fmt.Errorf("OpenAI bad request: %s", string(body))
		}
		return "", fmt.Errorf("OpenAI API returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var apiResp OpenAIResponse
	if err := json.Unmarshal(body, &apiResp); err != nil {
		return "", fmt.Errorf("failed to decode OpenAI response: %w", err)
	}

	// Validate response structure
	if len(apiResp.Choices) == 0 {
		return "", fmt.Errorf("OpenAI API returned no choices")
	}

	choice := apiResp.Choices[0]
	if choice.Message.Content == "" {
		return "", fmt.Errorf("OpenAI API returned empty content")
	}

	// Log token usage for cost tracking
	LogWithContext().WithField("provider", "openai").
		WithField("model", model).
		WithField("prompt_tokens", apiResp.Usage.PromptTokens).
		WithField("completion_tokens", apiResp.Usage.CompletionTokens).
		WithField("total_tokens", apiResp.Usage.TotalTokens).
		Info("OpenAI API call completed")

	// Cache the response
	if p.cache.Set(cacheKey, choice.Message.Content) {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").
			WithField("response_length", len(choice.Message.Content)).
			Debug("OpenAI response cached successfully")
	} else {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").
			Warn("Failed to cache OpenAI response (likely too large)")
	}

	return choice.Message.Content, nil
}
