package main

import "context"

// ModelProvider defines the interface for all model providers
type ModelProvider interface {
	CallModel(ctx context.Context, prompt, model string, maxTokens int, temperature float64) (string, error)
}

// ProviderFactory creates model providers based on provider name
func ProviderFactory(providerName, apiKey string) ModelProvider {
	switch providerName {
	case "anthropic":
		return NewAnthropicProvider(apiKey)
	case "openai":
		return NewOpenAIProvider(apiKey)
	case "openrouter":
		return NewOpenRouterProvider(apiKey)
	default:
		return nil
	}
}
