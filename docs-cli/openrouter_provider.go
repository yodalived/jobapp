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

// OpenRouterProvider implements ModelProvider for OpenRouter's API
type OpenRouterProvider struct {
	apiKey string
	cache  *EnterpriseCache
}

// OpenRouter API request/response structures
type OpenRouterRequest struct {
	Model       string                   `json:"model"`
	Messages    []OpenRouterMessage      `json:"messages"`
	MaxTokens   int                      `json:"max_tokens,omitempty"`
	Temperature float64                  `json:"temperature,omitempty"`
	Stream      bool                     `json:"stream"`
	Metadata    OpenRouterMetadata       `json:"metadata,omitempty"`
	Reasoning   *OpenRouterReasoning     `json:"reasoning,omitempty"`
}

type OpenRouterReasoning struct {
	Effort    string `json:"effort"`
	MaxTokens int    `json:"max_tokens,omitempty"`
	Exclude   bool   `json:"exclude"`
	Enabled   bool   `json:"enabled"`
}

type OpenRouterMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type OpenRouterMetadata struct {
	UserID      string `json:"user_id,omitempty"`
	Description string `json:"description,omitempty"`
}

type OpenRouterResponse struct {
	ID      string                `json:"id"`
	Object  string                `json:"object"`
	Created int64                 `json:"created"`
	Model   string                `json:"model"`
	Choices []OpenRouterChoice    `json:"choices"`
	Usage   OpenRouterUsage       `json:"usage"`
}

type OpenRouterChoice struct {
	Index        int                 `json:"index"`
	Message      OpenRouterMessage   `json:"message"`
	FinishReason string              `json:"finish_reason"`
}

type OpenRouterUsage struct {
	PromptTokens     int     `json:"prompt_tokens"`
	CompletionTokens int     `json:"completion_tokens"`
	TotalTokens      int     `json:"total_tokens"`
	TotalCost        float64 `json:"total_cost,omitempty"`
}

// NewOpenRouterProvider creates a new OpenRouter provider with enterprise caching
func NewOpenRouterProvider(apiKey string) *OpenRouterProvider {
	return &OpenRouterProvider{
		apiKey: apiKey,
		cache:  GetProviderCache("openrouter"),
	}
}

// CallModel calls the OpenRouter API with the given parameters
func (p *OpenRouterProvider) CallModel(ctx context.Context, prompt, model string, maxTokens int, temperature float64) (string, error) {
	return p.CallModelWithThinking(ctx, prompt, model, maxTokens, temperature, ThinkingConfig{})
}

