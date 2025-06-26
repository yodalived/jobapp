package main

import (
	"crypto/md5"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"docs-cli/pkg/config"
	"docs-cli/pkg/scanner"
)

// ComponentSnapshot represents the state of a component at a point in time
type ComponentSnapshot struct {
	ComponentName string            `json:"component_name"`
	Path          string            `json:"path"`
	LastUpdated   time.Time         `json:"last_updated"`
	FileHashes    map[string]string `json:"file_hashes"`
	DocsGenerated map[string]string `json:"docs_generated"` // docType -> hash of generated content
	TotalFiles    int               `json:"total_files"`
	TotalSize     int64             `json:"total_size"`
}

// SnapshotManager manages component snapshots for incremental updates
type SnapshotManager struct {
	snapshotsPath string
	snapshots     map[string]ComponentSnapshot
}

// NewSnapshotManager creates a new snapshot manager
func NewSnapshotManager() *SnapshotManager {
	manager := &SnapshotManager{
		snapshotsPath: filepath.Join(projectRoot, ".docs-cli-snapshots.json"),
		snapshots:     make(map[string]ComponentSnapshot),
	}
	manager.loadSnapshots()
	return manager
}

// loadSnapshots loads existing snapshots from disk
func (sm *SnapshotManager) loadSnapshots() {
	if _, err := os.Stat(sm.snapshotsPath); os.IsNotExist(err) {
		return // No snapshots file yet
	}
	
	data, err := os.ReadFile(sm.snapshotsPath)
	if err != nil {
		LogWithContext().WithError(err).Warn("Failed to load snapshots file")
		return
	}
	
	var snapshots map[string]ComponentSnapshot
	if err := json.Unmarshal(data, &snapshots); err != nil {
		LogWithContext().WithError(err).Warn("Failed to parse snapshots file")
		return
	}
	
	sm.snapshots = snapshots
	LogWithContext().WithField("snapshot_count", len(snapshots)).Info("Loaded component snapshots")
}

// saveSnapshots saves current snapshots to disk
func (sm *SnapshotManager) saveSnapshots() error {
	data, err := json.MarshalIndent(sm.snapshots, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal snapshots: %w", err)
	}
	
	if err := os.WriteFile(sm.snapshotsPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write snapshots file: %w", err)
	}
	
	return nil
}

// CreateSnapshot creates a snapshot of the current component state
func (sm *SnapshotManager) CreateSnapshot(component scanner.Component) ComponentSnapshot {
	snapshot := ComponentSnapshot{
		ComponentName: component.Name,
		Path:          component.Path,
		LastUpdated:   time.Now(),
		FileHashes:    make(map[string]string),
		DocsGenerated: make(map[string]string),
		TotalFiles:    len(component.Files),
	}
	
	// Calculate file hashes
	var totalSize int64
	for _, filePath := range component.Files {
		fullPath := filepath.Join(projectRoot, filePath)
		if content, err := MemoryAwareFileReader(fullPath); err == nil {
			hash := fmt.Sprintf("%x", md5.Sum(content))
			snapshot.FileHashes[filePath] = hash
			totalSize += int64(len(content))
		} else {
			LogWithContext().WithError(err).WithField("file", filePath).Warn("Failed to hash file")
		}
	}
	
	snapshot.TotalSize = totalSize
	return snapshot
}

// HasComponentChanged checks if a component has changed since the last snapshot
func (sm *SnapshotManager) HasComponentChanged(component scanner.Component) (bool, []string) {
	lastSnapshot, exists := sm.snapshots[component.Name]
	if !exists {
		return true, []string{"component never documented"}
	}
	
	currentSnapshot := sm.CreateSnapshot(component)
	
	var changes []string
	
	// Check if files were added or removed
	if currentSnapshot.TotalFiles != lastSnapshot.TotalFiles {
		changes = append(changes, fmt.Sprintf("file count changed (%d -> %d)", 
			lastSnapshot.TotalFiles, currentSnapshot.TotalFiles))
	}
	
	// Check for new or modified files
	for filePath, currentHash := range currentSnapshot.FileHashes {
		if lastHash, exists := lastSnapshot.FileHashes[filePath]; !exists {
			changes = append(changes, fmt.Sprintf("new file: %s", filePath))
		} else if currentHash != lastHash {
			changes = append(changes, fmt.Sprintf("modified file: %s", filePath))
		}
	}
	
	// Check for deleted files
	for filePath := range lastSnapshot.FileHashes {
		if _, exists := currentSnapshot.FileHashes[filePath]; !exists {
			changes = append(changes, fmt.Sprintf("deleted file: %s", filePath))
		}
	}
	
	return len(changes) > 0, changes
}

