package main

import (
	"container/list"
	"crypto/sha256"
	"fmt"
	"sync"
	"time"

	"docs-cli/pkg/config"
)

// getCacheConfig returns cache configuration from enterprise config
func getCacheConfig() config.CacheConfig {
	return config.GetConfig().Application.Cache
}

// CacheEntry represents a cached item
type CacheEntry struct {
	Key        string
	Value      string
	Size       int64
	CreatedAt  time.Time
	ExpiresAt  time.Time
	AccessedAt time.Time
	AccessCount int64
}

// CacheMetrics tracks cache performance
type CacheMetrics struct {
	Hits             int64   `json:"hits"`
	Misses           int64   `json:"misses"`
	Evictions        int64   `json:"evictions"`
	TotalSize        int64   `json:"total_size_bytes"`
	EntryCount       int      `json:"entry_count"`
	HitRatio         float64 `json:"hit_ratio"`
	AverageEntrySize int64   `json:"average_entry_size_bytes"`
}

// EnterpriseCache implements an LRU cache with size limits and metrics
type EnterpriseCache struct {
	mutex       sync.RWMutex
	entries     map[string]*list.Element
	lruList     *list.List
	maxSize     int64
	maxEntries  int
	currentSize int64
	ttl         time.Duration
	metrics     CacheMetrics
	stopCleanup chan bool
}

// NewEnterpriseCache creates a new cache with enterprise features
func NewEnterpriseCache(maxSize int64, maxEntries int, ttl time.Duration) *EnterpriseCache {
	cache := &EnterpriseCache{
		entries:     make(map[string]*list.Element),
		lruList:     list.New(),
		maxSize:     maxSize,
		maxEntries:  maxEntries,
		ttl:         ttl,
		stopCleanup: make(chan bool),
	}
	
	// Start cleanup goroutine
	go cache.cleanup()
	
	return cache
}

// Get retrieves an item from cache
func (c *EnterpriseCache) Get(key string) (string, bool) {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	element, exists := c.entries[key]
	if !exists {
		c.metrics.Misses++
		c.updateHitRatio()
		return "", false
	}
	
	entry := element.Value.(*CacheEntry)
	
	// Check if expired
	if time.Now().After(entry.ExpiresAt) {
		c.removeElement(element)
		c.metrics.Misses++
		c.updateHitRatio()
		return "", false
	}
	
	// Update access info and move to front
	entry.AccessedAt = time.Now()
	entry.AccessCount++
	c.lruList.MoveToFront(element)
	
	c.metrics.Hits++
	c.updateHitRatio()
	
	return entry.Value, true
}

// Set stores an item in cache
func (c *EnterpriseCache) Set(key, value string) bool {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	entrySize := int64(len(key) + len(value) + 200) // Approximate overhead
	
	// Check if single entry is too large
	if entrySize > c.maxSize {
		LogWithContext().WithField("entry_size", entrySize).
			WithField("max_size", c.maxSize).
			Warn("Cache entry too large, skipping")
		return false
	}
	
	// Remove existing entry if present
	if element, exists := c.entries[key]; exists {
		c.removeElement(element)
	}
	
	// Make space if needed
	for (c.currentSize+entrySize > c.maxSize || len(c.entries) >= c.maxEntries) && c.lruList.Len() > 0 {
		c.evictLRU()
	}
	
	// Create new entry
	entry := &CacheEntry{
		Key:         key,
		Value:       value,
		Size:        entrySize,
		CreatedAt:   time.Now(),
		ExpiresAt:   time.Now().Add(c.ttl),
		AccessedAt:  time.Now(),
		AccessCount: 1,
	}
	
	// Add to cache
	element := c.lruList.PushFront(entry)
	c.entries[key] = element
	c.currentSize += entrySize
	c.metrics.EntryCount = len(c.entries)
	c.metrics.TotalSize = c.currentSize
	c.updateAverageEntrySize()
	
	return true
}

// evictLRU removes the least recently used item
func (c *EnterpriseCache) evictLRU() {
	element := c.lruList.Back()
	if element != nil {
		c.removeElement(element)
		c.metrics.Evictions++
	}
}

