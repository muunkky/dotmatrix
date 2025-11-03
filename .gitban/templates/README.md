# Custom Templates

This directory contains your workspace templates for gitban card creation.

## Available Templates

Templates have been copied from the gitban package for customization:
- bug.md - Bug reports and fixes
- feature.md - New features and capabilities
- chore.md - Maintenance tasks
- docs.md - Documentation changes
- test.md - Test creation and updates
- refactor.md - Code restructuring
- perf.md - Performance improvements
- ci.md - CI/CD changes
- build.md - Build system changes
- style.md - Code formatting

## Using Templates

Templates are automatically applied when creating cards:
```python
# Uses bug.md template
create_card("Fix crash", card_type="bug")

# Uses custom variant
create_card("Fix crash", card_type="bug", template="bug-regression")
```

## Creating Template Variants

Create variants by following the naming convention:
```
{canonical-type}-{variant-name}.md
```

Examples:
- bug-feature-request.md
- bug-regression.md
- feature-spike.md
- chore-security-upgrade.md

## Template Discovery

Use these MCP tools to work with templates:
- `list_templates()` - See available templates
- `read_template("bug")` - View template content and structure
- Then edit files directly using Write/Edit tools

## Canonical Card Types

Templates must start with one of these prefixes:
feature, bug, chore, refactor, docs, test, perf, ci, build, style, feedback, other

## More Information

For detailed template authoring guide, run:
```python
generate_template_example()
```

Then read .gitban/templates/example.md