// ShouldRegenerateDoc determines if a specific document type should be regenerated
func (sm *SnapshotManager) ShouldRegenerateDoc(component scanner.Component, docType string) (bool, string) {
	changed, changes := sm.HasComponentChanged(component)
	if changed {
		return true, fmt.Sprintf("component changed: %s", strings.Join(changes, ", "))
	}
	
	// Check if this document type was never generated
	lastSnapshot, exists := sm.snapshots[component.Name]
	if !exists {
		return true, "no previous snapshot"
	}
	
	if _, docExists := lastSnapshot.DocsGenerated[docType]; !docExists {
		return true, "document type never generated"
	}
	
	// Check if the existing documentation file is missing
	var docPath string
	if docType == "README" {
		docPath = filepath.Join(projectRoot, component.Path, "README.md")
	} else if docType == "CHECKLIST" {
		docPath = filepath.Join(projectRoot, component.Path, "docs", "CHECKLIST.yaml")
	} else {
		docPath = filepath.Join(projectRoot, component.Path, "docs", docType+".md")
	}
	
	if _, err := os.Stat(docPath); os.IsNotExist(err) {
		return true, "documentation file missing"
	}
	
	return false, "no changes detected"
}

// UpdateSnapshot updates the snapshot after successful documentation generation
func (sm *SnapshotManager) UpdateSnapshot(component scanner.Component, docType, generatedContent string) {
	snapshot := sm.CreateSnapshot(component)
	
	// Store hash of generated content
	contentHash := fmt.Sprintf("%x", md5.Sum([]byte(generatedContent)))
	snapshot.DocsGenerated[docType] = contentHash
	
	// Merge with existing docs generated
	if existingSnapshot, exists := sm.snapshots[component.Name]; exists {
		for existingDocType, existingHash := range existingSnapshot.DocsGenerated {
			if existingDocType != docType {
				snapshot.DocsGenerated[existingDocType] = existingHash
			}
		}
	}
	
	sm.snapshots[component.Name] = snapshot
	
	if err := sm.saveSnapshots(); err != nil {
		LogWithContext().WithError(err).Warn("Failed to save updated snapshots")
	} else {
		LogWithContext().WithField("component", component.Name).
			WithField("doc_type", docType).
			Debug("Updated component snapshot")
	}
}

// GetChangesSummary returns a summary of changes across all components
func (sm *SnapshotManager) GetChangesSummary(components []scanner.Component) map[string][]string {
	summary := make(map[string][]string)
	
	for _, component := range components {
		changed, changes := sm.HasComponentChanged(component)
		if changed {
			summary[component.Name] = changes
		}
	}
	
	return summary
}

// GetCostSavingsEstimate estimates cost savings from incremental updates
func (sm *SnapshotManager) GetCostSavingsEstimate(components []scanner.Component, docTypes []string) CostSavingsReport {
	report := CostSavingsReport{
		TotalComponents:     len(components),
		TotalDocuments:      len(components) * len(docTypes),
		ComponentsChanged:   0,
		DocumentsToRegenerate: 0,
		EstimatedTokensSaved: 0,
		EstimatedCostSaved:   0.0,
	}
	
	for _, component := range components {
		changed, _ := sm.HasComponentChanged(component)
		if changed {
			report.ComponentsChanged++
			report.DocumentsToRegenerate += len(docTypes)
		} else {
			// For unchanged components, check individual docs
			for _, docType := range docTypes {
				shouldRegen, _ := sm.ShouldRegenerateDoc(component, docType)
				if shouldRegen {
					report.DocumentsToRegenerate++
				}
			}
		}
	}
	
	report.DocumentsSkipped = report.TotalDocuments - report.DocumentsToRegenerate
	
	// Estimate tokens saved (rough approximation)
	avgTokensPerDoc := 5000 // Conservative estimate
	report.EstimatedTokensSaved = report.DocumentsSkipped * avgTokensPerDoc
	
	// Estimate cost saved (using default pricing)
	costConfig := config.GetConfig().CostOpt
	defaultCost := 0.015 // fallback cost per 1K tokens
	if pricing, exists := costConfig.Pricing.Anthropic["sonnet4"]; exists {
		defaultCost = pricing.InputCost
	}
	report.EstimatedCostSaved = float64(report.EstimatedTokensSaved) / 1000.0 * defaultCost
	
	return report
}

// CostSavingsReport summarizes potential cost savings from incremental updates
type CostSavingsReport struct {
	TotalComponents       int     `json:"total_components"`
	ComponentsChanged     int     `json:"components_changed"`
	TotalDocuments        int     `json:"total_documents"`
	DocumentsToRegenerate int     `json:"documents_to_regenerate"`
	DocumentsSkipped      int     `json:"documents_skipped"`
	EstimatedTokensSaved  int     `json:"estimated_tokens_saved"`
	EstimatedCostSaved    float64 `json:"estimated_cost_saved"`
}

// ForceRefresh clears all snapshots to force full regeneration
func (sm *SnapshotManager) ForceRefresh() error {
	sm.snapshots = make(map[string]ComponentSnapshot)
	return sm.saveSnapshots()
}

// CleanupStaleSnapshots removes snapshots for components that no longer exist
func (sm *SnapshotManager) CleanupStaleSnapshots(activeComponents []scanner.Component) {
	activeNames := make(map[string]bool)
	for _, comp := range activeComponents {
		activeNames[comp.Name] = true
	}
	
	var removedCount int
	for name := range sm.snapshots {
		if !activeNames[name] {
			delete(sm.snapshots, name)
			removedCount++
		}
	}
	
	if removedCount > 0 {
		LogWithContext().WithField("removed_count", removedCount).Info("Cleaned up stale snapshots")
		sm.saveSnapshots()
	}
}