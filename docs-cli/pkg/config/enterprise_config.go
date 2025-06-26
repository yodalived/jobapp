package config

import (
	"fmt"
	"os"
	"time"

	"gopkg.in/yaml.v3"
)

// EnterpriseConfig holds all enterprise configuration
type EnterpriseConfig struct {
	Application ApplicationConfig `yaml:"application"`
	Providers   ProvidersConfig   `yaml:"providers"`
	CostOpt     CostOptConfig     `yaml:"cost_optimization"`
	Templates   TemplatesConfig   `yaml:"templates"`
}

// ApplicationConfig holds application-level settings
type ApplicationConfig struct {
	Cache       CacheConfig       `yaml:"cache"`
	Monitoring  MonitoringConfig  `yaml:"monitoring"`
	Resilience  ResilienceConfig  `yaml:"resilience"`
	FileScanning FileScanningConfig `yaml:"file_scanning"`
}

// CacheConfig holds cache settings
type CacheConfig struct {
	TTL                time.Duration `yaml:"ttl"`
	MaxSizeMB          int64         `yaml:"max_size_mb"`
	MaxEntries         int           `yaml:"max_entries"`
	CleanupInterval    time.Duration `yaml:"cleanup_interval"`
	MetricsLogInterval time.Duration `yaml:"metrics_log_interval"`
}

// MonitoringConfig holds monitoring settings
type MonitoringConfig struct {
	MemoryWarningMB  uint64        `yaml:"memory_warning_mb"`
	MemoryCriticalMB uint64        `yaml:"memory_critical_mb"`
	CheckInterval    time.Duration `yaml:"check_interval"`
	GCInterval       time.Duration `yaml:"gc_interval"`
}

// ResilienceConfig holds resilience settings
type ResilienceConfig struct {
	Retry          RetryConfig          `yaml:"retry"`
	CircuitBreaker CircuitBreakerConfig `yaml:"circuit_breaker"`
}

// RetryConfig holds retry settings
type RetryConfig struct {
	MaxAttempts        int           `yaml:"max_attempts"`
	InitialDelay       time.Duration `yaml:"initial_delay"`
	MaxDelay           time.Duration `yaml:"max_delay"`
	BackoffMultiplier  float64       `yaml:"backoff_multiplier"`
}

// CircuitBreakerConfig holds circuit breaker settings
type CircuitBreakerConfig struct {
	MaxRequests      uint32        `yaml:"max_requests"`
	Interval         time.Duration `yaml:"interval"`
	Timeout          time.Duration `yaml:"timeout"`
	FailureThreshold uint32        `yaml:"failure_threshold"`
}

// FileScanningConfig holds file scanning settings
type FileScanningConfig struct {
	MaxDepth              int            `yaml:"max_depth"`
	BinaryDetectionBuffer int            `yaml:"binary_detection_buffer"`
	DefaultFileLimit      int            `yaml:"default_file_limit"`
	FilePriorities        map[string]int `yaml:"file_priorities"`
}

// ProvidersConfig holds all provider configurations
type ProvidersConfig struct {
	Anthropic  ProviderConfig `yaml:"anthropic"`
	OpenAI     ProviderConfig `yaml:"openai"`
	OpenRouter ProviderConfig `yaml:"openrouter"`
}

// ProviderConfig holds individual provider configuration
type ProviderConfig struct {
	APIURL           string            `yaml:"api_url"`
	Timeout          time.Duration     `yaml:"timeout"`
	APIVersion       string            `yaml:"api_version,omitempty"`
	TemperatureRange TemperatureRange  `yaml:"temperature_range"`
	StopSequences    []string          `yaml:"stop_sequences,omitempty"`
	Metadata         map[string]string `yaml:"metadata,omitempty"`
	Headers          map[string]string `yaml:"headers,omitempty"`
}

// TemperatureRange holds temperature validation ranges
type TemperatureRange struct {
	Min float64 `yaml:"min"`
	Max float64 `yaml:"max"`
}

// CostOptConfig holds cost optimization settings
type CostOptConfig struct {
	TokenEstimationRatio  float64               `yaml:"token_estimation_ratio"`
	Compression           CompressionConfig     `yaml:"compression"`
	ComplexityThresholds  ComplexityConfig      `yaml:"complexity_thresholds"`
	Pricing               PricingConfig         `yaml:"pricing"`
}

// CompressionConfig holds compression settings
type CompressionConfig struct {
	MaxRatio float64 `yaml:"max_ratio"`
}

// ComplexityConfig holds task complexity thresholds
type ComplexityConfig struct {
	Simple  int `yaml:"simple"`
	Complex int `yaml:"complex"`
}

// PricingConfig holds pricing information for different providers
type PricingConfig struct {
	Anthropic map[string]ModelPricing `yaml:"anthropic"`
	OpenAI    map[string]ModelPricing `yaml:"openai"`
}

// ModelPricing holds pricing for input/output tokens
type ModelPricing struct {
	InputCost  float64 `yaml:"input_cost"`
	OutputCost float64 `yaml:"output_cost"`
}

// TemplatesConfig holds template system configuration
type TemplatesConfig struct {
	FallbackEnabled bool                       `yaml:"fallback_enabled"`
	Directory       string                     `yaml:"directory"`
	FallbackPrompts map[string]string          `yaml:"fallback_prompts"`
}

var globalConfig *EnterpriseConfig

