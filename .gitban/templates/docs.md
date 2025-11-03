
# [Document title - REQUIRED]

## Location

**File Path**: `[Path to documentation file]`

[Specify the exact location where this documentation will be created or updated]

**Related Files**:
- `[path/to/related/file1]`: [Relationship]
- `[path/to/related/file2]`: [Relationship]

---

## Documentation Goal

[Clear statement of what documentation needs to be created or updated and why it's needed]

**Purpose**: [Primary purpose - onboarding, troubleshooting, API reference, etc.]

**Problem Being Solved**: [What gap in documentation this fills]

**Value**: [How this documentation helps users, developers, or the organization]

**Estimated Effort**: [Time estimate, e.g., 2 hours, 1 day]

---

## Audience

**Primary Audience**: [Who will read this - developers, users, ops team]

[Detailed description of who will read and use this documentation]

### Audience Characteristics

- **Role**: [Developer, user, admin, contributor, etc.]
- **Experience Level**: [Beginner, intermediate, advanced]
- **Goals**: [What they're trying to accomplish]
- **Context**: [Where/when they'll read this]
- **Prerequisites**: [What they should already know]

### User Scenarios

1. **Scenario 1**: [Common use case]
   - User needs: [What information they need]
   - Success: [What they can do after reading]

2. **Scenario 2**: [Another use case]
   - User needs: [What information they need]
   - Success: [What they can do after reading]

---

## Scope

[What topics, features, or areas this documentation will cover]

- [ ] **Topic 1**: [Description of content to cover]
- [ ] **Topic 2**: [Description of content to cover]
- [ ] **Topic 3**: [Description of content to cover]
- [ ] **Topic 4**: [Description of content to cover]

### In Scope

[Explicitly state what is included]

- [Feature/concept 1] - [Why included]
- [Feature/concept 2] - [Why included]

### Out of Scope

[Explicitly state what is NOT included and why]

- [Feature/concept 1] - [Why excluded - covered elsewhere, future work, etc.]
- [Feature/concept 2] - [Why excluded]

---

## Documentation Type (Diátaxis)

[Select the documentation type(s) using the Diátaxis framework]

### Primary Type

- [ ] **Tutorial** (learning-oriented)
  - **Goal**: Teaching - helping user learn through hands-on lessons
  - **Structure**: Step-by-step learning journey with explanation
  - **Tone**: Friendly, encouraging, patient
  - **Example**: "Getting Started with Gitban"

- [ ] **How-To Guide** (task-oriented)
  - **Goal**: Guiding - helping user accomplish specific task
  - **Structure**: Problem → Solution steps → Result
  - **Tone**: Direct, practical, goal-focused
  - **Example**: "How to Configure Template Enforcement"

- [ ] **Reference** (information-oriented)
  - **Goal**: Informing - providing technical description
  - **Structure**: Structured, consistent, comprehensive
  - **Tone**: Neutral, precise, technical
  - **Example**: "MCP Tools API Reference"

- [ ] **Explanation** (understanding-oriented)
  - **Goal**: Explaining - clarifying concepts and design
  - **Structure**: Context → Concept → Connections
  - **Tone**: Thoughtful, contextual, clear
  - **Example**: "Architecture Decision: Why Template Enforcement"

### Supporting Types

[Secondary documentation types included]

- [ ] [Type]: [Which sections use this approach]

### Documentation Structure

[Outline of major sections and subsections]

```markdown
# Main Title
## Section 1 (optional)
### Subsection 1.1
### Subsection 1.2
## Section 2 (optional)
## Section 3 (optional)
```

---

## Acceptance Criteria

[Clear criteria for when documentation is complete and high-quality]

### Content Completeness

- [ ] All in-scope topics covered thoroughly
- [ ] Key concepts explained with examples
- [ ] Common use cases documented
- [ ] Edge cases and gotchas noted
- [ ] Troubleshooting section included (if applicable)

### Quality Standards

- [ ] Clear, concise writing with consistent voice
- [ ] Proper grammar, spelling, and formatting
- [ ] Appropriate for target audience level
- [ ] Follows documentation style guide
- [ ] Accessible and inclusive language

### Technical Accuracy

- [ ] All code examples tested and working
- [ ] All commands verified in target environment
- [ ] All API signatures accurate and up-to-date
- [ ] All screenshots current and correct
- [ ] All links working and pointing to correct locations

### Structure & Navigation

- [ ] Logical flow and organization
- [ ] Clear headings and subheadings
- [ ] Table of contents (if >5 sections)
- [ ] Cross-references to related docs
- [ ] Search-friendly keywords included

### Supporting Materials

- [ ] Code examples provided for key concepts
- [ ] Diagrams or visuals included (if helpful)
- [ ] Sample configurations or templates included
- [ ] Runnable examples or sandbox available

### Review & Approval

- [ ] Technical review completed
- [ ] Audience review completed (if possible)
- [ ] Feedback incorporated
- [ ] Final approval obtained

**Quality Metrics**:
- Total sections: [Target number]
- Code examples: [Target number]
- Diagrams/visuals: [Target number]
- Cross-references: [Target number]
- Estimated read time: [X minutes]

---

## Deliverables (optional)

[Concrete outputs from this documentation work]

### Primary Deliverable

- **File**: `[Path to documentation file]`
- **Format**: [Markdown, HTML, PDF, etc.]
- **Length**: [Target page count or word count]

### Supporting Deliverables

- [ ] **Code Examples**: [Where stored, how many]
- [ ] **Diagrams**: [Mermaid, images, architecture diagrams]
- [ ] **Configuration Templates**: [Example configs, boilerplate]
- [ ] **Video/Screencast**: [If creating video content]
- [ ] **Interactive Examples**: [Code sandboxes, live demos]

### Integration

- [ ] Documentation added to site navigation
- [ ] Cross-references updated in related docs
- [ ] Search index updated
- [ ] Version history/changelog updated

### Publication

- [ ] Markdown source committed to repository
- [ ] Documentation site rebuilt/deployed
- [ ] Announcement made (if significant update)
- [ ] Feedback mechanism in place

---

## Prerequisites (optional)

[Requirements that must be met before creating this documentation]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Prerequisite 1 - feature/system being documented is complete]
- [ ] [Prerequisite 2 - access to system for testing examples]
- [ ] [Prerequisite 3 - understanding of target audience needs]
- [ ] [Prerequisite 4 - documentation style guide available]

**Why**: [Explain why these prerequisites are critical]

[Common reason: Documentation should reflect reality, not theory. Document completed features, not planned ones.]

### Required Knowledge

[Knowledge needed to write this documentation]

- [Subject matter expertise needed]
- [Technical skills required]
- [Domain knowledge necessary]

### Required Access

- [ ] Access to system being documented
- [ ] Ability to test commands/code examples
- [ ] Permission to publish documentation

---

## Related Cards (optional)

[Connections to features, bugs, or other documentation]

### Dependencies

**Depends on**: [Card ID] - [Description - typically feature implementation cards]

[Cards that must be completed before documentation can be written]

### Blocks

**Blocks**: [Card ID] - [Description - cards waiting for documentation]

[Cards that need this documentation to proceed]

### Related Documentation

**Related**: [Card ID] - [Description - related docs or parallel documentation]

- [Related doc 1]: [Relationship]
- [Related doc 2]: [Relationship]

### Cross-References

- Features Documented: [Link to feature cards]
- ADRs Referenced: [Link to architecture decisions]
- Related Guides: [Link to complementary documentation]

---

## Resources (optional)

[References, examples, and tools for creating this documentation]

### Reference Materials

- [Existing documentation to build on]
- [Feature specifications or RFCs]
- [API documentation or source code]
- [Competitor documentation for inspiration]

### Style Guides

- **Writing Style**: [Link to style guide]
- **Code Style**: [Link to code conventions]
- **Formatting**: [Markdown guide, template to follow]

### Tools

- **Editor**: [Recommended editor with preview]
- **Diagram Tools**: [Mermaid, Draw.io, etc.]
- **Screenshot Tools**: [Tool for capturing images]
- **Testing**: [How to verify code examples work]

### Examples

[Links to similar documentation that serves as good examples]

- [Example doc 1]: [Why it's a good model]
- [Example doc 2]: [What to emulate]

### Diátaxis Resources

- Diátaxis: https://diataxis.fr/
- Documentation types explained with examples

---

## Notes (optional)

[Additional context, style considerations, or important details]

### Writing Guidelines

[Specific guidance for this documentation]

- **Tone**: [Formal/informal, friendly/technical]
- **Voice**: [First person, second person, third person]
- **Tense**: [Present/past, active/passive]
- **Examples**: [How detailed, realistic vs simplified]

### Content Strategy

[Approach to content organization and presentation]

- [Strategy note 1]
- [Strategy note 2]

### Accessibility Considerations

- [ ] Alt text for all images
- [ ] Descriptive link text (not "click here")
- [ ] Proper heading hierarchy
- [ ] Color not sole indicator of meaning

### Internationalization

[If documentation needs to support multiple languages]

- Languages: [Which languages]
- Translation process: [How docs are translated]
- Localization notes: [Cultural considerations]

### Maintenance Plan

[How this documentation will be kept up-to-date]

- **Update Frequency**: [When to review/update]
- **Owner**: [Who maintains this documentation]
- **Trigger**: [What changes require doc updates]

---

## Progress Notes (optional)

[Track documentation writing session by session]

**Session [Date] ([Your Name]):**

✅ **Completed:**
- [Sections written]
- [Examples created and tested]
- [Diagrams created]

🔄 **In Progress:**
- [Current section being written]
- [Current word count / target]

📊 **Metrics:**
- Sections complete: X / Y
- Code examples: X / Y
- Diagrams: X / Y
- Word count: ~XXXX

⚠️ **Questions/Blockers:**
- [Unclear technical detail]
- [Missing information]
- [Need review from SME]

📋 **Next Session:**
1. [Next section to write]
2. [Examples to create]
3. [Reviews to request]

**Writing Notes:**
[Observations about content, audience feedback, or style decisions]

---

<!--
EXTENSION POINTS:

This template can be extended with additional sections as needed:

## SEO & Discoverability (optional)
[For public documentation - keywords, meta descriptions, search optimization]

## API Documentation (optional)
[For API reference docs - endpoints, parameters, responses, examples]

## Changelog Integration (optional)
[How this documentation relates to product changelog]

## Video Script (optional)
[If creating video documentation - script, timestamps, demos]

## Translation Checklist (optional)
[For multi-language documentation]

## Legal Review (optional)
[For documentation with legal implications]

## Versioning Strategy (optional)
[For documentation that needs to support multiple product versions]

Add any project-specific sections your team needs!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