// CallModelWithThinking calls the OpenRouter API with thinking parameters
func (p *OpenRouterProvider) CallModelWithThinking(ctx context.Context, prompt, model string, maxTokens int, temperature float64, thinkingConfig ThinkingConfig) (string, error) {
	providerConfig := config.GetConfig().Providers.OpenRouter
	
	// Validate input parameters
	if prompt == "" {
		return "", fmt.Errorf("prompt cannot be empty")
	}
	if temperature < providerConfig.TemperatureRange.Min || temperature > providerConfig.TemperatureRange.Max {
		return "", fmt.Errorf("temperature must be between %.1f and %.1f for OpenRouter", providerConfig.TemperatureRange.Min, providerConfig.TemperatureRange.Max)
	}
	if maxTokens <= 0 {
		return "", fmt.Errorf("maxTokens must be positive")
	}

	// Generate cache key
	cacheKey := GenerateCacheKey("openrouter", prompt, model, maxTokens, temperature)

	// Check cache first
	if cached, found := p.cache.Get(cacheKey); found {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").Debug("Cache hit for OpenRouter API call")
		return cached, nil
	}
	
	LogWithContext().WithField("cache_key", cacheKey[:8]+"...").Debug("Cache miss for OpenRouter API call")

	// Create context with timeout
	ctx, cancel := context.WithTimeout(ctx, providerConfig.Timeout)
	defer cancel()

	// Create request payload optimized for OpenRouter
	reqBody := OpenRouterRequest{
		Model:       model,
		MaxTokens:   maxTokens,
		Temperature: temperature,
		Stream:      false,
		Messages: []OpenRouterMessage{
			{
				Role:    "system",
				Content: "You are an expert technical documentation writer. Create clear, comprehensive, and well-structured documentation.",
			},
			{
				Role:    "user",
				Content: prompt,
			},
		},
		Metadata: OpenRouterMetadata{
			UserID:      providerConfig.Metadata["user_id"],
			Description: providerConfig.Metadata["description"],
		},
	}
	
	// Add thinking parameters if enabled
	if thinkingConfig.EnableThinking && supportsThinking("openrouter", model) {
		reqBody.Reasoning = &OpenRouterReasoning{
			Effort:    thinkingConfig.ThinkingLevel,
			MaxTokens: thinkingConfig.ReasoningTokens,
			Exclude:   false,
			Enabled:   true,
		}
		
		LogWithContext().WithField("model", model).
			WithField("reasoning_effort", thinkingConfig.ThinkingLevel).
			WithField("reasoning_max_tokens", thinkingConfig.ReasoningTokens).
			WithField("thinking_level", thinkingConfig.ThinkingLevel).
			Info("OpenRouter reasoning enabled")
	}

	// Marshal request body
	jsonBody, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal OpenRouter request body: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, "POST", providerConfig.APIURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create OpenRouter request: %w", err)
	}

	// Set headers for OpenRouter API
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+p.apiKey)
	req.Header.Set("HTTP-Referer", providerConfig.Headers["http_referer"])
	req.Header.Set("X-Title", providerConfig.Headers["x_title"])

	// Send request
	client := &http.Client{Timeout: providerConfig.Timeout}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("OpenRouter API request failed: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read OpenRouter response: %w", err)
	}

	// Handle non-200 status codes
	if resp.StatusCode != http.StatusOK {
		// Check for specific OpenRouter error patterns
		if resp.StatusCode == 429 {
			LogWithContext().Warn("OpenRouter rate limit exceeded")
			return "", fmt.Errorf("OpenRouter rate limit exceeded, please try again later")
		}
		if resp.StatusCode == 401 {
			return "", fmt.Errorf("OpenRouter authentication failed - check API key")
		}
		if resp.StatusCode == 400 {
			return "", fmt.Errorf("OpenRouter bad request: %s", string(body))
		}
		if resp.StatusCode == 402 {
			return "", fmt.Errorf("OpenRouter insufficient credits: %s", string(body))
		}
		if resp.StatusCode == 503 {
			return "", fmt.Errorf("OpenRouter model unavailable: %s", string(body))
		}
		return "", fmt.Errorf("OpenRouter API returned status %d: %s", resp.StatusCode, string(body))
	}

	// Parse response
	var apiResp OpenRouterResponse
	if err := json.Unmarshal(body, &apiResp); err != nil {
		return "", fmt.Errorf("failed to decode OpenRouter response: %w", err)
	}

	// Validate response structure
	if len(apiResp.Choices) == 0 {
		return "", fmt.Errorf("OpenRouter API returned no choices")
	}

	choice := apiResp.Choices[0]
	if choice.Message.Content == "" {
		return "", fmt.Errorf("OpenRouter API returned empty content")
	}

	// Log detailed usage for cost tracking (OpenRouter provides actual costs)
	LogWithContext().WithField("provider", "openrouter").
		WithField("model", model).
		WithField("actual_model", apiResp.Model). // OpenRouter may route to different model
		WithField("prompt_tokens", apiResp.Usage.PromptTokens).
		WithField("completion_tokens", apiResp.Usage.CompletionTokens).
		WithField("total_tokens", apiResp.Usage.TotalTokens).
		WithField("total_cost_usd", apiResp.Usage.TotalCost).
		Info("OpenRouter API call completed")

	// Cache the response
	if p.cache.Set(cacheKey, choice.Message.Content) {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").
			WithField("response_length", len(choice.Message.Content)).
			Debug("OpenRouter response cached successfully")
	} else {
		LogWithContext().WithField("cache_key", cacheKey[:8]+"...").
			Warn("Failed to cache OpenRouter response (likely too large)")
	}

	return choice.Message.Content, nil
}
