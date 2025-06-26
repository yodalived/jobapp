package documentation

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"docs-cli/pkg/config"
	"docs-cli/pkg/scanner"
	"docs-cli/pkg/templates"
)

// DocumentationService orchestrates the documentation generation process
type DocumentationService interface {
	GenerateDocumentation(docType, componentName, projectRoot string, force bool) error
}

// DefaultDocumentationService implements DocumentationService
type DefaultDocumentationService struct {
	config           config.ConfigManager
	fileScanner      scanner.FileScanner
	templateProcessor templates.TemplateProcessor
}

// NewDocumentationService creates a new documentation service with default implementations
func NewDocumentationService(configManager config.ConfigManager) DocumentationService {
	return &DefaultDocumentationService{
		config:           configManager,
		fileScanner:      scanner.NewFileScanner(configManager, false),
		templateProcessor: templates.NewTemplateProcessor(configManager),
	}
}

// GenerateDocumentation generates documentation for a specific component and type
func (ds *DefaultDocumentationService) GenerateDocumentation(docType, componentName, projectRoot string, force bool) error {
	// Scan components
	components, err := ds.fileScanner.ScanComponents(projectRoot)
	if err != nil {
		return fmt.Errorf("failed to scan components: %w", err)
	}

	// Handle "all" cases with context chaining
	if docType == "all" {
		if componentName == "all" {
			// Generate for all components
			for _, component := range components {
				if err := ds.generateWithContextChaining(component, projectRoot, force); err != nil {
					fmt.Printf("Error generating docs for %s: %v\n", component.Name, err)
				}
			}
			return nil
		} else {
			// Generate all doc types for specific component with context chaining
			component, found := ds.findComponent(components, componentName)
			if !found {
				return fmt.Errorf("component '%s' not found", componentName)
			}
			return ds.generateWithContextChaining(component, projectRoot, force)
		}
	}

	// Handle single document type cases
	if componentName == "all" {
		for _, component := range components {
			if err := ds.generateSingleDocument(component, docType, projectRoot, force); err != nil {
				fmt.Printf("Error generating %s for %s: %v\n", docType, component.Name, err)
			}
		}
		return nil
	}

	// Generate for specific component and doc type
	component, found := ds.findComponent(components, componentName)
	if !found {
		return fmt.Errorf("component '%s' not found", componentName)
	}

	return ds.generateSingleDocument(component, docType, projectRoot, force)
}

// generateWithContextChaining generates all doc types with context chaining and smart existing file handling
func (ds *DefaultDocumentationService) generateWithContextChaining(component scanner.Component, projectRoot string, force bool) error {
	fmt.Printf("🔗 Starting context-chained generation for %s: ARCHITECTURE → README → SETUP → CHECKLIST\n", component.Name)
	
	docTypes := []string{"ARCHITECTURE", "README", "SETUP", "CHECKLIST"}
	previousDocuments := make(map[string]string)
	
	// Load EXECUTIVE_SUMMARY.md if it exists for initial context
	executiveSummaryPath := filepath.Join(projectRoot, component.Path, "docs", "executive_summary.md")
	if executiveSummary, err := ds.loadExistingDocument(executiveSummaryPath); err == nil {
		previousDocuments["EXECUTIVE_SUMMARY"] = executiveSummary
		fmt.Printf("📋 Loaded executive summary for context guidance\n")
	}
	
	// Pre-load existing README.md for ARCHITECTURE generation context
	readmePath := ds.getOutputPath(component, "README", projectRoot)
	if existingReadme, err := ds.loadExistingDocument(readmePath); err == nil {
		previousDocuments["README"] = existingReadme
		fmt.Printf("📄 Pre-loaded existing README.md for ARCHITECTURE context\n")
	}
	
	for _, docType := range docTypes {
		outputPath := ds.getOutputPath(component, docType, projectRoot)
		
		// Special handling for README - we already loaded it above, just skip generation
		if docType == "README" && len(previousDocuments["README"]) > 0 {
			fmt.Printf("📄 Skipping README (exists) - already loaded into context\n")
			continue
		}
		
		// Check if file exists for other document types
		if existingContent, err := ds.loadExistingDocument(outputPath); err == nil {
			// File exists - load into context but skip generation
			if docType != "README" { // README already handled above
				previousDocuments[docType] = existingContent
			}
			fmt.Printf("📄 Skipping %s (exists) - loaded into context for remaining docs\n", docType)
			continue
		}
		
		// File doesn't exist - generate it with current context
		if err := ds.generateSingleDocumentWithContext(component, docType, projectRoot, previousDocuments, force); err != nil {
			fmt.Printf("❌ Error generating %s for %s: %v\n", docType, component.Name, err)
			continue
		}
		
		// Load the newly generated document into context for next documents
		if newContent, err := ds.loadExistingDocument(outputPath); err == nil {
			previousDocuments[docType] = newContent
			fmt.Printf("📝 Generated %s (added to context chain)\n", docType)
		}
	}
	
	return nil
}

