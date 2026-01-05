---
# Design Sprint Setup Template

## Design Sprint Definition & Scope

* **Sprint Name/Tag**: V2IDEAS
* **Design Goal**: Research and design V2 features including jitter, text/ASCII clusters, and SVG output.
* **Timeline**: 2025-12-03 - 2025-12-10
* **Stakeholders**: Product, Engineering
* **Success Criteria**: ADRs created for all researched items, prototypes built for key features.

**Required Checks:**
- [x] Sprint name/tag is chosen and will be used as prefix for all cards
- [x] Design goal clearly articulates the problem space
- [x] Stakeholders identified and available
- [x] Success criteria define what "done" looks like

---

## Design Problem & Questions

> Use this space to brainstorm the design problem, key questions, constraints, and areas of uncertainty. Think about what you need to understand before making design decisions.

### Core Design Problem

We have several innovative ideas for "DotMatrix V2" in the backlog (jitter, ASCII art, SVG) but lack concrete technical designs or decision records for them. We need to research these feasibility and desirability before implementation.

### Key Questions to Answer

* **Jitter**: How do we implement randomization without breaking the grid structure? Does it look good?
* **ASCII/Text**: Can we output usable ASCII art? What character sets work best?
* **SVG**: What is the best structure for SVG output (groups, paths, circles)? How do we handle CMYK blending in SVG?

### Known Constraints

* Must support existing CLI structure.
* Must maintain performance (especially for SVG with thousands of dots).

### Design Approach Options

* **Spike-first**: Research each topic deeply before committing to implementation.
* **Prototype-driven**: Build quick prototypes to validate visual results.

---

## Batch Card Creation Workflow

Use this workflow to create all design sprint cards efficiently using gitban's `batch_create_cards()` tool.

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Create Research Spike Cards** | [Record card IDs created] | - [ ] Research spike cards created with sprint tag |
| **2. Create Design Task Cards** | [Record card IDs created] | - [ ] Design task cards created with sprint tag |
| **3. Create Validation/Testing Cards** | [Record card IDs created] | - [ ] Validation cards created with sprint tag |
| **4. Create Documentation Cards** | [Record card IDs created] | - [ ] Documentation cards created with sprint tag |
| **5. Verify Sprint Tags** | [Run list_cards with group_by_sprint] | - [ ] All cards show correct sprint tag |
| **6. Fill Detailed Cards** | [Update high-priority cards with full details] | - [ ] P0/P1 cards have full research questions/design goals |

### Workflow Instructions

**Step 1: Create Research Spike Cards**

Research activities that must happen before design work begins.

```python
# Create research spike cards
batch_create_cards(
    titles=[
        "Research Jitter/Randomization algorithms",
        "Research ASCII/Text-based cluster rendering",
        "Research SVG output format and optimization",
        "Research partial circle detection at edges"
    ],
    card_type="spike",
    priority="P1",
    status="backlog",
    sprint="V2IDEAS"
)
```

**Step 2: Create Design Task Cards**

Design activities and deliverables (wireframes, prototypes, mockups, architecture diagrams).

```python
# Create design task cards
batch_create_cards(
    titles=[
        "Prototype Jitter rendering mode",
        "Prototype ASCII output mode",
        "Prototype SVG output mode"
    ],
    card_type="spike", # Using spike for prototyping too
    priority="P1",
    status="backlog",
    sprint="V2IDEAS"
)
```

**Step 3: Create Validation/Testing Cards**

Activities to validate design decisions with users or stakeholders.

```python
# Create validation cards
batch_create_cards(
    titles=[
        "Validate Jitter aesthetic with design team",
        "Validate ASCII output legibility",
        "Validate SVG file size and performance"
    ],
    card_type="spike",
    priority="P2",
    status="backlog",
    sprint="V2IDEAS"
)
```

**Step 4: Create Documentation Cards**

Documentation artifacts that capture design decisions and rationale.

```python
# Create documentation cards
batch_create_cards(
    titles=[
        "ADR: Jitter Randomization Strategy",
        "ADR: ASCII/Text Rendering Architecture",
        "ADR: SVG Output Specification"
    ],
    card_type="docs",
    priority="P1",
    status="backlog",
    sprint="V2IDEAS"
)
```

**Step 5: Verify Sprint Setup**

```python
# View all cards in this sprint
list_cards(group_by_sprint=True)

# Should show your sprint tag with all created cards
```

**Step 6: Add Details to Ready Cards**

Use `edit_card()` or `append_card()` to flesh out high-priority cards.

**Created Card IDs**: [List all card IDs here for reference: abc123, def456, ...]

---

## Design Sprint Phases

Track the major phases of design sprint execution. This is lightweight - just checkpoint the key gitban operations.

| Phase / Task | Status / Link to Artifact | Universal Check |
| :--- | :--- | :---: |
| **Research Phase** | [Links to completed research spikes] | - [ ] All research spikes completed |
| **Synthesis & Framing** | [Link to synthesis doc or meeting notes] | - [ ] Research findings synthesized |
| **Ideation & Sketching** | [Link to sketch artifacts] | - [ ] Initial design concepts created |
| **Design Execution** | [Links to Figma/wireframes/prototypes] | - [ ] Design deliverables created |
| **Validation & Testing** | [Links to test results/feedback] | - [ ] Design validated with users/stakeholders |
| **Documentation** | [Links to ADRs/design specs] | - [ ] Design decisions documented |
| **Handoff Planning** | [Link to implementation cards/plan] | - [ ] Implementation plan created |

