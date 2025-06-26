package main

import (
	"fmt"
	"strings"
)

// ThinkingConfig defines thinking parameters for different providers
type ThinkingConfig struct {
	Provider           string
	Model              string
	EnableThinking     bool
	ThinkingLevel      string
	ReasoningTokens    int
	ReasoningEffort    string
}

// getThinkingConfig returns thinking configuration for a model
func getThinkingConfig(settings ModelSettings) ThinkingConfig {
	config := ThinkingConfig{
		Provider:       settings.Provider,
		Model:          settings.Model,
		EnableThinking: settings.EnableThinking,
		ThinkingLevel:  settings.ThinkingLevel,
	}
	
	if !settings.EnableThinking {
		return config
	}
	
	// Configure thinking parameters based on provider and model
	switch settings.Provider {
	case "openrouter":
		config = configureOpenRouterThinking(config, settings.Model)
	case "openai":
		config = configureOpenAIThinking(config, settings.Model)
	case "anthropic":
		config = configureAnthropicThinking(config, settings.Model)
	}
	
	return config
}

// configureOpenRouterThinking sets up thinking for OpenRouter models
func configureOpenRouterThinking(config ThinkingConfig, model string) ThinkingConfig {
	// Check if model supports thinking
	if !supportsThinking("openrouter", model) {
		config.EnableThinking = false
		return config
	}
	
	// Set reasoning tokens based on thinking level (OpenRouter format)
	switch config.ThinkingLevel {
	case "low":
		config.ReasoningTokens = 2048
	case "medium":
		config.ReasoningTokens = 4096  
	case "high":
		config.ReasoningTokens = 8192
	default:
		config.ThinkingLevel = "medium"
		config.ReasoningTokens = 4096
	}
	
	LogWithContext().WithField("provider", "openrouter").
		WithField("model", model).
		WithField("effort", config.ThinkingLevel).
		WithField("max_tokens", config.ReasoningTokens).
		Info("Configured OpenRouter reasoning parameters")
	
	return config
}

// configureOpenAIThinking sets up thinking for OpenAI models
func configureOpenAIThinking(config ThinkingConfig, model string) ThinkingConfig {
	// Check if model supports thinking
	if !supportsThinking("openai", model) {
		config.EnableThinking = false
		return config
	}
	
	// Set reasoning effort based on thinking level
	switch config.ThinkingLevel {
	case "low":
		config.ReasoningEffort = "low"
	case "medium":
		config.ReasoningEffort = "medium"
	case "high":
		config.ReasoningEffort = "high"
	default:
		config.ReasoningEffort = "medium"
	}
	
	LogWithContext().WithField("provider", "openai").
		WithField("model", model).
		WithField("thinking_level", config.ThinkingLevel).
		WithField("reasoning_effort", config.ReasoningEffort).
		Info("Configured OpenAI thinking parameters")
	
	return config
}

// configureAnthropicThinking sets up thinking for Anthropic models
func configureAnthropicThinking(config ThinkingConfig, model string) ThinkingConfig {
	// Check if model supports thinking
	if !supportsThinking("anthropic", model) {
		config.EnableThinking = false
		return config
	}
	
	// Set thinking budget tokens based on level (Anthropic format)
	switch config.ThinkingLevel {
	case "low":
		config.ReasoningTokens = 5000
	case "medium":
		config.ReasoningTokens = 10000
	case "high":
		config.ReasoningTokens = 15000
	default:
		config.ThinkingLevel = "medium"
		config.ReasoningTokens = 10000
	}
	
	LogWithContext().WithField("provider", "anthropic").
		WithField("model", model).
		WithField("thinking_type", "enabled").
		WithField("budget_tokens", config.ReasoningTokens).
		Info("Configured Anthropic thinking parameters")
	
	return config
}

// supportsThinking checks if a model supports thinking capabilities
func supportsThinking(provider, model string) bool {
	config, err := loadModelConfig()
	if err != nil {
		LogWithContext().WithError(err).Error("Failed to load model config for thinking support check")
		return false
	}
	
	var thinkingModels []string
	switch provider {
	case "openrouter":
		thinkingModels = config.OpenRouter.ThinkingModels
	case "openai":
		thinkingModels = config.OpenAI.ThinkingModels
	case "anthropic":
		thinkingModels = config.Anthropic.ThinkingModels
	default:
		return false
	}
	
	for _, supportedModel := range thinkingModels {
		if strings.Contains(model, supportedModel) || supportedModel == model {
			return true
		}
	}
	
	return false
}

// getThinkingCostMultiplier returns cost multiplier for thinking-enabled calls
func getThinkingCostMultiplier(config ThinkingConfig) float64 {
	if !config.EnableThinking {
		return 1.0
	}
	
	// Thinking adds significant computational cost
	switch config.Provider {
	case "openrouter":
		switch config.ThinkingLevel {
		case "low":
			return 1.3
		case "medium":
			return 1.6
		case "high":
			return 2.2
		}
	case "openai":
		switch config.ThinkingLevel {
		case "low":
			return 1.4
		case "medium":
			return 1.8
		case "high":
			return 2.5
		}
	case "anthropic":
		switch config.ThinkingLevel {
		case "low":
			return 1.2
		case "medium":
			return 1.5
		case "high":
			return 2.0
		}
	}
	
	return 1.5 // Default multiplier
}

// formatThinkingParams formats thinking parameters for logging
func formatThinkingParams(config ThinkingConfig) string {
	if !config.EnableThinking {
		return "disabled"
	}
	
	switch config.Provider {
	case "openrouter":
		return fmt.Sprintf("effort=%s, max_tokens=%d", 
			config.ThinkingLevel, config.ReasoningTokens)
	case "openai":
		return fmt.Sprintf("reasoning_effort=%s", config.ReasoningEffort)
	case "anthropic":
		return fmt.Sprintf("type=enabled, budget_tokens=%d", 
			config.ReasoningTokens)
	}
	
	return "enabled"
}