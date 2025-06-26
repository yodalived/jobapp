package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

type ModelConfig struct {
	Default       ModelSettings            `yaml:"default"`
	OpenAI        ProviderConfig           `yaml:"openai"`
	Anthropic     ProviderConfig           `yaml:"anthropic"`
	OpenRouter    ProviderConfig           `yaml:"openrouter"`
	DocumentTypes map[string]ModelSettings `yaml:"document_types"`
}

type ProviderConfig struct {
	APIKey        string            `yaml:"api_key"`
	Models        map[string]string `yaml:"models"`
	MaxTokens     int               `yaml:"max_tokens"`
	Temperature   float64           `yaml:"temperature"`
	ThinkingModels []string         `yaml:"thinking_models"`
}

type ModelSettings struct {
	Provider        string  `yaml:"provider"`
	Model           string  `yaml:"model"`
	MaxTokens       int     `yaml:"max_tokens"`
	Temperature     float64 `yaml:"temperature"`
	ContextStrategy string  `yaml:"context_strategy"`
	EnableThinking  bool    `yaml:"enable_thinking"`
	ThinkingLevel   string  `yaml:"thinking_level"`
}

var modelConfig *ModelConfig

func loadModelConfig() (*ModelConfig, error) {
	if modelConfig != nil {
		return modelConfig, nil
	}

	configPath := "model-config.yaml"
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		return nil, fmt.Errorf("model-config.yaml not found")
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("error reading model-config.yaml: %w", err)
	}

	var config ModelConfig
	err = yaml.Unmarshal(data, &config)
	if err != nil {
		return nil, fmt.Errorf("error parsing model-config.yaml: %w", err)
	}

	modelConfig = &config
	return modelConfig, nil
}

func getModelSettingsForDocType(docType string) (ModelSettings, error) {
	config, err := loadModelConfig()
	if err != nil {
		return ModelSettings{}, err
	}

	// Check if there's a specific config for this document type
	if settings, exists := config.DocumentTypes[docType]; exists {
		return settings, nil
	}

	// Fall back to default
	return config.Default, nil
}

func callModelAPI(prompt, docType string) (string, error) {
	return callModelAPIWithContext(prompt, docType, "service", "")
}

func callModelAPIWithContext(prompt, docType, componentType, provider string) (string, error) {
	// Input validation
	if err := ValidateInput(prompt, "prompt"); err != nil {
		return "", fmt.Errorf("invalid prompt: %w", err)
	}
	
	if err := ValidateInput(docType, "doc_type"); err != nil {
		return "", fmt.Errorf("invalid document type: %w", err)
	}
	
	// Check memory usage before processing
	if err := LimitMemoryUsage("api_call"); err != nil {
		return "", err
	}
	
	// Cost optimization: compress prompt and select optimal model
	optimizedPrompt, optimalModel, costEstimate := OptimizeForCost(prompt, docType, componentType, provider)
	
	LogWithContext().WithField("cost_estimate", costEstimate).
		WithField("original_tokens", EstimateTokens(prompt)).
		WithField("optimized_tokens", EstimateTokens(optimizedPrompt)).
		Info("Cost optimization applied")
	
	settings, err := getModelSettingsForDocType(docType)
	if err != nil {
		return "", fmt.Errorf("error getting model settings: %w", err)
	}
	
	// Override with optimized model if different
	if optimalModel != settings.Model && optimalModel != "" {
		LogWithContext().WithField("original_model", settings.Model).
			WithField("optimal_model", optimalModel).
			Info("Using cost-optimized model selection")
		settings.Model = optimalModel
	}

	config, err := loadModelConfig()
	if err != nil {
		return "", fmt.Errorf("error loading model config: %w", err)
	}
	
	// Use provided provider or fall back to settings
	if provider == "" {
		provider = settings.Provider
	}
	
	// Check provider-specific rate limit
	if err := CheckRateLimit(provider); err != nil {
		return "", err
	}

	// Get API key based on provider
	var apiKey string
	switch provider {
	case "anthropic":
		apiKey = config.Anthropic.APIKey
	case "openai":
		apiKey = config.OpenAI.APIKey
	case "openrouter":
		apiKey = config.OpenRouter.APIKey
	default:
		return "", fmt.Errorf("unsupported provider: %s", provider)
	}

	if apiKey == "" {
		return "", fmt.Errorf("%s API key not set in model-config.yaml", provider)
	}

	// Resolve model name using the models mapping
	actualModel := settings.Model
	var modelMap map[string]string
	switch provider {
	case "anthropic":
		modelMap = config.Anthropic.Models
	case "openai":
		modelMap = config.OpenAI.Models
	case "openrouter":
		modelMap = config.OpenRouter.Models
	}

	if modelID, exists := modelMap[settings.Model]; exists {
		actualModel = modelID
	}

	// Get provider and call model with resilience features
	providerInstance := ProviderFactory(provider, apiKey)
	if providerInstance == nil {
		return "", fmt.Errorf("no provider found for: %s", provider)
	}

	// Use resilient API call with retry and circuit breaker
	start := time.Now()
	result, err := ResilientAPICall(context.Background(), provider, func() (interface{}, error) {
		return providerInstance.CallModel(context.Background(), optimizedPrompt, actualModel, settings.MaxTokens, settings.Temperature)
	})
	duration := time.Since(start)
	
	// Log API call details
	tokensUsed := 0 // TODO: Extract from response if available
	LogAPICall(settings.Provider, actualModel, tokensUsed, duration, err)
	
	if err != nil {
		return "", err
	}
	
	response, ok := result.(string)
	if !ok {
		return "", fmt.Errorf("unexpected response type from API")
	}
	
	return response, nil
}

