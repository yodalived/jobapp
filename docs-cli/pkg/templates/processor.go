package templates

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/template"

	"docs-cli/pkg/config"
	"docs-cli/pkg/scanner"
)

// TemplateProcessor interface defines template processing operations
type TemplateProcessor interface {
	ProcessTemplate(templateType string, component scanner.Component, contextData TemplateContext) (string, error)
	LoadExternalTemplate(templateType string) (string, error)
	GeneratePrompt(component scanner.Component, docType, existingContent string) (string, error)
}

// TemplateContext holds data for template processing
type TemplateContext struct {
	ComponentName        string
	ComponentPath        string
	ComponentType        string
	ComponentDescription string
	ExistingDocs         []string
	SourceContext        string
	ConversationContext  string
	ExistingContent      string
}

// DefaultTemplateProcessor implements TemplateProcessor
type DefaultTemplateProcessor struct {
	config config.ConfigManager
}

// NewTemplateProcessor creates a new template processor
func NewTemplateProcessor(configManager config.ConfigManager) TemplateProcessor {
	return &DefaultTemplateProcessor{
		config: configManager,
	}
}

// ProcessTemplate processes a template with the given context
func (tp *DefaultTemplateProcessor) ProcessTemplate(templateType string, component scanner.Component, contextData TemplateContext) (string, error) {
	templatesConfig := tp.config.GetTemplatesConfig()
	
	// Try to load external template first
	templateContent, err := tp.LoadExternalTemplate(templateType)
	if err != nil {
		// Fall back to configuration-based templates if enabled
		if templatesConfig.FallbackEnabled {
			if fallbackPrompt, exists := templatesConfig.FallbackPrompts[templateType]; exists {
				templateContent = fallbackPrompt
			} else {
				return "", fmt.Errorf("no template found for type %s", templateType)
			}
		} else {
			return "", fmt.Errorf("external template loading failed and fallbacks disabled: %w", err)
		}
	}

	// Process template with context
	tmpl, err := template.New(templateType).Parse(templateContent)
	if err != nil {
		return "", fmt.Errorf("failed to parse template: %w", err)
	}

	var result strings.Builder
	err = tmpl.Execute(&result, contextData)
	if err != nil {
		return "", fmt.Errorf("failed to execute template: %w", err)
	}

	return result.String(), nil
}

// LoadExternalTemplate loads a template from the external templates directory
func (tp *DefaultTemplateProcessor) LoadExternalTemplate(templateType string) (string, error) {
	templatesConfig := tp.config.GetTemplatesConfig()
	templatePath := filepath.Join(templatesConfig.Directory, fmt.Sprintf("%s.prompt.md", templateType))
	
	if _, err := os.Stat(templatePath); os.IsNotExist(err) {
		return "", fmt.Errorf("template file not found: %s", templatePath)
	}

	content, err := os.ReadFile(templatePath)
	if err != nil {
		return "", fmt.Errorf("failed to read template file: %w", err)
	}

	return string(content), nil
}

// GeneratePrompt generates a complete prompt for documentation generation
func (tp *DefaultTemplateProcessor) GeneratePrompt(component scanner.Component, docType, existingContent string) (string, error) {
	// Create template context
	contextData := TemplateContext{
		ComponentName:        component.Name,
		ComponentPath:        component.Path,
		ComponentType:        component.Type,
		ComponentDescription: component.Description,
		ExistingDocs:         component.ExistingDocs,
		ExistingContent:      existingContent,
		// SourceContext and ConversationContext would be populated by caller
	}

	// Process the template
	return tp.ProcessTemplate(docType, component, contextData)
}

// GenerateLegacyPrompt generates a prompt using the legacy format for backward compatibility
func (tp *DefaultTemplateProcessor) GenerateLegacyPrompt(component scanner.Component, docType, existingContent, sourceContext string) string {
	templatesConfig := tp.config.GetTemplatesConfig()

	basePrompt := fmt.Sprintf(`
You are a technical documentation expert. Generate %s documentation for the %s component.

Component Information:
- Path: %s
- Type: %s
- Existing docs: %s

IMPORTANT: If an ARCHITECTURE.md document is included in the context below, use it as guidance to ensure consistency and alignment with the overall system design.

Source Code and Project Context:
%s

`, docType, component.Name, component.Path, component.Type,
		strings.Join(component.ExistingDocs, ", "), sourceContext)

	var specificPrompt string
	
	// Use fallback prompts from configuration if enabled
	if templatesConfig.FallbackEnabled {
		if configPrompt, exists := templatesConfig.FallbackPrompts[docType]; exists {
			specificPrompt = configPrompt
		} else {
			specificPrompt = tp.getDefaultPromptForDocType(docType)
		}
	} else {
		// Configuration disables fallbacks - this should force external template usage
		specificPrompt = "Please create documentation for this component."
	}

	prompt := basePrompt + specificPrompt

	if strings.TrimSpace(existingContent) != "" {
		prompt += fmt.Sprintf("\n\nExisting content to update/enhance:\n%s", existingContent)
	}

	return prompt
}

// getDefaultPromptForDocType returns a minimal default prompt for each document type
func (tp *DefaultTemplateProcessor) getDefaultPromptForDocType(docType string) string {
	switch docType {
	case "README":
		return "Generate a comprehensive README.md with component overview, features, usage, and development notes."
	case "SETUP":
		return "Generate a SETUP.md with installation steps, configuration, and troubleshooting."
	case "ARCHITECTURE":
		return "Generate an ARCHITECTURE.md with system design, component relationships, and technical decisions."
	case "CHECKLIST":
		return "Generate a CHECKLIST.yaml with feature status, tasks, and completion tracking."
	default:
		return "Generate appropriate documentation for this component."
	}
}

// TemplateValidator validates template content and structure
type TemplateValidator struct{}

// ValidateTemplate checks if a template is properly formatted
func (tv *TemplateValidator) ValidateTemplate(templateContent string) error {
	// Check for required template variables
	requiredVars := []string{"{{.ComponentName}}", "{{.ComponentPath}}", "{{.ComponentType}}"}
	
	for _, reqVar := range requiredVars {
		if !strings.Contains(templateContent, reqVar) {
			return fmt.Errorf("template missing required variable: %s", reqVar)
		}
	}
	
	// Try to parse as Go template
	_, err := template.New("validation").Parse(templateContent)
	if err != nil {
		return fmt.Errorf("invalid template syntax: %w", err)
	}
	
	return nil
}

// TemplateCache provides caching for frequently used templates
type TemplateCache struct {
	cache map[string]*template.Template
}

// NewTemplateCache creates a new template cache
func NewTemplateCache() *TemplateCache {
	return &TemplateCache{
		cache: make(map[string]*template.Template),
	}
}

// GetTemplate returns a cached template or loads and caches it
func (tc *TemplateCache) GetTemplate(templateType, templateContent string) (*template.Template, error) {
	if tmpl, exists := tc.cache[templateType]; exists {
		return tmpl, nil
	}
	
	tmpl, err := template.New(templateType).Parse(templateContent)
	if err != nil {
		return nil, err
	}
	
	tc.cache[templateType] = tmpl
	return tmpl, nil
}

// ClearCache clears all cached templates
func (tc *TemplateCache) ClearCache() {
	tc.cache = make(map[string]*template.Template)
}