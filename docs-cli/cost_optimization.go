package main

import (
	"regexp"
	"strings"
	"unicode"

	"docs-cli/pkg/config"
)

// getCostOptConfig returns cost optimization configuration from enterprise config
func getCostOptConfig() config.CostOptConfig {
	return config.GetConfig().CostOpt
}

// TaskComplexity represents the complexity level of a documentation task
type TaskComplexity int

const (
	SimpleTask TaskComplexity = iota
	MediumTask
	ComplexTask
)

// CostEstimate represents the estimated cost for an API call
type CostEstimate struct {
	Provider         string  `json:"provider"`
	Model           string  `json:"model"`
	InputTokens     int     `json:"input_tokens"`
	EstimatedOutputTokens int `json:"estimated_output_tokens"`
	EstimatedInputCost    float64 `json:"estimated_input_cost"`
	EstimatedOutputCost   float64 `json:"estimated_output_cost"`
	TotalEstimatedCost    float64 `json:"total_estimated_cost"`
}

// EstimateTokens approximates token count from text
func EstimateTokens(text string) int {
	costConfig := getCostOptConfig()
	// Remove extra whitespace and count characters
	cleaned := strings.TrimSpace(regexp.MustCompile(`\s+`).ReplaceAllString(text, " "))
	return int(float64(len(cleaned)) * costConfig.TokenEstimationRatio)
}

// AnalyzeTaskComplexity determines the complexity level of a documentation task
func AnalyzeTaskComplexity(prompt string, docType string, componentType string) TaskComplexity {
	promptTokens := EstimateTokens(prompt)
	costConfig := getCostOptConfig()
	thresholds := costConfig.ComplexityThresholds
	
	// Base complexity on prompt size
	var complexity TaskComplexity
	if promptTokens < thresholds.Simple {
		complexity = SimpleTask
	} else if promptTokens < thresholds.Complex {
		complexity = MediumTask
	} else {
		complexity = ComplexTask
	}
	
	// Adjust based on document type
	switch docType {
	case "CHECKLIST":
		// Checklists are usually simpler
		if complexity > SimpleTask {
			complexity--
		}
	case "ARCHITECTURE":
		// Architecture docs are usually more complex
		if complexity < ComplexTask {
			complexity++
		}
	}
	
	// Adjust based on component type
	if componentType == "frontend" && docType == "SETUP" {
		// Frontend setup docs can be complex
		if complexity < MediumTask {
			complexity = MediumTask
		}
	}
	
	return complexity
}

// SelectOptimalModel chooses the most cost-effective model for the task
func SelectOptimalModel(complexity TaskComplexity, provider string) string {
	switch provider {
	case "anthropic":
		switch complexity {
		case SimpleTask:
			return "haiku-3.5" // Fastest, cheapest for simple tasks
		case MediumTask:
			return "sonnett-4" // Good balance
		case ComplexTask:
			return "opus-4" // Most capable for complex tasks
		}
	case "openai":
		switch complexity {
		case SimpleTask:
			return "gpt-3.5-turbo" // Cheapest option
		case MediumTask, ComplexTask:
			return "gpt-4o" // Best quality for medium/complex
		}
	}
	
	// Default fallback
	return "sonnett-4"
}

// CompressPrompt reduces prompt size while preserving essential information
func CompressPrompt(prompt string) string {
	// Start with the original prompt
	compressed := prompt
	originalSize := len(compressed)
	
	// Step 1: Remove excessive whitespace
	compressed = regexp.MustCompile(`\s+`).ReplaceAllString(compressed, " ")
	compressed = strings.TrimSpace(compressed)
	
	// Step 2: Remove comments and metadata that don't affect generation
	compressed = regexp.MustCompile(`(?m)^#.*$`).ReplaceAllString(compressed, "")
	compressed = regexp.MustCompile(`(?m)^\s*//.*$`).ReplaceAllString(compressed, "")
	
	// Step 3: Compress repeated patterns
	compressed = regexp.MustCompile(`\n\s*\n\s*\n+`).ReplaceAllString(compressed, "\n\n")
	
	// Step 4: Remove redundant file extensions in listings
	compressed = regexp.MustCompile(`\.(py|go|ts|tsx|js|jsx|md|yaml|yml|json)`).ReplaceAllString(compressed, "")
	
	// Step 5: Compress common programming patterns
	replacements := map[string]string{
		"import ": "imp ",
		"export ": "exp ",
		"function ": "fn ",
		"interface ": "int ",
		"component ": "comp ",
		"const ": "c ",
		"return ": "ret ",
	}
	
	for old, new := range replacements {
		compressed = strings.ReplaceAll(compressed, old, new)
	}
	
	// Step 6: Remove file paths prefixes for brevity
	compressed = regexp.MustCompile(`/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/`).ReplaceAllString(compressed, "")
	
	// Don't compress too aggressively
	costConfig := getCostOptConfig()
	if len(compressed) < int(float64(originalSize)*costConfig.Compression.MaxRatio) {
		LogWithContext().WithField("original_size", originalSize).
			WithField("compressed_size", len(compressed)).
			WithField("ratio", float64(len(compressed))/float64(originalSize)).
			Warn("Compression too aggressive, reverting")
		return prompt
	}
	
	compressionRatio := float64(len(compressed)) / float64(originalSize)
	
	LogWithContext().WithField("original_size", originalSize).
		WithField("compressed_size", len(compressed)).
		WithField("compression_ratio", compressionRatio).
		WithField("tokens_saved", EstimateTokens(prompt)-EstimateTokens(compressed)).
		Info("Prompt compressed successfully")
	
	return compressed
}

