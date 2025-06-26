# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Documentation CLI Tool - A Go CLI tool for automated documentation generation using the Claude API with full source code context. Configuration-based documentation generation that supports multiple LLM providers and template-based prompts.

## Current Status
- ✅ **Core Infrastructure**: Complete with enterprise-grade features
- ✅ **Multi-Provider Support**: Anthropic Claude, OpenAI GPT, OpenRouter integration
- ✅ **Cost Optimization**: Intelligent prompt compression and model selection
- ✅ **Enterprise Features**: Structured logging, caching, rate limiting, input validation
- ✅ **Resilience**: Circuit breaker patterns, retry logic, memory monitoring
- ✅ **Provider Optimization**: All providers (Anthropic, OpenAI, OpenRouter) fully optimized
- ✅ **Context Chaining**: Conversation continuity within components, fresh conversations between components
- ✅ **Deep Thinking**: Support for reasoning models (DeepSeek-R1, o1, o3, Claude Opus 4)

## Architecture
This is a Go CLI application built with Cobra for command handling and supports multiple AI providers:
- **Configuration-based discovery**: Uses `components.yaml` to define which components to document
- **Multi-provider support**: Anthropic, OpenAI, and OpenRouter models
- **Template system**: Customizable prompt templates for different document types
- **Full source context**: Includes ALL source files from components (no limits)
- **Status page generation**: Consolidates CHECKLIST.yaml files into status.json

## Development Commands

### Environment Setup
```bash
# Install dependencies
go mod tidy

# Build the CLI tool
go build -o docs-cli .

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Tool
```bash
# List available components
./docs-cli list

# Create specific documentation
./docs-cli create README api
./docs-cli create all core
./docs-cli create README all

# Enable deep thinking for supported models
./docs-cli create all api --think
./docs-cli create README core --think --force

# Update all documentation
./docs-cli update

# Generate status page
./docs-cli status

# Force overwrite existing files
./docs-cli create README api --force
./docs-cli create all core -f
```

### Development Commands
```bash
# Run with full source context (no file limits)
./docs-cli create README api --full

# Honor .gitignore files
./docs-cli create README api --gitignore

# Deep recursion without depth limits
./docs-cli create README api --deep
```

## Configuration Files

### Required Files
- **components.yaml**: Defines which components to document and file patterns
- **model-config.yaml**: Configures AI providers and models for different document types
- **.env**: API keys and environment settings

### Template System
- **templates/README.prompt.md**: README generation prompt template
- **templates/SETUP.prompt.md**: Setup guide prompt template
- **templates/ARCHITECTURE.prompt.md**: Architecture documentation prompt
- **templates/CHECKLIST.prompt.md**: Checklist generation prompt

Templates support variable substitution:
- `{{.ComponentName}}` - Component name
- `{{.ComponentPath}}` - Component path
- `{{.ComponentType}}` - Component type
- `{{.SourceContext}}` - Full source code context
- `{{.ExistingContent}}` - Existing content for updates

## Key Features
- **Multi-provider AI support**: Anthropic Claude, OpenAI GPT, OpenRouter
- **Document type specialization**: Different models for README, SETUP, ARCHITECTURE, CHECKLIST
- **Template-based prompts**: Easy customization without code changes
- **Project context inclusion**: Automatically includes README.md, CLAUDE.md, PROJECT_STATUS.md
- **Dynamic context directory**: Includes all .md files from docs/context/
- **Status page aggregation**: Consolidates component checklists into unified status
- **Context Chaining**: Conversation continuity within components for improved document coherence

## File Structure
```
docs-cli/
├── main.go                     # Main CLI logic and commands
├── model_config.go             # Model configuration management
├── model_provider.go           # Provider factory and interface
├── anthropic_provider.go       # Anthropic Claude provider
├── openai_provider.go          # OpenAI GPT provider
├── openrouter_provider.go      # OpenRouter provider
├── anthropic_optimization.go   # Anthropic-specific cost optimization
├── openai_optimization.go      # OpenAI-specific cost optimization
├── openrouter_optimization.go  # OpenRouter-specific cost optimization
├── cost_optimization.go        # Core cost optimization logic
├── cache.go                    # Enterprise caching system
├── validation.go               # Input validation and rate limiting
├── resilience.go               # Circuit breaker and retry logic
├── monitoring.go               # Memory monitoring and GC
├── logger.go                   # Structured logging
├── components.yaml             # Component definitions
├── model-config.yaml           # AI model configuration
└── templates/                  # Prompt templates
    ├── README.prompt.md
    ├── SETUP.prompt.md
    ├── ARCHITECTURE.prompt.md
    └── CHECKLIST.prompt.md