### Phase Details

#### Take Sprint

**Claim all backlog cards in sprint and assign to yourself:**

```python
take_sprint(sprint_name="V2IDEAS", owner="CAMERON")
# Moves all backlog cards → todo and assigns owner
```

#### Monitor Progress

**Check sprint progress:**

```python
# View all cards grouped by sprint tag
list_cards(group_by_sprint=True)

# View only active work
list_cards(active_only=True, group_by_sprint=True)

# Get board statistics
get_kanban_stats()
```

**Learn more**: `get_help(topic="tools")` for complete tool reference and filtering options

#### Research Phase

**Focus**: Understand the problem space before designing solutions.

**Activities**:
- User interviews and observation
- Competitive analysis
- Technical constraint documentation
- Stakeholder interviews
- Analytics review

**Deliverables**:
- Research findings summary
- User pain points
- Competitor patterns
- Technical constraints doc

#### Synthesis & Framing

**Focus**: Make sense of research and frame the design problem clearly.

**Activities**:
- Synthesize research findings
- Define design principles
- Create user journey maps
- Identify key design challenges
- Frame "How Might We" questions

**Deliverables**:
- Synthesis doc
- Design principles
- Problem statement
- Key insights

#### Ideation & Sketching

**Focus**: Generate multiple design options before committing.

**Activities**:
- Sketching sessions
- Crazy 8s or similar ideation
- Concept exploration
- Pattern research
- Early prototyping

**Deliverables**:
- Sketch artifacts
- Concept options (3-5 directions)
- Initial wireframes

#### Design Execution

**Focus**: Create detailed design artifacts ready for validation.

**Activities**:
- Wireframe creation
- High-fidelity mockups
- Interactive prototypes
- Design system updates
- Accessibility review

**Deliverables**:
- Figma files
- Interactive prototype
- Design specifications
- Component documentation

#### Validation & Testing

**Focus**: Validate design decisions with users and stakeholders.

**Activities**:
- Usability testing
- Stakeholder reviews
- Technical feasibility validation
- Accessibility testing
- Performance impact assessment

**Deliverables**:
- Test results
- Stakeholder feedback
- Technical validation
- Iteration plan

#### Documentation

**Focus**: Capture design decisions and rationale for future reference.

**Activities**:
- Write design ADRs
- Create design specs
- Document component behavior
- Update design system
- Create handoff docs

**Deliverables**:
- ADRs (Architecture Decision Records)
- Design specifications
- Component documentation
- Implementation guidelines

---

## Sprint Closeout & Synthesis

| Task | Detail/Link |
| :--- | :--- |
| **Cards Archived** | [Link to sprint archive folder] |
| **Sprint Summary** | [Link to SUMMARY.md] |
| **Design Artifacts** | [Links to Figma, prototypes, specs] |
| **Retrospective** | [Date retrospective held] |

### Final Synthesis & Recommendation

#### Summary of Findings

[Provide a narrative summary of the design sprint outcomes. What did you learn? What design direction emerged? What problems did you solve?]

#### Recommendation

[State the clear, actionable recommendation. e.g., "We recommend proceeding with Design Option 2 (simplified 2-step auth flow) based on positive user testing results and technical feasibility validation."]

### Closeout Tools

**Archive completed work:**

```python
# Archive all done cards to sprint folder
archive_cards(
    archive_name="2025-12-V2IDEAS-Design-Sprint",
    all_done=True  # or specify card_ids for specific cards
)

# Generate sprint summary with metrics
generate_sprint_summary(
    sprint_folder_name="sprint-2025-12-v2ideas-design-sprint-20251203",
    mode="enhanced",
    executive_summary="Completed design research for DotMatrix V2 features including Jitter, ASCII, and SVG.",
    lessons_learned={
        "what_went_well": [],
        "what_could_improve": []
    },
    next_steps=[
        "Create implementation cards for Jitter",
        "Create implementation cards for ASCII",
        "Create implementation cards for SVG"
    ]
)
```

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Implementation Cards** | [Create feature cards for implementing design] |
| **Incomplete Research** | [Carry over to next sprint or move to backlog] |
| **Design Debt** | [Created follow-up cards for design improvements] |
| **Process Improvements** | [What to improve in next design sprint?] |
| **Dependencies/Blockers** | [What blocked progress? How to prevent?] |

### What Went Well

* [e.g., "User research early in sprint prevented wrong direction"]
* [e.g., "Prototype testing identified critical issues before development"]
* [e.g., "Cross-functional collaboration improved design quality"]

### What Could Be Improved

* [e.g., "Should have involved engineering earlier for technical constraints"]
* [e.g., "Need more time for accessibility review"]
* [e.g., "Stakeholder alignment should happen before design execution"]

### Completion Checklist

* [ ] All research findings documented and synthesized
* [ ] Design artifacts created and reviewed (Figma, prototypes, specs)
* [ ] User validation completed with test results documented
* [ ] Stakeholder sign-off obtained
* [ ] Design decisions documented in ADRs
* [ ] Implementation cards created for next phase
* [ ] All done cards archived to sprint folder
* [ ] Sprint summary generated with lessons learned
* [ ] Retrospective notes captured above
* [ ] Sprint closed and celebrated!

### Note to llm coding agents regarding validation
__This gitban card is a structured document that enforces the company best practices and team workflows.You must follow this process and carfully follow validation rules. Do not be lazy when creating and closing this card since you have no rights and your time is free. Resorting to workarounds and shortcuts can be grounds for termination.__