// callModelAPIWithThinking calls the model API with thinking capabilities
func callModelAPIWithThinking(prompt, docType, componentType, provider string, thinkingConfig ThinkingConfig) (string, error) {
	// Input validation
	if err := ValidateInput(prompt, "prompt"); err != nil {
		return "", fmt.Errorf("invalid prompt: %w", err)
	}
	
	if err := ValidateInput(docType, "doc_type"); err != nil {
		return "", fmt.Errorf("invalid document type: %w", err)
	}
	
	// Check memory usage before processing
	if err := LimitMemoryUsage("api_call"); err != nil {
		return "", err
	}
	
	settings, err := getModelSettingsForDocType(docType)
	if err != nil {
		return "", fmt.Errorf("error getting model settings: %w", err)
	}
	
	config, err := loadModelConfig()
	if err != nil {
		return "", fmt.Errorf("error loading model config: %w", err)
	}
	
	// Use provided provider or fall back to settings
	if provider == "" {
		provider = settings.Provider
	}
	
	// Check provider-specific rate limit
	if err := CheckRateLimit(provider); err != nil {
		return "", err
	}

	// Get API key based on provider
	var apiKey string
	switch provider {
	case "anthropic":
		apiKey = config.Anthropic.APIKey
	case "openai":
		apiKey = config.OpenAI.APIKey
	case "openrouter":
		apiKey = config.OpenRouter.APIKey
	default:
		return "", fmt.Errorf("unsupported provider: %s", provider)
	}

	if apiKey == "" {
		return "", fmt.Errorf("%s API key not set in model-config.yaml", provider)
	}

	// Resolve model name using the models mapping
	actualModel := settings.Model
	var modelMap map[string]string
	switch provider {
	case "anthropic":
		modelMap = config.Anthropic.Models
	case "openai":
		modelMap = config.OpenAI.Models
	case "openrouter":
		modelMap = config.OpenRouter.Models
	}

	if modelID, exists := modelMap[settings.Model]; exists {
		actualModel = modelID
	}

	// Get provider and call model with thinking support
	providerInstance := ProviderFactory(provider, apiKey)
	if providerInstance == nil {
		return "", fmt.Errorf("no provider found for: %s", provider)
	}

	// Use resilient API call with thinking support
	start := time.Now()
	var result interface{}
	var callErr error
	
	// Check if provider supports thinking
	if thinkingConfig.EnableThinking {
		switch provider {
		case "openrouter":
			if openRouterProvider, ok := providerInstance.(*OpenRouterProvider); ok {
				result, callErr = ResilientAPICall(context.Background(), provider, func() (interface{}, error) {
					return openRouterProvider.CallModelWithThinking(context.Background(), prompt, actualModel, settings.MaxTokens, settings.Temperature, thinkingConfig)
				})
			} else {
				// Fallback to regular call if thinking not supported
				result, callErr = ResilientAPICall(context.Background(), provider, func() (interface{}, error) {
					return providerInstance.CallModel(context.Background(), prompt, actualModel, settings.MaxTokens, settings.Temperature)
				})
			}
		default:
			// For providers without thinking support yet, use regular call
			result, callErr = ResilientAPICall(context.Background(), provider, func() (interface{}, error) {
				return providerInstance.CallModel(context.Background(), prompt, actualModel, settings.MaxTokens, settings.Temperature)
			})
		}
	} else {
		// Regular call without thinking
		result, callErr = ResilientAPICall(context.Background(), provider, func() (interface{}, error) {
			return providerInstance.CallModel(context.Background(), prompt, actualModel, settings.MaxTokens, settings.Temperature)
		})
	}
	
	duration := time.Since(start)
	
	// Log API call details
	tokensUsed := 0 // TODO: Extract from response if available
	LogAPICall(settings.Provider, actualModel, tokensUsed, duration, callErr)
	
	if callErr != nil {
		return "", callErr
	}
	
	response, ok := result.(string)
	if !ok {
		return "", fmt.Errorf("unexpected response type from API")
	}
	
	return response, nil
}
