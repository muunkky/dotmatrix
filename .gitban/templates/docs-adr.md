# ADR-XXX: [Decision title - REQUIRED]

## Status

[Status of this decision - REQUIRED]

**Current Status**: [Status] [Proposed/Accepted/Deprecated/Superseded]

**Date**: [Date]

**Supersedes**: [ADR-XXX if applicable] (optional)

**Superseded by**: [ADR-YYY if applicable] (optional)

---

## Decision Context

[What decision we're documenting - REQUIRED]

**Problem Statement**: [Problem being addressed - REQUIRED]

[What issue are we facing? What factors are in play? Why do we need to make this decision now?]

**Background**: [Context and background]

[Additional context about the system, constraints, or business requirements]

---

## Options Considered

[At least 2 alternatives - REQUIRED]

### Option 1: [Option 1 name]

**Description**: [Description of option 1]

**Pros**:
- [Advantage 1]
- [Advantage 2]
- [Advantage 3]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]
- [Disadvantage 3]

**Trade-offs**: [Trade-offs for option 1] (optional)

### Option 2: [Option 2 name]

**Description**: [Description of option 2]

**Pros**:
- [Advantage 1]
- [Advantage 2]
- [Advantage 3]

**Cons**:
- [Disadvantage 1]
- [Disadvantage 2]
- [Disadvantage 3]

**Trade-offs**: [Trade-offs for option 2] (optional)

### Option 3: [Option 3 name] (optional)

[Additional options considered]

---

## Decision

[What we chose - REQUIRED]

**Selected Option**: [Chosen option - REQUIRED]

**Rationale**: [Why this option was chosen - REQUIRED]

[Why did we choose this option? What evidence supports this decision? Be specific about how this solves the problem.]

**Decision Makers**: [People involved in decision] (optional)

---

## Consequences

[What happens as a result - optional but recommended]

### Positive Consequences (optional)

- [Positive consequence 1]
- [Positive consequence 2]
- [Positive consequence 3]

### Negative Consequences (optional)

- [Negative consequence 1]
- [Negative consequence 2]
- [Negative consequence 3]

### Neutral Consequences (optional)

- [Neutral consequence 1]
- [Neutral consequence 2]

---

## Implementation Notes (optional)

[How to implement this decision]

**Migration Steps**: (optional)
1. [Migration step 1]
2. [Migration step 2]
3. [Migration step 3]

**Affected Components**: (optional)
- [Affected component 1]
- [Affected component 2]

**Timeline**: [Implementation timeline] (optional)

---

## References (optional)

[Links to related docs, spikes, discussions]

- Spike card: [link] (optional)
- Design doc: [link] (optional)
- Related ADRs: [links] (optional)
- External resources: [links] (optional)
- Discussion thread: [link] (optional)

---

## Review History (optional)

[Track when ADR was reviewed/updated]

- [Date]: Created by [Author name] (optional)
- [Date]: Reviewed by [Reviewer name] (optional)
- [Date]: Updated by [Author name] - [Summary of changes] (optional)

---

## Additional Notes (optional)

📝 FREEFORM SECTION - Add anything project-specific

[Any other relevant information]

---

## ADR Template Tips

**Status lifecycle**:
- **Proposed**: Decision under discussion
- **Accepted**: Decision approved and active
- **Deprecated**: No longer recommended (but code may still use it)
- **Superseded**: Replaced by newer ADR

**Best practices**:
- Keep ADRs immutable - don't edit decisions, create new ADRs that supersede
- Number ADRs sequentially (ADR-001, ADR-002, etc.)
- Store in `docs/adr/` directory
- Link from code comments where decision is implemented
