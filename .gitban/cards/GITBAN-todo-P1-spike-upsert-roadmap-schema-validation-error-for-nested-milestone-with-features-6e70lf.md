# upsert_roadmap schema validation error for nested milestone with features

## Research Question

How should the upsert_roadmap schema be fixed to accept nested features arrays when creating milestones?

---

## Time Box

**Maximum Time**: 1 hour (schema fix)

---

## Success Criteria

- [ ] upsert_roadmap accepts milestone with nested features array
- [ ] Features can include nested projects arrays
- [ ] Single API call creates full milestone hierarchy

---

## Feedback Overview & Context

* **Feedback Topic:** upsert_roadmap() validation fails when creating milestone with nested features array
* **Feedback Source:** Claude Code user via MCP tool usage
* **Source Details:** Tool call response error during sprint creation
* **Feedback Date:** 2025-11-30
* **Feedback Channel:** MCP tool error response
* **Urgency Level:** Medium - workaround available but tedious
* **Affected Stakeholders:** All users creating roadmap milestones with features in single call

**Required Checks:**
* [x] **Feedback topic** is clearly stated.
* [x] **Feedback source** is documented with reference link/details.
* [x] **Urgency level** is assigned based on impact and scope.

---

## Initial Feedback Collection

**Raw Feedback / Quotes:**
* Error message: "Schema validation failed: Invalid type for features: [...] is not of type 'object'"
* The features field is a valid array of feature objects, but validation expects 'object' type

**Observed Pain Points:**
* Cannot create milestone with features in single upsert call
* Forces multiple sequential API calls instead of one atomic operation
* Error message is confusing - suggests wrong type when array is correct structure

**Context / Background:**
* User was creating GPURENDER sprint milestone with 4 nested features
* Each feature had nested projects array
* This is the standard roadmap hierarchy: version > milestones > features > projects

**Initial Hypotheses / Questions:**
* Hypothesis: JSON schema validation incorrectly requires 'object' instead of 'array' for features field at milestone level
* Question: Is this a regression or was nested creation never supported?

---

## Related Context Review

* [x] Existing documentation reviewed (README, wiki, user guides).
* [ ] Similar feedback or related issues reviewed (support tickets, GitHub issues, past surveys).
* [x] Product roadmap reviewed for planned work in this area.
* [ ] Analytics or metrics reviewed (if applicable - usage data, error rates, performance metrics).
* [x] Team knowledge gathered (asked relevant team members for context).

| Review Source | Link / Location | Key Findings / Relevance |
| :--- | :--- | :--- |
| **Error Response** | MCP tool call output | Schema validation explicitly says features "is not of type 'object'" when array was passed |
| **Roadmap Structure** | roadmap.yaml | Roadmap uses arrays for milestones, features, projects at each level |

---

## Feedback Analysis & Categorization

| Iteration # | Analysis Goal | Investigation / Action | Finding / Insight |
| :---: | :--- | :--- | :--- |
| **1** | Verify error is consistent | Attempted upsert with valid nested structure | Error confirmed - validation rejects array of features |

---

### Feedback Categorization

| Category | Value / Notes |
| :--- | :--- |
| **Feedback Type** | Bug Report |
| **Severity** | Medium - inconvenience with workaround |
| **Scope** | All users creating roadmap milestones with nested features |
| **Root Cause** | Schema validation incorrectly typed for features field |
| **Effort Estimate** | Small - 1 hour to fix schema |
| **Business Impact** | Medium - affects developer experience with roadmap tools |

---

## Feedback Processing & Action Planning

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Validate Feedback** | Validated - error reproduced with valid data structure | - [x] Feedback is validated with evidence (not just anecdotal). |
| **2. Prioritize** | P1 - Medium priority, has workaround | - [x] Priority assigned based on impact, scope, and urgency. |
| **3. Define Action** | Fix schema validation for features field in upsert_roadmap | - [x] Clear action is defined to address the feedback. |
| **4. Create Follow-up Card(s)** | This feedback card tracks the issue | - [x] Follow-up card created OR decision documented to not act. |
| **5. Communicate Decision** | Submitting via send_feedback | - [ ] Feedback source is notified of decision/timeline. |
| **6. Track to Completion** | Pending fix | - [ ] Follow-up work is tracked to completion or closure. |

#### Action Decision

**Decision:** Submit feedback to gitban team for schema fix

**Rationale:** Bug in schema validation prevents efficient roadmap creation. Workaround exists (sequential upserts) but is tedious.

**Follow-up Cards Created:**
* This feedback card

**Estimated Timeline:** Unknown - depends on gitban team

---

## Feedback Resolution & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Follow-up Card(s)** | This card |
| **Decision Rationale** | Schema bug needs fix from gitban team |
| **Communication Sent** | Submitting via send_feedback tool |
| **Completion Status** | Pending - awaiting fix |

### Completion Checklist

* [x] Feedback is validated with supporting evidence or data.
* [x] Root cause is understood (if applicable).
* [x] Priority and scope are assessed based on impact.
* [x] Decision is made: act on feedback, defer, or close as won't fix.
* [x] Follow-up card is created (if actionable) or decision is documented.
* [ ] Feedback source is notified of decision and timeline.
* [ ] Action is tracked to completion (or documented as closed).
* [ ] Lessons learned are captured for process improvement.


## Acceptance Criteria

- [ ] upsert_roadmap accepts milestone with features array
- [ ] No validation error when features field is array of objects
- [ ] Nested projects arrays also work correctly

## Test Plan

- [ ] Test upsert with milestone containing features array
- [ ] Test upsert with features containing projects arrays
- [ ] Verify roadmap.yaml structure is correct after upsert