// removeElement removes an element from cache
func (c *EnterpriseCache) removeElement(element *list.Element) {
	if element == nil {
		return
	}
	
	entry := element.Value.(*CacheEntry)
	delete(c.entries, entry.Key)
	c.lruList.Remove(element)
	c.currentSize -= entry.Size
	c.metrics.EntryCount = len(c.entries)
	c.metrics.TotalSize = c.currentSize
	c.updateAverageEntrySize()
}

// cleanup removes expired entries periodically
func (c *EnterpriseCache) cleanup() {
	cacheConfig := getCacheConfig()
	ticker := time.NewTicker(cacheConfig.CleanupInterval)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			c.cleanupExpired()
		case <-c.stopCleanup:
			return
		}
	}
}

// cleanupExpired removes all expired entries
func (c *EnterpriseCache) cleanupExpired() {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	now := time.Now()
	var toRemove []*list.Element
	
	// Collect expired entries
	for element := c.lruList.Back(); element != nil; element = element.Prev() {
		entry := element.Value.(*CacheEntry)
		if now.After(entry.ExpiresAt) {
			toRemove = append(toRemove, element)
		}
	}
	
	// Remove expired entries
	for _, element := range toRemove {
		c.removeElement(element)
	}
	
	if len(toRemove) > 0 {
		LogWithContext().WithField("expired_entries", len(toRemove)).
			Debug("Cleaned up expired cache entries")
	}
}

// updateHitRatio calculates the current hit ratio
func (c *EnterpriseCache) updateHitRatio() {
	total := c.metrics.Hits + c.metrics.Misses
	if total > 0 {
		c.metrics.HitRatio = float64(c.metrics.Hits) / float64(total)
	}
}

// updateAverageEntrySize calculates average entry size
func (c *EnterpriseCache) updateAverageEntrySize() {
	if c.metrics.EntryCount > 0 {
		c.metrics.AverageEntrySize = c.metrics.TotalSize / int64(c.metrics.EntryCount)
	}
}

// GetMetrics returns current cache metrics
func (c *EnterpriseCache) GetMetrics() CacheMetrics {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	return c.metrics
}

// Clear removes all entries from cache
func (c *EnterpriseCache) Clear() {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	c.entries = make(map[string]*list.Element)
	c.lruList = list.New()
	c.currentSize = 0
	c.metrics = CacheMetrics{}
}

// Close stops the cache cleanup goroutine
func (c *EnterpriseCache) Close() {
	close(c.stopCleanup)
}

// Global cache instances
var (
	anthropicCache *EnterpriseCache
	openaiCache    *EnterpriseCache
	defaultCache   *EnterpriseCache
)

func init() {
	cacheConfig := getCacheConfig()
	maxSizeBytes := cacheConfig.MaxSizeMB * 1024 * 1024
	anthropicCache = NewEnterpriseCache(maxSizeBytes, cacheConfig.MaxEntries, cacheConfig.TTL)
	openaiCache = NewEnterpriseCache(maxSizeBytes, cacheConfig.MaxEntries, cacheConfig.TTL)
	defaultCache = NewEnterpriseCache(maxSizeBytes, cacheConfig.MaxEntries, cacheConfig.TTL)
}

// GetProviderCache returns the appropriate cache for a provider
func GetProviderCache(provider string) *EnterpriseCache {
	switch provider {
	case "anthropic":
		return anthropicCache
	case "openai":
		return openaiCache
	default:
		return defaultCache
	}
}

// GenerateCacheKey creates a cache key for API calls
func GenerateCacheKey(provider, prompt, model string, maxTokens int, temperature float64) string {
	// Use shorter hash for cache keys since we have size limits
	input := fmt.Sprintf("%s|%s|%s|%d|%.2f", provider, model, prompt, maxTokens, temperature)
	hash := sha256.Sum256([]byte(input))
	return fmt.Sprintf("%x", hash)[:16] // Use first 16 chars for shorter keys
}

// LogCacheMetrics logs cache performance metrics
func LogCacheMetrics() {
	providers := []string{"anthropic", "openai", "default"}
	
	for _, provider := range providers {
		cache := GetProviderCache(provider)
		metrics := cache.GetMetrics()
		
		LogWithContext().WithField("provider", provider).
			WithField("cache_metrics", metrics).
			Info("Cache performance metrics")
	}
}