```

## Development Notes
- The tool scans components based on `components.yaml` configuration rather than dynamic discovery
- Full source context is provided to AI models with no truncation by default
- Uses file priority system for intelligent file selection when limits are needed
- Supports both single and batch documentation generation
- Project documentation context is automatically included for better consistency
- CHECKLIST.yaml files are aggregated into a consolidated status.json file

## API Keys and Security
- Store API keys in `.env` file (not committed)
- Multiple provider support allows fallback options
- Model selection can be customized per document type
- Temperature and token limits are configurable per provider

## Provider-Specific Optimizations

### OpenRouter Optimization Features
- **Adaptive Compression**: Three-tier compression strategy based on prompt size
  - Conservative: Minimal compression for prompts < 50k tokens
  - Moderate: Balanced compression for prompts 50k-100k tokens  
  - Aggressive: Maximum compression for prompts > 100k tokens
- **Model Aggregation**: Leverages OpenRouter's model routing capabilities
- **Cost Tracking**: Real-time cost calculation from OpenRouter usage data
- **Extended Timeout**: 90-second timeout for OpenRouter's routing delays
- **Error Handling**: Specific handling for 402 (insufficient credits) and 503 (model unavailable) errors

### Anthropic Optimization Features
- **Aggressive Compression**: 50-70% prompt size reduction with context-aware truncation
- **Smart Model Selection**: Haiku→Sonnet→Opus based on complexity
- **Section Prioritization**: Preserves important sections during truncation
- **Enterprise Caching**: LRU cache with size limits and metrics

### OpenAI Optimization Features
- **Moderate Compression**: 30-40% prompt size reduction maintaining code structure
- **Cost-Effective Model Selection**: Dynamic selection between GPT-3.5-turbo and GPT-4o
- **Real-Time Pricing**: Actual OpenAI pricing with adjusted output estimates
- **Import Optimization**: Intelligent truncation of import statements

## Context Chaining Architecture

### How Context Chaining Works
The system implements sophisticated conversation continuity that maintains context **within** a component while starting fresh **between** components to prevent context poisoning.

### Within-Component Flow (Same Conversation)
When running `create all api`, the system:

1. **ARCHITECTURE Generation**:
   - Loads `executive_summary.md` as context (if exists)
   - Does NOT create executive_summary.md 
   - Generates ARCHITECTURE.md using executive summary guidance

2. **README Generation**:
   - Uses the SAME conversation context
   - Includes previously generated ARCHITECTURE.md as conversation context
   - References architectural decisions for consistency

3. **SETUP Generation**:
   - Continues the SAME conversation
   - Includes ARCHITECTURE.md + README.md as conversation context
   - Builds on established architectural foundation

4. **CHECKLIST Generation**:
   - Continues the SAME conversation
   - Includes ARCHITECTURE.md + README.md + SETUP.md as conversation context
   - Reflects features described in all previous documents

### Between-Component Separation (New Conversations)
- When moving from "api" to "core" component: **NEW conversation starts**
- Prevents context poisoning between different components
- Maintains document coherence within each component scope

### Technical Implementation
```go
// Cost-optimized contextual chaining with provider flexibility
previousDocuments := make(map[string]string)

for _, docType := range []string{"ARCHITECTURE", "README", "SETUP", "CHECKLIST"} {
    // Each document uses fresh API call with cost-optimized context
    settings := getModelSettingsForDocType(docType)
    optimizedContext := buildOptimizedContext(comp, docType, previousDocuments, settings.ContextStrategy)
    content := generateDocumentWithContext(comp, docType, optimizedContext)
    previousDocuments[docType] = content  // Add to context for next document
}
```

### Cost Optimization Features

#### Per-Document Model Configuration
```yaml
document_types:
  ARCHITECTURE:
    provider: "openai"
    model: "gpt-4.1" 
    temperature: 4.5
    context_strategy: "minimal"
    
  README:
    provider: "openrouter"
    model: "deepseek-r1"
    temperature: 0.7
    context_strategy: "compressed"
    
  SETUP:
    provider: "openrouter" 
    model: "deepseek-r1"
    temperature: 0.7
    context_strategy: "summary_only"
    
  CHECKLIST:
    provider: "openai"
    model: "gpt-4o-mini"
    temperature: 0.0
    context_strategy: "ultra_compressed"
