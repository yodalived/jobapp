package main

import (
	"errors"
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"golang.org/x/time/rate"
	"gopkg.in/yaml.v3"
)

// Checklist represents a YAML checklist structure
type Checklist struct {
	ProjectName string     `yaml:"project_name"`
	Categories  []Category `yaml:"categories"`
}

// Category represents a category within a checklist
type Category struct {
	Name  string `yaml:"name"`
	Tasks []Task `yaml:"tasks"`
}

// Task represents an individual task within a category
type Task struct {
	Name         string   `yaml:"name"`
	Status       string   `yaml:"status"`
	Priority     string   `yaml:"priority"`
	Description  string   `yaml:"description"`
	Dependencies []string `yaml:"dependencies,omitempty"`
}

const (
	// Input validation limits
	MaxPromptLength     = 1000000 // 1MB
	MaxFileSize         = 10000000 // 10MB
	MaxFilesPerComponent = 1000
	MaxComponentPathDepth = 10
	
	// Rate limiting - Anthropic
	AnthropicCallsPerMinute = 50 // Conservative limit for Anthropic
	AnthropicBurstLimit    = 5
	
	// Rate limiting - OpenAI (more aggressive limits for cost control)
	OpenAICallsPerMinute = 100  // Conservative for cost control
	OpenAIBurstLimit     = 10   // Lower burst to prevent cost spikes
	
	// Rate limiting - Default/OpenRouter
	DefaultCallsPerMinute = 60
	DefaultBurstLimit     = 10
)

var (
	// Provider-specific rate limiters
	rateLimiters = map[string]*rate.Limiter{
		"anthropic": rate.NewLimiter(rate.Every(time.Minute/AnthropicCallsPerMinute), AnthropicBurstLimit),
		"openai":    rate.NewLimiter(rate.Every(time.Minute/OpenAICallsPerMinute), OpenAIBurstLimit),
		"openrouter": rate.NewLimiter(rate.Every(time.Minute/DefaultCallsPerMinute), DefaultBurstLimit),
		"default":   rate.NewLimiter(rate.Every(time.Minute/DefaultCallsPerMinute), DefaultBurstLimit),
	}
)

// ValidateInput validates user input for security and constraints
func ValidateInput(input string, inputType string) error {
	if input == "" {
		return fmt.Errorf("%s cannot be empty", inputType)
	}
	
	switch inputType {
	case "component_name":
		return validateComponentName(input)
	case "doc_type":
		return validateDocType(input)
	case "file_path":
		return validateFilePath(input)
	case "prompt":
		return validatePrompt(input)
	default:
		return fmt.Errorf("unknown input type: %s", inputType)
	}
}