// EstimateCost calculates the estimated cost for an API call
func EstimateCost(provider, model, prompt string, estimatedOutputTokens int) CostEstimate {
	inputTokens := EstimateTokens(prompt)
	costConfig := getCostOptConfig()
	
	var inputCostPer1K, outputCostPer1K float64
	
	switch provider {
	case "anthropic":
		switch model {
		case "opus-4", "claude-opus-4-20250514":
			if pricing, exists := costConfig.Pricing.Anthropic["sonnet4"]; exists {
				inputCostPer1K = pricing.InputCost
				outputCostPer1K = pricing.OutputCost
			} else {
				inputCostPer1K = 0.015
				outputCostPer1K = 0.075
			}
		case "sonnett-4", "claude-sonnet-4-20250514":
			if pricing, exists := costConfig.Pricing.Anthropic["sonnet4"]; exists {
				inputCostPer1K = pricing.InputCost
				outputCostPer1K = pricing.OutputCost
			} else {
				inputCostPer1K = 0.015
				outputCostPer1K = 0.075
			}
		case "haiku-3.5", "claude-3-5-haiku-20241022":
			if pricing, exists := costConfig.Pricing.Anthropic["haiku"]; exists {
				inputCostPer1K = pricing.InputCost
				outputCostPer1K = pricing.OutputCost
			} else {
				inputCostPer1K = 0.0008
				outputCostPer1K = 0.004
			}
		default:
			if pricing, exists := costConfig.Pricing.Anthropic["sonnet4"]; exists {
				inputCostPer1K = pricing.InputCost
				outputCostPer1K = pricing.OutputCost
			} else {
				inputCostPer1K = 0.015
				outputCostPer1K = 0.075
			}
		}
	case "openai":
		if pricing, exists := costConfig.Pricing.OpenAI["gpt4"]; exists {
			inputCostPer1K = pricing.InputCost
			outputCostPer1K = pricing.OutputCost
		} else {
			inputCostPer1K = 0.005
			outputCostPer1K = 0.015
		}
	default:
		if pricing, exists := costConfig.Pricing.Anthropic["sonnet4"]; exists {
			inputCostPer1K = pricing.InputCost
			outputCostPer1K = pricing.OutputCost
		} else {
			inputCostPer1K = 0.015
			outputCostPer1K = 0.075
		}
	}
	
	inputCost := float64(inputTokens) / 1000.0 * inputCostPer1K
	outputCost := float64(estimatedOutputTokens) / 1000.0 * outputCostPer1K
	
	return CostEstimate{
		Provider:              provider,
		Model:                model,
		InputTokens:          inputTokens,
		EstimatedOutputTokens: estimatedOutputTokens,
		EstimatedInputCost:   inputCost,
		EstimatedOutputCost:  outputCost,
		TotalEstimatedCost:   inputCost + outputCost,
	}
}

// EstimateOutputTokens predicts output length based on document type and input
func EstimateOutputTokens(docType string, inputTokens int) int {
	switch docType {
	case "README":
		// READMEs are typically comprehensive
		return inputTokens / 3 // About 33% of input size
	case "SETUP":
		// Setup docs are usually detailed but structured
		return inputTokens / 4 // About 25% of input size
	case "ARCHITECTURE":
		// Architecture docs can be very detailed
		return inputTokens / 2 // About 50% of input size
	case "CHECKLIST":
		// Checklists are usually shorter and structured
		return inputTokens / 6 // About 17% of input size
	default:
		return inputTokens / 4 // Conservative default
	}
}

// OptimizeForCost performs comprehensive provider-specific cost optimization
func OptimizeForCost(prompt, docType, componentType, provider string) (string, string, CostEstimate) {
	// Analyze task complexity
	complexity := AnalyzeTaskComplexity(prompt, docType, componentType)
	
	// Dispatch to provider-specific optimization
	switch provider {
	case "anthropic":
		return OptimizeForAnthropic(prompt, docType, complexity)
	case "openai":
		return OptimizeForOpenAI(prompt, docType, complexity)
	case "openrouter":
		return OptimizeForOpenRouter(prompt, docType, complexity)
	default:
		// Fallback to Anthropic optimization
		return OptimizeForAnthropic(prompt, docType, complexity)
	}
}

