# Documentation CLI Tool

A Go CLI tool for automated documentation generation using the Claude API with full source code context.

## Features

- 🤖 **Claude Integration**: Uses Claude API for intelligent documentation generation
- 📁 **Configuration-Based**: Uses `components.yaml` to define exactly which components to document
- 📝 **Template-Based Prompts**: Customizable prompt templates for each documentation type
- 📊 **Full Source Context**: Includes ALL source files from each component (no limits or truncation)
- 📚 **Project Documentation Context**: Automatically includes project-level docs (README.md, PROJECT_STATUS.md, CLAUDE.md) and all files in docs/context/
- 🔄 **Flexible Commands**: Support for generating single or all documentation types
- ⚙️ **Configurable**: Model selection and settings via environment variables
- 📋 **Status Generation**: Creates consolidated status page from CHECKLIST.yaml files

## Installation

```bash
cd docs-cli
go mod tidy
go build -o docs-cli .
```

## Setup

1. **Copy the environment template:**
```bash
cp .env.example .env
```

2. **Configure your settings in `.env`:**
```bash
# Required: Your Anthropic API key
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Claude model selection (default: claude-3-5-sonnet-20241022)
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Optional: Max tokens per request (default: 4000)
CLAUDE_MAX_TOKENS=4000
```

3. **Or set environment variables directly:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export CLAUDE_MODEL="claude-3-5-sonnet-20241022"
```

4. **Ensure components.yaml exists:**
The tool requires a `components.yaml` file to define which components to document. See the example below.

## Usage

### List Available Components

```bash
./docs-cli list
```

### Create Documentation

```bash
# Create README for specific component
./docs-cli create README api

# Create all documentation types for specific component
./docs-cli create all core

# Create specific documentation type for all components
./docs-cli create README all
./docs-cli create SETUP all
./docs-cli create ARCHITECTURE all
./docs-cli create CHECKLIST all

# Create all documentation types for all components
./docs-cli create all all

# Force overwrite existing documentation (multiple flag formats supported)
./docs-cli create README api --force
./docs-cli create all core -f
```

### Update All Documentation

```bash
# Update README, SETUP, and ARCHITECTURE for all components
./docs-cli update

# Force overwrite existing
./docs-cli update --force
./docs-cli update -f
```

### Generate Status Page

```bash
# Generate status.json from all CHECKLIST.yaml files
./docs-cli status
```

## Commands

| Command | Description | Examples |
|---------|-------------|----------|
| `list` | List all available components and their existing documentation | `./docs-cli list` |
| `create [type] [component]` | Create specific documentation type | `./docs-cli create README api` |
| `create all [component]` | Create all documentation types for a component | `./docs-cli create all core` |
| `update` | Update all documentation for all components | `./docs-cli update` |
| `status` | Generate status page from checklists | `./docs-cli status` |

### Flags
- `--force`, `-f` - Overwrite existing documentation without prompting

## Document Types

- **README** - Component overview, features, usage examples
- **SETUP** - Installation and configuration instructions
- **ARCHITECTURE** - System design and architectural decisions
- **CHECKLIST** - Feature tracking and status information (YAML format)

## Component Configuration

The tool uses a `components.yaml` file to define which components to document. This approach provides:

- **✅ Explicit Control**: You decide exactly which components to document
- **✅ Full Source Context**: Claude receives ALL source files from each component (no truncation)
- **✅ Complete Understanding**: No arbitrary file limits - Claude sees your entire codebase
- **✅ Custom Descriptions**: Add meaningful descriptions for each component
- **✅ Flexible Patterns**: Configure which file types to include/exclude

### Why Configuration-Based?
Unlike dynamic discovery that might miss important files or hit arbitrary limits, the configuration approach ensures Claude gets complete context about your application, leading to much better documentation quality.

## Project Documentation Context

The tool automatically includes project-wide documentation context with every component documentation generation. This ensures Claude has complete understanding of the overall project when creating component-specific documentation.

### Automatically Included Files

**Top-Level Documentation** (if they exist):
- `README.md` - Main project overview
- `PROJECT_STATUS.md` - Current development status
- `CLAUDE.md` - Development instructions and patterns

**Dynamic Context Directory**:
- All `.md` files in `docs/context/` - Architecture decisions, troubleshooting, recent changes, etc.

### Benefits

- **✅ Consistent Context**: Every component doc has full project understanding
- **✅ Dynamic Discovery**: Automatically picks up new files in `docs/context/`
- **✅ No Manual Updates**: No need to modify the tool when documentation structure changes
- **✅ Complete Picture**: Claude sees both component code and project architecture
- **✅ Better Quality**: Documentation aligns with overall project goals and patterns

This context enables Claude to generate documentation that properly integrates with the overall project architecture and follows established patterns.

## Template System

Documentation prompts are now template-based for easy customization:

- `templates/README.prompt.md` - README generation prompt
- `templates/SETUP.prompt.md` - Setup guide prompt  
- `templates/ARCHITECTURE.prompt.md` - Architecture documentation prompt
- `templates/CHECKLIST.prompt.md` - Checklist generation prompt

Templates support variable substitution:
- `{{.ComponentName}}` - Component name
- `{{.ComponentPath}}` - Component path
- `{{.ComponentType}}` - Component type (service/frontend)
- `{{.ExistingDocs}}` - List of existing documentation
- `{{.SourceContext}}` - Full source code context (all files)
- `{{.ExistingContent}}` - Existing content (for updates)

## Example components.yaml

```yaml
components:
  - name: "api"
    path: "src/api"
    type: "service"
    description: "FastAPI backend with routers for auth, applications, files, and generator"
    
  - name: "core"
    path: "src/core"
    type: "service"
    description: "Core utilities including auth, database, email, events, and Kafka client"
    
  - name: "frontend"
    path: "frontend/src"
    type: "frontend"
    description: "Next.js frontend with authentication, dashboard, and status pages"
    
  - name: "storage"
    path: "src/core/storage"
    type: "service"
    description: "Multi-backend storage system with local, MinIO, S3, and Azure backends"

