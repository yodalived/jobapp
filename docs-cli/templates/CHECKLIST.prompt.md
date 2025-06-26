# ENTERPRISE CHECKLIST GENERATION

Generate structured CHECKLIST.yaml for {{.ComponentName}} component using the EXACT template structure below.

## TEMPLATE STRUCTURE
```yaml:docs-cli/templates/CHECKLIST.template.yaml
categories:
  - name: "{{.ComponentName}} Core Features"
    tasks:
      - name: "Feature Name"
        status: "completed"  # Must be: completed, in_progress, planned
        priority: "high"     # Must be: high, medium, low
        description: "Task description"
        dependencies: []     # Optional list of task names

  - name: "{{.ComponentName}} Integration"
    tasks: [...]

  - name: "{{.ComponentName}} Testing"
    tasks: [...]

  - name: "{{.ComponentName}} Documentation"
    tasks: [...]

  - name: "{{.ComponentName}} Deployment"
    tasks: [...]
```

## CONTEXT
**Component Information**:
- Path: {{.ComponentPath}}
- Type: {{.ComponentType}}

**Project and Source Context**:
{{.SourceContext}}

**Conversation Context (Previously Generated Documents)**:
{{.ConversationContext}}

## REQUIREMENTS
1. **Strict Template Adherence**:
   - Use EXACTLY the categories from the template
   - Maintain EXACT field names and hierarchy
   - Replace {{.ComponentName}} with actual component name
   
2. **Task Structure**:
   - name: Clear, actionable title (3-7 words)
   - status: [completed, in_progress, planned] (exactly these values)
   - priority: [high, medium, low] (exactly these values)
   - description: 1-2 sentence explanation (15-50 words)
   - dependencies: [optional list of task names]

3. **Validation Rules**:
   - All fields required except dependencies
   - No empty names or descriptions
   - Status and priority must match allowed values
   - Tasks must be logically grouped under categories
   - No markdown formatting in YAML

## OUTPUT INSTRUCTIONS
- Generate 5-10 tasks per category
- Use consistent YAML formatting (2-space indentation)
- Include template comments for clarity
- Ensure all tasks are actionable and measurable
- Output must be valid YAML that passes schema validation