// LoadEnterpriseConfig loads the enterprise configuration from file
func LoadEnterpriseConfig() (*EnterpriseConfig, error) {
	if globalConfig != nil {
		return globalConfig, nil
	}

	configPath := "enterprise-config.yaml"
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		return nil, fmt.Errorf("enterprise-config.yaml not found")
	}

	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("error reading enterprise-config.yaml: %w", err)
	}

	var config EnterpriseConfig
	err = yaml.Unmarshal(data, &config)
	if err != nil {
		return nil, fmt.Errorf("error parsing enterprise-config.yaml: %w", err)
	}

	globalConfig = &config
	return globalConfig, nil
}

// GetConfig returns the loaded enterprise configuration
func GetConfig() *EnterpriseConfig {
	if globalConfig == nil {
		// Try to load config if not already loaded
		config, err := LoadEnterpriseConfig()
		if err != nil {
			// Return default config if loading fails
			return getDefaultConfig()
		}
		return config
	}
	return globalConfig
}

// getDefaultConfig returns a default configuration for fallback
func getDefaultConfig() *EnterpriseConfig {
	return &EnterpriseConfig{
		Application: ApplicationConfig{
			Cache: CacheConfig{
				TTL:                2 * time.Minute,
				MaxSizeMB:          50,
				MaxEntries:         1000,
				CleanupInterval:    1 * time.Minute,
				MetricsLogInterval: 10 * time.Minute,
			},
			Monitoring: MonitoringConfig{
				MemoryWarningMB:  500,
				MemoryCriticalMB: 1000,
				CheckInterval:    30 * time.Second,
				GCInterval:       2 * time.Minute,
			},
			Resilience: ResilienceConfig{
				Retry: RetryConfig{
					MaxAttempts:       3,
					InitialDelay:      1 * time.Second,
					MaxDelay:          30 * time.Second,
					BackoffMultiplier: 2.0,
				},
				CircuitBreaker: CircuitBreakerConfig{
					MaxRequests:      3,
					Interval:         60 * time.Second,
					Timeout:          30 * time.Second,
					FailureThreshold: 5,
				},
			},
			FileScanning: FileScanningConfig{
				MaxDepth:              3,
				BinaryDetectionBuffer: 512,
				DefaultFileLimit:      10,
				FilePriorities: map[string]int{
					".go": 10, ".py": 9, ".ts": 8, ".tsx": 7, ".js": 6,
					".jsx": 5, ".tex": 4, ".yaml": 3, ".yml": 2, ".json": 1, ".md": 0,
				},
			},
		},
		Providers: ProvidersConfig{
			Anthropic: ProviderConfig{
				APIURL:     "https://api.anthropic.com/v1/messages",
				Timeout:    30 * time.Second,
				APIVersion: "2023-06-01",
				TemperatureRange: TemperatureRange{Min: 0.0, Max: 1.0},
				StopSequences:    []string{"\n\nHuman:"},
			},
			OpenAI: ProviderConfig{
				APIURL:           "https://api.openai.com/v1/chat/completions",
				Timeout:          60 * time.Second,
				TemperatureRange: TemperatureRange{Min: 0.0, Max: 2.0},
			},
			OpenRouter: ProviderConfig{
				APIURL:           "https://openrouter.ai/api/v1/chat/completions",
				Timeout:          90 * time.Second,
				TemperatureRange: TemperatureRange{Min: 0.0, Max: 2.0},
			},
		},
		CostOpt: CostOptConfig{
			TokenEstimationRatio: 0.25,
			Compression: CompressionConfig{
				MaxRatio: 0.3,
			},
			ComplexityThresholds: ComplexityConfig{
				Simple:  2000,
				Complex: 10000,
			},
		},
		Templates: TemplatesConfig{
			FallbackEnabled: false,
			Directory:       "templates",
		},
	}
}

// ConfigManager interface for dependency injection
type ConfigManager interface {
	LoadConfig() (*EnterpriseConfig, error)
	GetConfig() *EnterpriseConfig
	GetProviderConfig(provider string) ProviderConfig
	GetCacheConfig() CacheConfig
	GetMonitoringConfig() MonitoringConfig
	GetResilienceConfig() ResilienceConfig
	GetFileScanningConfig() FileScanningConfig
	GetCostOptConfig() CostOptConfig
	GetTemplatesConfig() TemplatesConfig
}

// DefaultConfigManager implements ConfigManager
type DefaultConfigManager struct{}

// NewConfigManager creates a new configuration manager
func NewConfigManager() ConfigManager {
	return &DefaultConfigManager{}
}

func (cm *DefaultConfigManager) LoadConfig() (*EnterpriseConfig, error) {
	return LoadEnterpriseConfig()
}

func (cm *DefaultConfigManager) GetConfig() *EnterpriseConfig {
	return GetConfig()
}

func (cm *DefaultConfigManager) GetProviderConfig(provider string) ProviderConfig {
	config := GetConfig()
	switch provider {
	case "anthropic":
		return config.Providers.Anthropic
	case "openai":
		return config.Providers.OpenAI
	case "openrouter":
		return config.Providers.OpenRouter
	default:
		return ProviderConfig{}
	}
}

func (cm *DefaultConfigManager) GetCacheConfig() CacheConfig {
	return GetConfig().Application.Cache
}

func (cm *DefaultConfigManager) GetMonitoringConfig() MonitoringConfig {
	return GetConfig().Application.Monitoring
}

func (cm *DefaultConfigManager) GetResilienceConfig() ResilienceConfig {
	return GetConfig().Application.Resilience
}

func (cm *DefaultConfigManager) GetFileScanningConfig() FileScanningConfig {
	return GetConfig().Application.FileScanning
}

func (cm *DefaultConfigManager) GetCostOptConfig() CostOptConfig {
	return GetConfig().CostOpt
}

func (cm *DefaultConfigManager) GetTemplatesConfig() TemplatesConfig {
	return GetConfig().Templates
}