package main

import (
	"fmt"
	"os"
	"runtime"
	"time"

	"docs-cli/pkg/config"
)

// getMonitoringConfig returns monitoring configuration from enterprise config
func getMonitoringConfig() config.MonitoringConfig {
	return config.GetConfig().Application.Monitoring
}

type MemoryStats struct {
	AllocMB       uint64 `json:"alloc_mb"`
	TotalAllocMB  uint64 `json:"total_alloc_mb"`
	SysMB         uint64 `json:"sys_mb"`
	NumGC         uint32 `json:"num_gc"`
	GCCPUFraction float64 `json:"gc_cpu_fraction"`
	HeapObjects   uint64 `json:"heap_objects"`
	StackInUseMB  uint64 `json:"stack_inuse_mb"`
}

// GetMemoryStats returns current memory statistics
func GetMemoryStats() MemoryStats {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	
	return MemoryStats{
		AllocMB:       m.Alloc / 1024 / 1024,
		TotalAllocMB:  m.TotalAlloc / 1024 / 1024,
		SysMB:         m.Sys / 1024 / 1024,
		NumGC:         m.NumGC,
		GCCPUFraction: m.GCCPUFraction,
		HeapObjects:   m.HeapObjects,
		StackInUseMB:  m.StackInuse / 1024 / 1024,
	}
}

// CheckMemoryUsage logs memory usage and triggers GC if needed
func CheckMemoryUsage() {
	stats := GetMemoryStats()
	
	entry := LogWithContext().WithField("memory_stats", stats)
	
	monitoringConfig := getMonitoringConfig()
	
	if stats.AllocMB >= monitoringConfig.MemoryCriticalMB {
		entry.Error("Critical memory usage detected")
		runtime.GC() // Force garbage collection
		runtime.GC() // Run twice for better cleanup
		
		// Log stats after GC
		newStats := GetMemoryStats()
		LogWithContext().WithField("memory_stats_after_gc", newStats).
			Info("Memory usage after forced GC")
		
	} else if stats.AllocMB >= monitoringConfig.MemoryWarningMB {
		entry.Warn("High memory usage detected")
	} else {
		entry.Debug("Memory usage normal")
	}
}

// StartMemoryMonitor starts a background goroutine to monitor memory usage
func StartMemoryMonitor() {
	go func() {
		monitoringConfig := getMonitoringConfig()
		memoryTicker := time.NewTicker(monitoringConfig.CheckInterval)
		gcTicker := time.NewTicker(monitoringConfig.GCInterval)
		defer memoryTicker.Stop()
		defer gcTicker.Stop()
		
		for {
			select {
			case <-memoryTicker.C:
				CheckMemoryUsage()
				
			case <-gcTicker.C:
				// Periodic garbage collection
				LogWithContext().Debug("Running periodic garbage collection")
				runtime.GC()
			}
		}
	}()
}

// LimitMemoryUsage enforces memory limits for operations
func LimitMemoryUsage(operation string) error {
	stats := GetMemoryStats()
	monitoringConfig := getMonitoringConfig()
	
	if stats.AllocMB >= monitoringConfig.MemoryCriticalMB {
		LogWithContext().WithField("operation", operation).
			WithField("memory_mb", stats.AllocMB).
			Error("Operation blocked due to high memory usage")
		
		return ErrMemoryLimitExceeded
	}
	
	return nil
}

// Custom errors
var (
	ErrMemoryLimitExceeded = fmt.Errorf("memory usage exceeds critical threshold")
)

// MemoryAwareFileReader reads files with memory monitoring
func MemoryAwareFileReader(filePath string) ([]byte, error) {
	// Check memory before reading
	if err := LimitMemoryUsage("file_read"); err != nil {
		return nil, err
	}
	
	// Get file size first
	info, err := os.Stat(filePath)
	if err != nil {
		return nil, err
	}
	
	// Validate file size
	if err := ValidateFileSize(info.Size()); err != nil {
		return nil, err
	}
	
	// Log the operation
	start := time.Now()
	content, err := os.ReadFile(filePath)
	duration := time.Since(start)
	
	LogFileOperation("read", filePath, info.Size(), err)
	
	if err == nil {
		LogWithContext().WithField("file_path", filePath).
			WithField("size_bytes", len(content)).
			WithField("duration_ms", duration.Milliseconds()).
			Debug("File read completed")
	}
	
	return content, err
}