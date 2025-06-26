# ENTERPRISE SETUP DOCUMENTATION

Generate detailed SETUP.md for {{.ComponentName}} component.

## CONTEXT
**Component Information**:  
- Path: {{.ComponentPath}}  
- Type: {{.ComponentType}}  

**Project and Source Context**:  
{{.SourceContext}}

**Conversation Context (Previously Generated Documents)**:  
{{.ConversationContext}}

## REQUIREMENTS
1. **Prerequisites**:
   - Hardware requirements (CPU, memory, storage)
   - Software dependencies with version constraints
   - Network configuration

2. **Installation**:
   - Step-by-step commands with examples
   - Container deployment (Docker/Kubernetes)
   - OS-specific instructions (Linux, macOS, Windows)

3. **Configuration**:
   - Environment variables
   - Config files (YAML format)
   - Secret management
   - Multi-environment setup (dev/stage/prod)

4. **Verification**:
   - Health check procedures
   - Smoke tests
   - Performance benchmarks

5. **Troubleshooting**:
   - Common issues and solutions
   - Diagnostic commands
   - Log analysis guidelines

6. **Maintenance**:
   - Backup procedures
   - Upgrade instructions
   - Scaling operations

## OUTPUT INSTRUCTIONS
- Use numbered steps for procedures
- Include command-line examples in code blocks
- Note OS-specific differences
- Address security best practices
- Minimum length: 1500 words