func validateComponentName(name string) error {
	if len(name) > 100 {
		return errors.New("component name too long (max 100 characters)")
	}
	
	// Only allow alphanumeric, hyphens, and underscores
	for _, r := range name {
		if !((r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || 
			 (r >= '0' && r <= '9') || r == '-' || r == '_') {
			return fmt.Errorf("component name contains invalid character: %c", r)
		}
	}
	
	return nil
}

func validateDocType(docType string) error {
	validTypes := map[string]bool{
		"README":      true,
		"SETUP":       true,
		"ARCHITECTURE": true,
		"CHECKLIST":   true,
		"all":         true,
	}
	
	if !validTypes[docType] {
		return fmt.Errorf("invalid document type: %s", docType)
	}
	
	return nil
}

func validateFilePath(path string) error {
	// Convert to absolute path for validation
	absPath, err := filepath.Abs(path)
	if err != nil {
		return fmt.Errorf("invalid file path: %w", err)
	}
	
	// Check path depth to prevent excessive nesting
	depth := len(strings.Split(strings.TrimPrefix(absPath, "/"), "/"))
	if depth > MaxComponentPathDepth {
		return fmt.Errorf("path too deep (max depth: %d)", MaxComponentPathDepth)
	}
	
	// Prevent directory traversal
	if strings.Contains(path, "..") {
		return errors.New("path traversal not allowed")
	}
	
	// Check for suspicious paths
	suspiciousPaths := []string{"/etc/", "/proc/", "/sys/", "/dev/"}
	for _, suspicious := range suspiciousPaths {
		if strings.HasPrefix(absPath, suspicious) {
			return fmt.Errorf("access to system path not allowed: %s", suspicious)
		}
	}
	
	return nil
}

func validatePrompt(prompt string) error {
	if len(prompt) > MaxPromptLength {
		return fmt.Errorf("prompt too long (max %d characters)", MaxPromptLength)
	}
	
	// Check for potential injection attempts
	suspiciousPatterns := []string{
		"<script>", "javascript:", "eval(", "exec(",
		"system(", "shell_exec(", "passthru(",
	}
	
	lowerPrompt := strings.ToLower(prompt)
	for _, pattern := range suspiciousPatterns {
		if strings.Contains(lowerPrompt, pattern) {
			return fmt.Errorf("prompt contains suspicious pattern: %s", pattern)
		}
	}
	
	return nil
}

// ValidateFileSize checks if a file size is within limits
func ValidateFileSize(size int64) error {
	if size > MaxFileSize {
		return fmt.Errorf("file too large (max %d bytes)", MaxFileSize)
	}
	return nil
}

// CheckRateLimit enforces provider-specific API rate limiting
func CheckRateLimit(provider string) error {
	limiter, exists := rateLimiters[provider]
	if !exists {
		limiter = rateLimiters["default"]
	}
	
	if !limiter.Allow() {
		LogWithContext().WithField("provider", provider).Warn("API rate limit exceeded")
		return fmt.Errorf("rate limit exceeded for provider %s, please wait before making more requests", provider)
	}
	return nil
}

// Enhanced YAML validation with security checks
func validateChecklistYAML(content string) error {
	// Basic size check
	if len(content) > 100000 { // 100KB limit for YAML
		return errors.New("YAML content too large")
	}
	
	var checklist Checklist
	err := yaml.Unmarshal([]byte(content), &checklist)
	if err != nil {
		return fmt.Errorf("invalid YAML format: %w", err)
	}

	// Validate categories
	if len(checklist.Categories) == 0 {
		return errors.New("at least one category is required")
	}
	
	if len(checklist.Categories) > 50 { // Reasonable limit
		return errors.New("too many categories (max 50)")
	}

	for _, category := range checklist.Categories {
		if strings.TrimSpace(category.Name) == "" {
			return errors.New("category name cannot be empty")
		}
		
		if len(category.Name) > 200 {
			return errors.New("category name too long (max 200 characters)")
		}

		// Validate tasks
		if len(category.Tasks) == 0 {
			return fmt.Errorf("category '%s' must have at least one task", category.Name)
		}
		
		if len(category.Tasks) > 100 { // Reasonable limit per category
			return fmt.Errorf("category '%s' has too many tasks (max 100)", category.Name)
		}

		for _, task := range category.Tasks {
			if strings.TrimSpace(task.Name) == "" {
				return errors.New("task name cannot be empty")
			}
			
			if len(task.Name) > 200 {
				return errors.New("task name too long (max 200 characters)")
			}
			
			if strings.TrimSpace(task.Description) == "" {
				return fmt.Errorf("task '%s' description cannot be empty", task.Name)
			}
			
			if len(task.Description) > 1000 {
				return fmt.Errorf("task '%s' description too long (max 1000 characters)", task.Name)
			}

			// Validate status
			validStatus := map[string]bool{
				"completed":   true,
				"in_progress": true,
				"planned":     true,
			}
			if !validStatus[task.Status] {
				return fmt.Errorf("task '%s' has invalid status '%s'", task.Name, task.Status)
			}

			// Validate priority
			validPriority := map[string]bool{
				"high":   true,
				"medium": true,
				"low":    true,
			}
			if !validPriority[task.Priority] {
				return fmt.Errorf("task '%s' has invalid priority '%s'", task.Name, task.Priority)
			}
			
			// Validate dependencies
			if len(task.Dependencies) > 20 {
				return fmt.Errorf("task '%s' has too many dependencies (max 20)", task.Name)
			}
		}
	}

	return nil
}