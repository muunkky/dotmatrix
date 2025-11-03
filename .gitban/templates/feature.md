
## Description

[Feature name and brief summary - REQUIRED]

[Comprehensive description of the feature and what it enables]

**Value**: [Business value and user benefit - REQUIRED]

[Explain the business impact, user benefit, or technical value this feature provides. Be specific about how this improves the system or user experience.]

**Target Users**: [Who will use this feature]

**Estimated Effort**: [Time estimate, e.g., 2 days, 1 week]

---

## Acceptance Criteria

[Clear, testable criteria that define when this feature is complete. Use checkboxes for tracking.]

- [ ] Core functionality criterion 1
- [ ] Core functionality criterion 2
- [ ] User experience criterion
- [ ] Performance criterion (optional)
- [ ] Security criterion (optional)
- [ ] Documentation criterion (optional)

**Quality Metrics** (if applicable):
- [ ] Test coverage: >90% for new code (optional)
- [ ] Performance: [specific benchmark, e.g., <100ms response time] (optional)
- [ ] Error rate: <0.1% in production (optional)
- [ ] User satisfaction: [specific metric if measurable] (optional)

---

## Implementation Plan

[High-level implementation strategy broken into numbered, actionable steps]

### Overview

[One paragraph summary of the implementation approach and key technical decisions]

### Implementation Steps

1. **[Step 1 Title]**: [Step description]
   - Sub-task or technical detail
   - Configuration or setup needed
   - Code changes required
   ```[language]
   # Example code or command if helpful
   [code snippet]
   ```

2. **[Step 2 Title]**: [Step description]
   - Sub-task or technical detail
   - Integration points
   - Data flow considerations

3. **[Step 3 Title]**: [Step description]
   - Sub-task or technical detail
   - Error handling approach
   - Edge cases to address

[Add more steps as needed - typically 3-7 major steps]

### Technical Considerations

[Important technical details, constraints, and architectural decisions]

- **Architecture**: [How this fits into the overall system architecture]
- **Data Model**: [Database schema changes, data structures, or API contracts]
- **Performance**: [Performance implications, optimization strategies, caching needs]
- **Security**: [Authentication, authorization, data validation, encryption]
- **Scalability**: [How this handles growth, rate limits, resource constraints]
- **Error Handling**: [Failure modes, retry logic, fallback strategies]
- **Backwards Compatibility**: [Migration strategy, versioning, deprecation plan]

### Dependencies

[External dependencies, services, libraries, or infrastructure needed]

- **Service Dependencies**: [APIs, databases, external services]
- **Library Dependencies**: [New packages to install, version requirements]
- **Infrastructure**: [Servers, networking, storage, permissions]
- **Data Dependencies**: [Required data, seed data, migrations]

### Configuration

[Configuration changes, environment variables, feature flags]

```[config-format]
# Example configuration
[configuration example]
```

### Rollout Strategy

[How this feature will be deployed and enabled]

- **Deployment approach**: [Blue-green, canary, feature flag, etc.]
- **Rollout phases**: [Alpha → Beta → GA, or immediate full rollout]
- **Monitoring**: [Metrics to watch during rollout]
- **Rollback plan**: [How to quickly disable if issues arise]

---

## Testing Strategy (optional)

[Comprehensive testing approach to ensure quality]

### Unit Tests

- [ ] Test core functionality components
- [ ] Test edge cases and boundary conditions
- [ ] Test error handling and validation
- [ ] Test data transformations and business logic

### Integration Tests

- [ ] Test interactions with dependencies
- [ ] Test API endpoints end-to-end
- [ ] Test database operations and transactions
- [ ] Test external service integrations

### Manual Testing Scenarios

[Key scenarios to manually verify]

1. **Happy Path**: [Normal successful flow]
   - Steps to test
   - Expected results

2. **Error Scenarios**: [How system handles errors]
   - Test invalid inputs
   - Test permission failures
   - Test service unavailability

3. **Edge Cases**: [Boundary conditions]
   - Minimum/maximum values
   - Empty or null data
   - Concurrent operations

### Performance Testing

