# Resume Personalization Engine

## Overview

The Resume Personalization Engine is a comprehensive data collection and intelligence system that captures, understands, and leverages a user's complete career history to generate highly personalized resumes and uncover career opportunities.

## Architecture

This system implements a three-layer intelligence architecture:

1. **Data Collection Layer**: Multi-modal ingestion (documents, conversations, notes)
2. **Knowledge Graph Layer**: Structured understanding with skill ontology and relationships
3. **Career Intelligence Layer**: Pattern recognition and opportunity discovery

## Core Components

### 1. Document Processing Pipeline
- **Security Filter**: MIME validation, content safety checks
- **Document Classifier**: Categorizes work documents (resume, cover letter, review, etc.)
- **Content Extractor**: Chunks and tags content with structured schema
- **Deduplication**: SHA-256 hash and semantic similarity filtering

### 2. Conversation Engine
- **Adaptive Interviewing**: Progressively uncovers career details
- **Behavioral Pattern Extraction**: Identifies work style and soft skills
- **Gap Analysis**: Targets missing information intelligently

### 3. Knowledge Management
- **User Knowledge Graph**: Relationships between experiences, skills, and achievements
- **Skill Ontology**: O*NET/ESCO integration for canonical skill mapping
- **Provenance Tracking**: Complete audit trail for every fact

### 4. Intelligence Services
- **Career Path Analysis**: Discovers traditional and non-obvious career options
- **Tone Extraction**: Captures authentic communication style
- **Insight Generation**: Surfaces patterns users don't see themselves

## Data Flow

[User Upload] → [Security Check] → [Classification] → [Extraction] → [Knowledge Graph]
                                                          ↓
[Conversation] → [Pattern Recognition] → [Behavioral Analysis] → [Knowledge Graph]
                                                          ↓
                                                   [Resume Generation]
                                                   [Career Discovery]

## Key Features

- **Multi-source Integration**: Accepts resumes, cover letters, reviews, recommendations
- **Intelligent Deduplication**: Prevents redundant information storage
- **Progressive Profiling**: Builds comprehensive profiles over multiple sessions
- **Explainable Insights**: Shows evidence for all recommendations
- **Privacy-First Design**: User-controlled data with clear deletion options

## Event-Driven Architecture

All components communicate through Kafka events:
- document.uploaded
- document.classified
- content.extracted
- fact.created
- knowledge.updated
- insight.generated

## Security & Compliance

- Content safety filtering on all inputs
- PII detection and optional redaction
- Row-level multi-tenant isolation
- Encryption at rest for sensitive documents
- GDPR-compliant data deletion

## Success Metrics

- Facts extracted per document
- Conversation engagement depth
- Unique insights generated
- User "aha moments" (via feedback)
- Resume personalization score

## Getting Started

See /implementation/SETUP.md for detailed setup instructions.

## Directory Structure

personalization/
├── README.md                    # This file
├── implementation/             
│   ├── SETUP.md               # Setup instructions
│   ├── ARCHITECTURE.md        # Detailed architecture
│   └── DEVELOPMENT.md         # Development guide
├── schemas/
│   ├── resume_item.json       # Core data schema
│   ├── events.json            # Event definitions
│   └── knowledge_graph.json   # Graph structure
├── services/
│   ├── document_processor/    # Document ingestion
│   ├── conversation_engine/   # LLM interactions
│   ├── knowledge_graph/       # Graph management
│   └── intelligence/          # Career insights
└── docs/
   ├── API.md                 # API documentation
   ├── PRIVACY.md             # Privacy policy
   └── ALGORITHMS.md          # Core algorithms
