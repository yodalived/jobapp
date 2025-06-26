# ENTERPRISE README GENERATION

Generate professional README.md for {{.ComponentName}} component.

## CONTEXT
**Component Information**:  
- Path: {{.ComponentPath}}  
- Type: {{.ComponentType}}  

**Project and Source Context**:  
{{.SourceContext}}

**Conversation Context (Previously Generated Documents)**:  
{{.ConversationContext}}

## REQUIREMENTS
1. **Business Purpose**: Value proposition and business impact
2. **Key Features**: Capabilities with concrete examples
3. **Usage Patterns**: 
   - Primary use cases
   - Code samples for integration
   - API endpoint reference
4. **Configuration**: 
   - Environment variables
   - Config files
   - Feature flags
5. **Development Guidelines**:
   - Contribution process
   - Testing strategy
   - Code quality standards
6. **Performance Characteristics**:
   - Throughput metrics
   - Latency expectations
   - Resource consumption

## OUTPUT INSTRUCTIONS
- Use ## for section headers
- Include runnable code examples
- Link to architecture documentation
- Minimum length: 1500 words
- Address scalability considerations