```

#### Context Strategy Optimization
- **minimal**: Executive summary + core source files (ARCHITECTURE)
- **compressed**: 60-70% compression, all previous docs (README)
- **summary_only**: Document summaries only, no source code (SETUP)  
- **ultra_compressed**: Key points extraction only (CHECKLIST)

#### Provider-Specific Compression
- **OpenAI**: Aggressive compression (60-70% reduction)
- **OpenRouter**: Moderate compression (40-50% reduction)
- **Anthropic**: Aggressive compression optimized for Claude

#### Cost Impact Analysis
- **Before**: 4 full-context calls = ~4x cost
- **After**: 1x + 0.6x + 0.3x + 0.2x = ~2.1x cost
- **Provider savings**: ~70% cost reduction using DeepSeek vs GPT-4
- **Total estimated savings**: ~60-70% vs naive implementation

### Template Integration
All templates support cost-optimized context via `{{.ConversationContext}}`:
- Contains compressed previous documents
- Provider-optimized formatting
- Enables cross-document consistency with minimal token overhead

### Example: Cost-Optimized Generation Flow
```bash
./docs-cli create all api

# Output shows cost optimization in action:
# 🔗 Starting context-chained generation for api: ARCHITECTURE → README → SETUP → CHECKLIST
# 📝 Generating ARCHITECTURE with minimal context (GPT-4.1, temp=4.5)...
# 💰 Cost estimate: $0.045 (1,200 tokens) 
# ✅ Generated ARCHITECTURE (added to context chain)
# 📝 Generating README with compressed context (DeepSeek-R1, temp=0.7)...
# 💰 Cost estimate: $0.008 (2,800 tokens compressed from 6,500)
# ✅ Generated README (added to context chain)
# 📝 Generating SETUP with summary-only context (DeepSeek-R1, temp=0.7)...
# 💰 Cost estimate: $0.004 (1,400 tokens, no source code)
# ✅ Generated SETUP (added to context chain)
# 📝 Generating CHECKLIST with ultra-compressed context (GPT-4o-mini, temp=0.0)...
# 💰 Cost estimate: $0.002 (800 tokens, key points only)
# ✅ Generated CHECKLIST (added to context chain)
# 🎯 Total estimated cost: $0.059 (vs $0.180 without optimization)
```

## Deep Thinking Configuration

### Supported Models & APIs

#### **OpenRouter Models**
- **DeepSeek-R1**: `deepseek/deepseek-r1` with reasoning object
- **o1/o3 via OpenRouter**: `openai/o1-preview`, `openai/o3-mini` 

#### **OpenAI Direct**
- **o1 Series**: `o1-preview`, `o1-mini` with `reasoning_effort`
- **o3 Series**: `o3-mini`, `o3-preview` with `reasoning_effort`

#### **Anthropic Models**
- **Opus 4**: `claude-opus-4-20250514` with thinking object
- **Sonnet 4**: `claude-sonnet-4-20250514` with thinking object

### Configuration Options

#### **Per-Document Configuration**
```yaml
document_types:
  README:
    provider: "openrouter"
    model: "deepseek-r1"
    enable_thinking: true
    thinking_level: "high"  # low, medium, high
```

#### **Global Flag Override**
```bash
# Enable thinking for all supported models
./docs-cli create all api --think

# Override config settings, uses "high" thinking level
./docs-cli create README core --think --force
```

### Thinking Parameters by Provider

#### **OpenRouter (DeepSeek-R1)**
```json
{
  "reasoning": {
    "effort": "high",
    "max_tokens": 8192,
    "exclude": false,
    "enabled": true
  }
}
```

#### **OpenAI (o1/o3)**
```json
{
  "reasoning_effort": "high"  // low, medium, high
}
```

#### **Anthropic**
```json
{
  "thinking": {
    "type": "enabled",
    "budget_tokens": 15000
  }
}
```

### Cost Impact of Thinking

**Thinking Cost Multipliers**:
- **Low**: 1.2x - 1.4x base cost
- **Medium**: 1.5x - 1.8x base cost  
- **High**: 2.0x - 2.5x base cost

**Example Cost Comparison**:
```bash
# Without thinking
./docs-cli create all api
# Cost: $0.059

# With thinking enabled
./docs-cli create all api --think  
# Cost: ~$0.118 (2x for high-level thinking)
# Quality: Significantly improved reasoning and consistency
```

## Provider Customization
- Remember to keep all provider customizations in separate files
- Each provider has its own optimization strategy tailored to pricing and capabilities
- Cost optimization is applied automatically based on provider selection
- Thinking capabilities are provider-specific and auto-detected based on model support