// OptimizeForAnthropic handles Anthropic-specific optimization
func OptimizeForAnthropic(prompt, docType string, complexity TaskComplexity) (string, string, CostEstimate) {
	optimalModel := SelectOptimalModel(complexity, "anthropic")
	optimizedPrompt := CompressPrompt(prompt)
	baseOutputEstimate := EstimateOutputTokens(docType, EstimateTokens(optimizedPrompt))
	costEstimate := EstimateCost("anthropic", optimalModel, optimizedPrompt, baseOutputEstimate)
	
	LogWithContext().WithField("provider", "anthropic").
		WithField("original_tokens", EstimateTokens(prompt)).
		WithField("optimized_tokens", EstimateTokens(optimizedPrompt)).
		WithField("complexity", complexity).
		WithField("selected_model", optimalModel).
		WithField("cost_estimate", costEstimate).
		Info("Anthropic-specific cost optimization completed")
	
	return optimizedPrompt, optimalModel, costEstimate
}

// OptimizeForOpenAI handles OpenAI-specific optimization
func OptimizeForOpenAI(prompt, docType string, complexity TaskComplexity) (string, string, CostEstimate) {
	optimalModel := SelectOptimalModel(complexity, "openai")
	optimizedPrompt := CompressPrompt(prompt)
	baseOutputEstimate := EstimateOutputTokens(docType, EstimateTokens(optimizedPrompt))
	costEstimate := EstimateCost("openai", optimalModel, optimizedPrompt, baseOutputEstimate)
	
	LogWithContext().WithField("provider", "openai").
		WithField("original_tokens", EstimateTokens(prompt)).
		WithField("optimized_tokens", EstimateTokens(optimizedPrompt)).
		WithField("complexity", complexity).
		WithField("selected_model", optimalModel).
		WithField("cost_estimate", costEstimate).
		Info("OpenAI-specific cost optimization completed")
	
	return optimizedPrompt, optimalModel, costEstimate
}

// OptimizeForOpenRouter handles OpenRouter-specific optimization
func OptimizeForOpenRouter(prompt, docType string, complexity TaskComplexity) (string, string, CostEstimate) {
	optimalModel := SelectOptimalModel(complexity, "openrouter")
	optimizedPrompt := CompressPrompt(prompt)
	baseOutputEstimate := EstimateOutputTokens(docType, EstimateTokens(optimizedPrompt))
	costEstimate := EstimateCost("openrouter", optimalModel, optimizedPrompt, baseOutputEstimate)
	
	LogWithContext().WithField("provider", "openrouter").
		WithField("original_tokens", EstimateTokens(prompt)).
		WithField("optimized_tokens", EstimateTokens(optimizedPrompt)).
		WithField("complexity", complexity).
		WithField("selected_model", optimalModel).
		WithField("cost_estimate", costEstimate).
		Info("OpenRouter-specific cost optimization completed")
	
	return optimizedPrompt, optimalModel, costEstimate
}

// CleanupFileContent removes boilerplate and focuses on essential content
func CleanupFileContent(content, filePath string) string {
	// Remove common boilerplate patterns
	cleaned := content
	
	// Remove license headers
	cleaned = regexp.MustCompile(`(?s)^/\*.*?Copyright.*?\*/\s*`).ReplaceAllString(cleaned, "")
	cleaned = regexp.MustCompile(`(?m)^#.*?[Ll]icense.*$`).ReplaceAllString(cleaned, "")
	
	// Remove generated code markers
	cleaned = regexp.MustCompile(`(?m)^.*?[Gg]enerated.*?[Dd]o not edit.*$`).ReplaceAllString(cleaned, "")
	
	// Remove excessive imports (keep first few)
	if strings.Contains(filePath, ".py") {
		lines := strings.Split(cleaned, "\n")
		var result []string
		importCount := 0
		for _, line := range lines {
			if strings.HasPrefix(strings.TrimSpace(line), "import ") || 
			   strings.HasPrefix(strings.TrimSpace(line), "from ") {
				importCount++
				if importCount <= 5 { // Keep first 5 imports
					result = append(result, line)
				} else if importCount == 6 {
					result = append(result, "# ... additional imports truncated ...")
				}
			} else {
				result = append(result, line)
			}
		}
		cleaned = strings.Join(result, "\n")
	}
	
	// Remove debug prints and logs
	cleaned = regexp.MustCompile(`(?m)^.*?(console\.log|print\(|fmt\.Print).*$`).ReplaceAllString(cleaned, "")
	
	// Remove empty lines (but keep structure)
	cleaned = regexp.MustCompile(`\n\s*\n\s*\n+`).ReplaceAllString(cleaned, "\n\n")
	
	return cleaned
}

// RemoveUnicode removes or replaces problematic Unicode characters that increase token cost
func RemoveUnicode(text string) string {
	var result strings.Builder
	
	for _, r := range text {
		if r <= unicode.MaxASCII {
			result.WriteRune(r)
		} else {
			// Replace common Unicode characters with ASCII equivalents
			switch r {
			case '\u2018', '\u2019': // Smart quotes
				result.WriteRune('\'')
			case '\u201C', '\u201D': // Smart double quotes
				result.WriteRune('"')
			case '\u2013', '\u2014': // En dash, em dash
				result.WriteRune('-')
			case '\u2026': // Ellipsis
				result.WriteString("...")
			default:
				// Skip other Unicode characters
				result.WriteRune('?')
			}
		}
	}
	
	return result.String()
}