package scanner

import (
	"bytes"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"

	gitignore "github.com/sabhiram/go-gitignore"
	"gopkg.in/yaml.v3"

	"docs-cli/pkg/config"
)

// Component represents a scanned component with its files and metadata
type Component struct {
	Path         string   `json:"path"`
	Name         string   `json:"name"`
	Type         string   `json:"type"`
	Description  string   `json:"description"`
	ExistingDocs []string `json:"existing_docs"`
	Files        []string `json:"files"`
}

// ComponentDef represents a component definition from configuration
type ComponentDef struct {
	Name        string `yaml:"name"`
	Path        string `yaml:"path"`
	Type        string `yaml:"type"`
	Description string `yaml:"description"`
}

// ComponentConfig represents the component configuration structure
type ComponentConfig struct {
	Components []ComponentDef `yaml:"components"`
}

// FileScanner interface defines the contract for file scanning operations
type FileScanner interface {
	ScanComponents(projectRoot string) ([]Component, error)
	FindSourceFiles(rootPath string, deepScan bool) ([]string, error)
	LoadComponentConfig() (*ComponentConfig, error)
}

// DefaultFileScanner implements FileScanner with configurable behavior
type DefaultFileScanner struct {
	config       config.ConfigManager
	useGitignore bool
}

// NewFileScanner creates a new file scanner with configuration
func NewFileScanner(configManager config.ConfigManager, useGitignore bool) FileScanner {
	return &DefaultFileScanner{
		config:       configManager,
		useGitignore: useGitignore,
	}
}

// ScanComponents scans all components defined in the configuration
func (fs *DefaultFileScanner) ScanComponents(projectRoot string) ([]Component, error) {
	// Load component configuration
	componentConfig, err := fs.LoadComponentConfig()
	if err != nil {
		return nil, err
	}

	var components []Component

	for _, compDef := range componentConfig.Components {
		fullPath := filepath.Join(projectRoot, compDef.Path)

		// Check if component path exists
		if _, err := os.Stat(fullPath); os.IsNotExist(err) {
			// Log warning but continue - don't fail entire scan
			continue
		}

		// Find existing docs
		existingDocs := fs.findExistingDocs(fullPath)

		// Find all source files
		files, err := fs.FindSourceFiles(fullPath, false)
		if err != nil {
			// Log warning but continue
			continue
		}

		components = append(components, Component{
			Path:         compDef.Path,
			Name:         compDef.Name,
			Type:         compDef.Type,
			Description:  compDef.Description,
			ExistingDocs: existingDocs,
			Files:        files,
		})
	}

	return components, nil
}

// findExistingDocs scans for existing documentation files
func (fs *DefaultFileScanner) findExistingDocs(componentPath string) []string {
	var existingDocs []string

	// Check for README in root
	readmePath := filepath.Join(componentPath, "README.md")
	if _, err := os.Stat(readmePath); err == nil {
		existingDocs = append(existingDocs, "README.md")
	}

	// Check for other docs in docs/ subdirectory
	docsDir := filepath.Join(componentPath, "docs")
	for _, docPattern := range []string{"SETUP.md", "ARCHITECTURE.md", "CHECKLIST.yaml"} {
		docPath := filepath.Join(docsDir, docPattern)
		if _, err := os.Stat(docPath); err == nil {
			existingDocs = append(existingDocs, "docs/"+docPattern)
		}
	}

	return existingDocs
}

// FindSourceFiles scans for source files with configurable depth and filtering
func (fs *DefaultFileScanner) FindSourceFiles(rootPath string, deepScan bool) ([]string, error) {
	var files []string
	fileScanConfig := fs.config.GetFileScanningConfig()
	
	maxDepth := fileScanConfig.MaxDepth
	if deepScan {
		maxDepth = -1 // unlimited
	}

	base := filepath.Clean(rootPath)
	err := filepath.Walk(rootPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Calculate depth
		rel, err := filepath.Rel(base, path)
		if err != nil {
			return err
		}
		depth := 0
		if rel != "." {
			depth = len(strings.Split(rel, string(filepath.Separator)))
		}

		// Apply depth limit
		if maxDepth >= 0 && depth > maxDepth {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		// Skip directories
		if info.IsDir() {
			return nil
		}

		// Skip binary files
		if fs.isBinaryFile(path) {
			return nil
		}

		// Apply gitignore filtering
		if fs.useGitignore && fs.isGitIgnored(path) {
			return nil
		}

		files = append(files, path)
		return nil
	})

	return files, err
}

// isBinaryFile checks if a file is binary using configurable buffer size
func (fs *DefaultFileScanner) isBinaryFile(path string) bool {
	file, err := os.Open(path)
	if err != nil {
		return true
	}
	defer file.Close()

	fileScanConfig := fs.config.GetFileScanningConfig()
	buf := make([]byte, fileScanConfig.BinaryDetectionBuffer)
	n, _ := io.ReadFull(file, buf)
	if n > 0 {
		return bytes.Contains(buf[:n], []byte{0})
	}
	return false
}

// isGitIgnored checks if a file should be ignored based on .gitignore
func (fs *DefaultFileScanner) isGitIgnored(path string) bool {
	dir := filepath.Dir(path)
	gitignorePath := filepath.Join(dir, ".gitignore")

	if _, err := os.Stat(gitignorePath); err != nil {
		return false
	}

	ignorer, err := gitignore.CompileIgnoreFile(gitignorePath)
	if err != nil {
		return false
	}

	relPath, err := filepath.Rel(dir, path)
	if err != nil {
		return false
	}
	return ignorer.MatchesPath(relPath)
}

// LoadComponentConfig loads component configuration from file
func (fs *DefaultFileScanner) LoadComponentConfig() (*ComponentConfig, error) {
	configPath := "components.yaml"
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		return nil, err
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var config ComponentConfig
	err = yaml.Unmarshal(data, &config)
	if err != nil {
		return nil, err
	}
	
	return &config, nil
}

// SortFilesByPriority sorts files by their extension priority
func (fs *DefaultFileScanner) SortFilesByPriority(files []string) []string {
	fileScanConfig := fs.config.GetFileScanningConfig()
	
	sorted := make([]string, len(files))
	copy(sorted, files)
	
	sort.Slice(sorted, func(i, j int) bool {
		extI := strings.ToLower(filepath.Ext(sorted[i]))
		extJ := strings.ToLower(filepath.Ext(sorted[j]))
		priorityI := fileScanConfig.FilePriorities[extI]
		priorityJ := fileScanConfig.FilePriorities[extJ]
		return priorityI > priorityJ
	})
	
	return sorted
}

// LimitFiles limits the number of files based on configuration
func (fs *DefaultFileScanner) LimitFiles(files []string, fullScan bool) []string {
	fileScanConfig := fs.config.GetFileScanningConfig()
	
	if fullScan || len(files) <= fileScanConfig.DefaultFileLimit {
		return files
	}
	
	// Sort by priority first
	sortedFiles := fs.SortFilesByPriority(files)
	
	// Return limited set
	return sortedFiles[:fileScanConfig.DefaultFileLimit]
}