// generateSingleDocument generates a single document for a component
func (ds *DefaultDocumentationService) generateSingleDocument(component scanner.Component, docType, projectRoot string, force bool) error {
	return ds.generateSingleDocumentWithContext(component, docType, projectRoot, make(map[string]string), force)
}

// generateSingleDocumentWithContext generates a single document with conversation context
func (ds *DefaultDocumentationService) generateSingleDocumentWithContext(component scanner.Component, docType, projectRoot string, previousDocuments map[string]string, force bool) error {
	outputPath := ds.getOutputPath(component, docType, projectRoot)
	
	// Check if file exists and force flag
	if !force {
		if _, err := os.Stat(outputPath); err == nil {
			fmt.Printf("File %s already exists. Use --force to overwrite.\n", outputPath)
			return nil
		}
	}

	// Build conversation context from previous documents
	var conversationContext strings.Builder
	if len(previousDocuments) > 0 {
		conversationContext.WriteString("\n=== CONVERSATION CONTEXT ===\n")
		conversationContext.WriteString("Previous documents in this conversation:\n\n")
		
		// Add documents in logical order
		for _, contextDocType := range []string{"EXECUTIVE_SUMMARY", "ARCHITECTURE", "README", "SETUP", "CHECKLIST"} {
			if content, exists := previousDocuments[contextDocType]; exists {
				conversationContext.WriteString(fmt.Sprintf("## %s:\n%s\n\n", contextDocType, content))
			}
		}
		conversationContext.WriteString("=== END CONVERSATION CONTEXT ===\n\n")
	}

	// Create content with context awareness
	content := fmt.Sprintf("# %s Documentation for %s\n\nGenerated by docs-cli with context chaining\nComponent: %s\nType: %s\nPath: %s\n\nConversation Context: %d previous documents\n%s", 
		docType, component.Name, component.Name, component.Type, component.Path, len(previousDocuments), conversationContext.String())

	// Ensure output directory exists
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Write the content to file
	if err := os.WriteFile(outputPath, []byte(content), 0644); err != nil {
		return fmt.Errorf("failed to write documentation: %w", err)
	}

	return nil
}

// loadExistingDocument loads content from an existing document file
func (ds *DefaultDocumentationService) loadExistingDocument(filePath string) (string, error) {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return "", fmt.Errorf("file does not exist: %s", filePath)
	}
	
	content, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read file %s: %w", filePath, err)
	}
	
	return string(content), nil
}

// getOutputPath determines the output path for a document
func (ds *DefaultDocumentationService) getOutputPath(component scanner.Component, docType, projectRoot string) string {
	componentPath := filepath.Join(projectRoot, component.Path)
	
	switch docType {
	case "README":
		return filepath.Join(componentPath, "README.md")
	case "SETUP":
		return filepath.Join(componentPath, "docs", "SETUP.md")
	case "ARCHITECTURE":
		return filepath.Join(componentPath, "docs", "ARCHITECTURE.md")
	case "CHECKLIST":
		return filepath.Join(componentPath, "docs", "CHECKLIST.yaml")
	default:
		return filepath.Join(componentPath, "docs", strings.ToUpper(docType)+".md")
	}
}

// findComponent finds a component by name
func (ds *DefaultDocumentationService) findComponent(components []scanner.Component, name string) (scanner.Component, bool) {
	for _, component := range components {
		if component.Name == name {
			return component, true
		}
	}
	return scanner.Component{}, false
}