- [ ] Load test under expected traffic
- [ ] Stress test to find breaking points
- [ ] Measure response times and resource usage
- [ ] Verify caching effectiveness

### Security Testing

- [ ] Verify authentication and authorization
- [ ] Test input validation and sanitization
- [ ] Check for common vulnerabilities (SQL injection, XSS, etc.)
- [ ] Verify data encryption and secure storage

---

## Documentation Updates (optional)

[Documentation that needs to be created or updated]

### 📝 IMPORTANT: Update CHANGELOG.md
- [ ] **Add entry to CHANGELOG.md under [Unreleased]** (REQUIRED for user-facing features)
  - Use "Added" for new features
  - Include feature name and brief description
  - Note any breaking changes
  - Mention new CLI flags or API changes
  - See: [Keep a Changelog](https://keepachangelog.com/)

### Other Documentation
- [ ] Update README.md with feature overview (if user-facing)
- [ ] Update ROADMAP.md if this completes or adds a milestone
- [ ] Update API/MCP reference documentation
- [ ] Add usage examples to guides
- [ ] Create/update architecture diagrams
- [ ] Create runbook for operational procedures (if applicable)
- [ ] Update troubleshooting guide with common issues

### Documentation Files to Update

- `[file path 1]`: [What to add/change]
- `[file path 2]`: [What to add/change]

---

## Prerequisites (optional)

[Critical requirements that must be met before starting work on this card]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Prerequisite 1 - dependency, infrastructure, or approval needed]
- [ ] [Prerequisite 2 - data, configuration, or tools required]
- [ ] [Prerequisite 3 - technical foundation or prior work completed]

**Why**: [Explain why these prerequisites are necessary and what happens if work starts prematurely]

### Validation Checklist

[How to verify prerequisites are met]

- [ ] [Verification step 1]
- [ ] [Verification step 2]

---

## Related Cards (optional)

[Relationships to other cards - dependencies, blockers, and related work]

### Dependencies

**Depends on**: [Card ID] - [Brief description of dependency and why it's needed]

[List all cards that must be completed before this one]

### Blocks

**Blocks**: [Card ID] - [Brief description of what this enables]

[List all cards that are waiting for this one]

### Related Work

**Related**: [Card ID] - [Brief description of relationship]

[List cards that are related but not direct dependencies]

### Cross-References

- ADRs: [Link to relevant Architecture Decision Records]
- Issues: [Link to related GitHub issues or bugs]
- PRs: [Link to related pull requests if work is split]
- Docs: [Link to related documentation]

---

## Notes (optional)

[Additional context, research findings, design decisions, or implementation notes]

### Design Decisions

[Key decisions made during planning or implementation]

- **Decision**: [What was decided]
- **Rationale**: [Why this approach was chosen]
- **Alternatives Considered**: [Other options evaluated]
- **Trade-offs**: [Pros and cons of chosen approach]

### Research Findings

[Links to research, RFCs, competitor analysis, or technical investigations]

### Known Limitations

[Current limitations or future improvements needed]

### Open Questions

[Unresolved questions that need answers before or during implementation]

- **Q**: [Question]
- **A**: [Answer once resolved]

### Resources

[Helpful links, documentation, examples, or references]

- [Link 1]: [Description]
- [Link 2]: [Description]

---

## Progress Notes (optional)

[Session-by-session progress updates - add new sections as work proceeds]

**Session [Date] ([Your Name]):**

✅ **Completed:**
- [Completed task 1]
- [Completed task 2]

🔄 **In Progress:**
- [What's currently being worked on]

⚠️ **Blockers:**
- [Any issues or blockers encountered]

📋 **Next Steps:**
1. [Next action item]
2. [Following action item]

**Technical Notes:**
[Important technical details discovered during this session]

---

## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

This template provides the minimum structure for feature cards. Feel free to add:
- Custom sections specific to your project
- Cost analysis or resource planning
- Migration strategies or compatibility notes
- Analytics and metrics tracking
- Stakeholder approvals or sign-offs
- User training materials
- Compliance or legal requirements
- Or any other content your team needs!

No validation is enforced below this line - organize additional information however works best for your workflow.
