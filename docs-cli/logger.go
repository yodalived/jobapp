package main

import (
	"os"
	"runtime"
	"time"

	"github.com/sirupsen/logrus"
)

var logger *logrus.Logger

func init() {
	logger = logrus.New()
	
	// Set output to stdout for containerized environments
	logger.SetOutput(os.Stdout)
	
	// JSON formatter for structured logging
	logger.SetFormatter(&logrus.JSONFormatter{
		TimestampFormat: time.RFC3339,
		FieldMap: logrus.FieldMap{
			logrus.FieldKeyTime:  "timestamp",
			logrus.FieldKeyLevel: "level",
			logrus.FieldKeyMsg:   "message",
		},
	})
	
	// Set log level from environment or default to Info
	level := os.Getenv("LOG_LEVEL")
	switch level {
	case "debug":
		logger.SetLevel(logrus.DebugLevel)
	case "warn":
		logger.SetLevel(logrus.WarnLevel)
	case "error":
		logger.SetLevel(logrus.ErrorLevel)
	default:
		logger.SetLevel(logrus.InfoLevel)
	}
	
	// Add caller information for better debugging
	logger.SetReportCaller(true)
}

// LogWithContext creates a logger with common context fields
func LogWithContext() *logrus.Entry {
	return logger.WithFields(logrus.Fields{
		"service":   "docs-cli",
		"version":   "1.0.0",
		"go_version": runtime.Version(),
	})
}

// LogAPICall logs API call details
func LogAPICall(provider, model string, tokensUsed int, duration time.Duration, err error) {
	entry := LogWithContext().WithFields(logrus.Fields{
		"operation":    "api_call",
		"provider":     provider,
		"model":        model,
		"tokens_used":  tokensUsed,
		"duration_ms":  duration.Milliseconds(),
	})
	
	if err != nil {
		entry.WithError(err).Error("API call failed")
	} else {
		entry.Info("API call completed successfully")
	}
}

// LogFileOperation logs file operations
func LogFileOperation(operation, path string, size int64, err error) {
	entry := LogWithContext().WithFields(logrus.Fields{
		"operation": "file_" + operation,
		"path":      path,
		"size_bytes": size,
	})
	
	if err != nil {
		entry.WithError(err).Error("File operation failed")
	} else {
		entry.Info("File operation completed")
	}
}

// LogComponentScan logs component scanning results
func LogComponentScan(componentName, path string, fileCount int, err error) {
	entry := LogWithContext().WithFields(logrus.Fields{
		"operation":      "component_scan",
		"component":      componentName,
		"path":          path,
		"files_found":   fileCount,
	})
	
	if err != nil {
		entry.WithError(err).Error("Component scan failed")
	} else {
		entry.Info("Component scan completed")
	}
}

// LogMemoryUsage logs current memory usage
func LogMemoryUsage() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	
	LogWithContext().WithFields(logrus.Fields{
		"operation":     "memory_usage",
		"alloc_mb":      m.Alloc / 1024 / 1024,
		"total_alloc_mb": m.TotalAlloc / 1024 / 1024,
		"sys_mb":        m.Sys / 1024 / 1024,
		"gc_cycles":     m.NumGC,
	}).Info("Memory usage report")
}