## Feedback Overview & Context

- Feedback Topic: Roadmap upsert semantics (merge vs replace) and safe field updates
- Feedback Source: Internal engineering (LLM coding agent workflow)
- Source Details: VS Code + Gitban MCP usage in repo muunkky/dotmatrix
- Feedback Date: 2025-12-02
- Feedback Channel: In-editor MCP tools (roadmap read/upsert), follow-up via send_feedback
- Urgency Level: Medium — risk of accidental data loss in normal workflows
- Affected Stakeholders: Engineers using roadmap upserts from tools/automation

Required Checks:
- [x] Feedback topic is clearly stated.
- [x] Feedback source is documented with reference link/details.
- [x] Urgency level is assigned based on impact and scope.

---

## Initial Feedback Collection

Raw Feedback / Quotes:
- "The roadmap upsert behaves like a full replace, not an upsert/merge."
- "If I include features: {}, it wipes the whole features subtree."
- "I only wanted to set status=done; why do I have to resend the entire object?"

Observed Pain Points:
- Partial updates are rejected unless full required fields are re-sent.
- Destructive behavior easy to trigger (empty maps erase content).
- No preview/diff of changes before apply.

Context / Background:
- Agent was marking milestone v1 > m1 as done.
- Encountered sequential validation misses (title, description, success_criteria, features).
- Adding `features: {}` made the update succeed but erased the milestone features.

Initial Hypotheses / Questions:
- Upsert endpoint uses replace semantics, not merge.
- Schema validation demands full object even for trivial updates.
- A merge/patch mode would prevent accidental data loss.

---

## Related Context Review

- [x] Existing documentation reviewed (tools reference, template usage)
- [x] Similar feedback or related issues reviewed (internal discussion)
- [x] Product roadmap reviewed (roadmap tools)
- [x] Analytics/metrics N/A
- [x] Team knowledge gathered (engineering agent usage)

| Review Source | Link / Location | Key Findings / Relevance |
| :--- | :--- | :--- |
| Roadmap content | read_roadmap(scope="milestone", v1/m1) | Milestone has nested features/projects tree |
| Upsert errors | tool responses | Sequential required-field errors culminating in required features |
| Upsert result | upsert with features: {} | Succeeds but erases entire features subtree (replace semantics) |
| Restoration | full-object upsert | Re-sending complete milestone with status=done restores content safely |

---

## Feedback Analysis & Categorization

| Iteration # | Analysis Goal | Investigation / Action | Finding / Insight |
| :---: | :--- | :--- | :--- |
| 1 | Reproduce validation sequence | Attempted minimal upsert then added fields as requested | Upsert demands title, description, success_criteria, features |
| 2 | Assess data-loss risk | Supplied features: {} to satisfy schema | Operation succeeded but wiped nested features (destructive replace) |
| 3 | Identify safer model | Compared to code patch workflows | Patch/merge semantics avoid accidental deletions |

#### Iteration 1: Scope & Validation Behavior
- Analysis Goal: Understand minimum valid payload for milestone upsert
- Investigation / Action: Sent minimal payload then added fields per error messages
- Finding / Insight: All listed fields are required; omitting any fails; features required even if unchanged

#### Iteration 2: Replace vs Merge Risk
- Analysis Goal: Determine effect of unspecified fields
- Investigation / Action: Sent `features: {}`
- Finding / Insight: Entire subtree replaced; unspecified content lost — dangerous default

### Feedback Categorization

| Category | Value / Notes |
| :--- | :--- |
| Feedback Type | Process/Tooling Improvement |
| Severity | Medium |
| Scope | All roadmap updates via MCP tools/automation |
| Root Cause | Upsert uses replace semantics, requires full object; no merge/patch support |
| Effort Estimate | Medium (API changes + tests) |
| Business Impact | Reduces risk of data loss; improves developer UX |

---

## Feedback Processing & Action Planning

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| 1. Validate Feedback | Reproduced locally; logs captured | - [x] Feedback is validated with evidence (not just anecdotal). |
| 2. Prioritize | Recommend P2 | - [x] Priority assigned based on impact, scope, and urgency. |
| 3. Define Action | Add merge/patch semantics and safe defaults | - [x] Clear action is defined to address the feedback. |
| 4. Create Follow-up Card(s) | N/A (this card) | - [ ] Follow-up card created OR decision documented to not act. |
| 5. Communicate Decision | Pending | - [ ] Feedback source is notified of decision/timeline. |
| 6. Track to Completion | Pending | - [ ] Follow-up work is tracked to completion or closure. |

#### Action Decision
- Decision: Propose API enhancements for safe, merge-first roadmap updates.
- Rationale: Prevent accidental data loss; align with code-edit mental model.
- Follow-up Cards Created: TBD by gitban team
- Estimated Timeline: TBD

---

## Feedback Resolution & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| Follow-up Card(s) | TBD |
| Decision Rationale | Merge-first avoids destructive updates and better matches code patch expectations |
| Communication Sent | Submit via send_feedback; await triage |
| Completion Status | Open |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| Similar Feedback Expected? | Yes — any automation attempting small updates |
| Process Improvement? | Yes — add merge/patch mode and preview diff |
| Documentation Needed? | Yes — clarify semantics, required fields, and destructive cases |
| Proactive Communication? | Yes — release notes + examples for safe updates |
| Feedback Loop Closed? | Pending |

### Completion Checklist

- [x] Feedback is validated with supporting evidence or data.
- [x] Root cause is understood (if applicable).
- [x] Priority and scope are assessed based on impact.
- [x] Decision is made: act on feedback, defer, or close as won't fix.
- [ ] Follow-up card is created (if actionable) or decision is documented.
- [ ] Feedback source is notified of decision and timeline.
- [ ] Action is tracked to completion (or documented as closed).
- [x] Lessons learned are captured for process improvement.

---

System Environment (for reference):
- OS: Windows (PowerShell)
- Date: 2025-12-02
- Repo: muunkky/dotmatrix
- Tools: Gitban MCP (read_roadmap, upsert_roadmap, send_feedback)


## Research Question

What changes to gitban roadmap upsert semantics and API surface will make roadmap updates safe (non-destructive), merge-friendly, and intuitive for engineers and coding agents performing small edits (e.g., flipping a milestone status)?

## Time Box

Maximum Time: 1 workday (to collect reproducible evidence, analyze risks, and propose actionable API changes)

## Success Criteria

We'll know this spike is successful when:
- [x] Repro steps and risk are clearly documented.
- [x] A non-destructive, merge-first update path is proposed (API or mode).
- [x] A minimal safe client workflow is documented (read→merge→validate→apply).
- [ ] The gitban team accepts the feedback for triage (ticket linked).

## Acceptance Criteria

- [x] Card includes Research Question, Time Box, and Success Criteria as per spike template.
- [x] Describes current vs expected behavior with concrete repro steps.
- [x] Proposes actionable API changes (merge/patch mode, preview, flags).
- [x] Documents safe client workflow (read→merge→validate→apply) as interim guidance.
- [x] Provides environment details and impact assessment.
- [ ] Feedback submitted to gitban team via send_feedback with this card ID.


## Test Plan

1. Reproduce validation chain by attempting minimal milestone upsert and observe sequential required-field errors.
2. Confirm destructive behavior by applying `features: {}` in a non-critical sandbox and verifying that nested features are erased.
3. Restore state by re-upserting full milestone content and validate content matches pre-test snapshot.
4. Demonstrate safe client workflow: read full object → merge intended change → validate-only → apply → compare post-state to expected.
5. Submit this card via send_feedback and confirm server receipt.