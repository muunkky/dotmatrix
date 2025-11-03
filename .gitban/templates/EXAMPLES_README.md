# Gitban Example Cards

> Canonical example cards demonstrating gitban best practices across all card types and complexity levels

This repository contains high-quality example cards that demonstrate how to write effective gitban cards for different scenarios. Use these as learning materials, starting points for your own cards, or templates to adapt.

## 📚 What's Inside

**12 Example Cards** covering all major card types:
- 🎯 **Features** (simple, medium, complex) - New functionality and capabilities
- 🐛 **Bugs** (simple, medium) - Issues and defects with reproduction steps
- 📖 **Docs** - Documentation tasks and technical writing
- ✅ **Tests** - Test coverage and quality improvements
- 🔧 **Chore** - Maintenance, dependencies, tooling
- ♻️ **Refactor** - Code quality and architecture improvements
- 💅 **Style** - Code formatting and style consistency
- ⚡ **Performance** - Optimization and speed improvements
- 🤖 **CI** - Continuous integration and deployment

## 🚀 Using These Examples

### Via Gitban MCP Tools

The easiest way to explore and use these examples is through gitban's MCP tools:

```python
# List all available examples
list_example_cards()

# Filter by card type
list_example_cards(card_type="feature")

# Filter by complexity
list_example_cards(complexity="simple")

# Filter by tags
list_example_cards(tags=["beginner-friendly"])

# Download a specific example
download_example_card("feature-simple-button")

# Download to custom location
download_example_card("bug-simple-crash", save_to="my-examples/bug-template.md")
```

### Manual Download

You can also browse and download examples directly from this repository:

1. Browse the `examples/` directory
2. Click on any `.md` file to view
3. Click "Raw" to download
4. Save to your `.gitban/examples/` directory

**⚠️ Important Note:** These example files use descriptive names like `feature-simple-button.md` for readability. If you want to use them as actual gitban cards in your workspace, you'll need to rename them to follow gitban's card naming convention:

```
# Example filename (for learning):
feature-simple-button.md

# Actual card filename (for use in .gitban/cards/):
backlog-P1-feature-add-submit-button-abc123.md
```

The MCP tool `download_example_card()` handles this automatically when you save to `.gitban/cards/`, but manual downloads will need renaming.

## 📋 Example Index

### By Complexity

#### Simple (Quick, 1-2 hours)
- `feature-simple-button` - Add UI component with basic validation
- `bug-simple-crash` - Fix obvious error with clear reproduction steps
- `style-code-formatting` - Apply code formatting with Prettier

#### Medium (Half day to 1 day)
- `feature-medium-api` - REST API endpoint with auth and validation
- `bug-medium-performance` - Performance issue with profiling and optimization
- `docs-api-documentation` - API documentation with OpenAPI spec
- `test-increase-coverage` - Systematic test coverage improvement
- `chore-dependency-update` - Dependency updates with security patches
- `ci-github-actions` - CI/CD pipeline setup with GitHub Actions

#### Complex (Multiple days to weeks)
- `feature-complex-auth` - Complete OAuth2 authentication system
- `refactor-simplify-auth` - Major architectural refactoring
- `perf-optimize-queries` - Database query optimization with indexing and caching

### By Card Type

| Type | Examples | Use Case |
|------|----------|----------|
| **feature** | simple-button, medium-api, complex-auth | New functionality, capabilities |
| **bug** | simple-crash, medium-performance | Issues, defects, errors |
| **docs** | api-documentation | Documentation, technical writing |
| **test** | increase-coverage | Testing, quality assurance |
| **chore** | dependency-update | Maintenance, tooling, dependencies |
| **refactor** | simplify-auth | Code quality, architecture |
| **style** | code-formatting | Formatting, style consistency |
| **perf** | optimize-queries | Performance, optimization |
| **ci** | github-actions | CI/CD, automation |

## 🎓 Learning Path

### Beginners
Start with these simple, well-structured examples:
1. `feature-simple-button` - Learn basic feature card structure
2. `bug-simple-crash` - Learn bug reporting best practices
3. `style-code-formatting` - Learn chore/maintenance cards

### Intermediate
Progress to medium complexity cards:
1. `feature-medium-api` - Learn API design and implementation planning
2. `bug-medium-performance` - Learn performance debugging and optimization
3. `docs-api-documentation` - Learn technical documentation

### Advanced
Tackle complex, multi-faceted cards:
1. `feature-complex-auth` - Learn comprehensive system design
2. `refactor-simplify-auth` - Learn large-scale refactoring planning
3. `perf-optimize-queries` - Learn database optimization strategies

## 🏷️ Tags Guide

Examples are tagged to help you find relevant patterns:

- `beginner-friendly` - Good starting points for new users
- `frontend` - UI, React, client-side code
- `backend` - APIs, servers, databases
- `security` - Authentication, authorization, vulnerabilities
- `performance` - Optimization, speed, efficiency
- `architecture` - System design, patterns, structure
- `testing` - Test strategies, coverage, quality

## 💡 Customizing Examples

These examples are starting points - **adapt them to your needs!**

### For Your Team
- Replace placeholder names with your actual services
- Adjust acceptance criteria to match your definition of done
- Add/remove sections based on your workflow
- Change complexity estimates to match your team's velocity

### For Your Domain
- Software teams: Use as-is or adapt slightly
- Writing teams: Replace code examples with writing tasks
- Research teams: Adapt for research objectives and methodologies
- Operations teams: Adjust for infrastructure and deployment tasks

## 🤝 Contributing

Want to add more examples or improve existing ones?

1. Fork this repository
2. Create a new example card in `examples/`
3. Update `manifest.json` with metadata
4. Submit a pull request

**Good examples to add:**
- Mobile app development cards
- Data science/ML workflow cards
- Content creation and editorial cards
- DevOps and infrastructure cards
- Design and UX research cards

## 📜 License

These example cards are provided under the MIT License. Feel free to use, modify, and share them for any purpose.

## 🔗 Related Resources

- [Gitban Documentation](https://github.com/gitban-mcp/gitban-mcp-dev) - Main gitban repository
- [MCP Protocol](https://modelcontextprotocol.io) - Model Context Protocol specification
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format we follow

## 📞 Questions or Feedback?

- Open an issue in this repository
- Use the gitban feedback tool: `send_feedback()`
- Join discussions in the main gitban repo

---

**Happy card writing! May your backlogs be manageable and your sprints be successful!**