# File patterns
include_patterns:
  - "*.py"          # Python source files
  - "*.go"          # Go source files
  - "*.ts"          # TypeScript files
  - "*.tsx"         # React TypeScript files
  - "*.js"          # JavaScript files
  - "*.jsx"         # React JavaScript files
  - "*.tex"         # LaTeX templates
  - "*.yaml"        # Configuration files
  - "*.yml"         # Configuration files
  - "*.json"        # JSON configuration
  - "*.md"          # Markdown documentation

exclude_patterns:
  - "__pycache__/*"      # Python cache
  - "*.pyc"              # Python bytecode
  - "node_modules/*"     # Node.js dependencies
  - ".next/*"            # Next.js build cache
  - "build/*"            # Build artifacts
  - "dist/*"             # Distribution files
  - "*.log"              # Log files
  - ".env"               # Environment files
  - ".env.local"         # Local environment
  - "tsconfig.tsbuildinfo"  # TypeScript build cache
  - "package-lock.json"  # Lock files
```

## Status Page Generation

The `status` command collects all `CHECKLIST.yaml` files from configured components and generates a consolidated `status.json` file with:

- Project overview and metadata
- Component-wise task lists with status tracking
- Completion statistics and progress metrics
- Last updated timestamp
- Summary analytics across all components

```bash
# Generate status page from all component checklists
./docs-cli status
```

This creates a `status.json` file that can be consumed by status dashboards or monitoring systems.

## Example CHECKLIST.yaml Format

```yaml
categories:
  - name: "Core Features"
    tasks:
      - name: "User Authentication"
        status: "completed"
        priority: "high"
        description: "JWT-based authentication system"
      - name: "Resume Generation"
        status: "in_progress" 
        priority: "high"
        description: "AI-powered resume customization"
        dependencies:
          - "User Authentication"
```

## Key Improvements from Previous Version

### ✅ **Configuration-Based vs Dynamic Discovery**
- **Before**: Hardcoded component paths, missed important files
- **Now**: Explicit `components.yaml` configuration for complete control

### ✅ **Full Source Context vs Truncated**
- **Before**: Limited to 5 files, 2000 characters each (~10KB total context)
- **Now**: ALL source files included in full (no limits, no truncation)

### ✅ **Template-Based Prompts vs Hardcoded**
- **Before**: Prompts hardcoded in Go source
- **Now**: Editable template files in `templates/` directory

### ✅ **Flexible Command Syntax**
- **Before**: `./docs-cli create README api`
- **Now**: Supports `./docs-cli create all core` for all doc types

### ✅ **Environment Configuration**
- **Before**: Hardcoded Claude model
- **Now**: Configurable via `CLAUDE_MODEL` and `CLAUDE_MAX_TOKENS`

## Error Handling

The tool provides clear error messages for:
- Missing API key or `components.yaml` file
- Invalid component names or document types
- File permission issues
- API request failures
- Invalid YAML syntax in configuration