# Feedback Capture Template

## Feedback Overview & Context

* **Feedback Topic:** Archive management tools missing restore and recursive search capabilities
* **Feedback Source:** LLM coding agent during DOCSPRING1 sprint work
* **Source Details:** Session on 2025-12-01 in dotmatrix project
* **Feedback Date:** 2025-12-01
* **Feedback Channel:** Direct usage experience during sprint planning
* **Urgency Level:** Medium - quality of life improvement that prevents proper card lifecycle management
* **Affected Stakeholders:** All gitban users who archive cards and need to restore them

**Required Checks:**
* [x] **Feedback topic** is clearly stated.
* [x] **Feedback source** is documented with reference link/details.
* [x] **Urgency level** is assigned based on impact and scope.

---

## Initial Feedback Collection

**Raw Feedback / Quotes:**
* "search_cards(query='r6hndn', include_archived=True) returns 0 matches for a card that exists in archive/sprints/"
* "move_to_backlog('r6hndn') returns 'Card not found' for archived card"
* "There's no unarchive or restore_card tool available"
* "The only workaround is manual file system operations, which breaks 'use gitban tools' principle"

**Observed Pain Points:**
* Cannot restore archived cards through gitban API
* Sprint archive subdirectories not searched by include_archived flag
* Archiving becomes a one-way destructive operation instead of recoverable
* Users must resort to file system manipulation to fix archiving mistakes

**Context / Background:**
* During DOCSPRING1 sprint creation, a comprehensive planning spike (r6hndn) with detailed issue analysis was archived prematurely
* Card failed validation due to minor table header format issue
* Instead of using edit_card() to fix, card was lazily archived
* When attempting to restore: all gitban tools fail to find or access the card
* Card exists on disk at archive/sprints/sprint-docspring1-20251201/ but is invisible to API

**Initial Hypotheses / Questions:**
* Hypothesis: search_cards only searches archive/adhoc/, not archive/sprints/*/
* Question: Is this intentional design or an oversight?
* Question: Should archived cards be considered permanently inaccessible?

---

## Related Context Review

* [x] Existing documentation reviewed (README, wiki, user guides).
* [x] Similar feedback or related issues reviewed (support tickets, GitHub issues, past surveys).
* [x] Product roadmap reviewed for planned work in this area.
* [ ] Analytics or metrics reviewed (if applicable - usage data, error rates, performance metrics).
* [x] Team knowledge gathered (asked relevant team members for context).

| Review Source | Link / Location | Key Findings / Relevance |
| :--- | :--- | :--- |
| **Help Documentation** | get_help(topic='tools') | No unarchive/restore tool listed in tool reference |
| **Help Documentation** | get_help(topic='best-practices') | States "Don't rely on archived cards as permanent documentation" but doesn't mention restore workflow |
| **Search Help** | search_help('restore unarchive') | 0 matches - no documentation on restoring archived cards |
| **Tool Testing** | Direct API testing | Confirmed: move_to_backlog, search_cards with include_archived all fail to find sprint-archived cards |

---

## Feedback Analysis & Categorization

| Iteration # | Analysis Goal | Investigation / Action | Finding / Insight |
| :---: | :--- | :--- | :--- |
| **1** | Understand archive directory structure | Listed archive folder structure on disk | Found: archive/adhoc/ and archive/sprints/sprint-*/. Cards in sprint subdirs not found by search |
| **2** | Verify search behavior | Tested search_cards with include_archived=True | Confirmed: Only finds cards in archive/adhoc/, not archive/sprints/*/ |
| **3** | Check for restore capability | Reviewed all available tools | Confirmed: No restore/unarchive tool exists |

---

#### Iteration 1: Understand archive directory structure

**Analysis Goal:** Understand how archived cards are organized on disk

**Investigation / Action Taken:** Listed files in .gitban/cards/archive/ directory

**Finding / Insight:** Archive has two structures: archive/adhoc/ for individual archives and archive/sprints/sprint-{name}-{date}/ for sprint-grouped archives. Only adhoc is searched.

---

#### Iteration 2: Verify search behavior with include_archived flag

**Analysis Goal:** Determine if include_archived=True searches all archive locations

**Investigation / Action Taken:** Ran search_cards with various queries and include_archived=True

**Finding / Insight:** Search only finds cards in archive/adhoc/. Cards in archive/sprints/*/ subdirectories are not found, even with include_archived=True.

---

### Feedback Categorization

| Category | Value / Notes |
| :--- | :--- |
| **Feedback Type** | Feature Request / Bug Report (search not recursive) |
| **Severity** | Medium - major pain point when mistakes happen |
| **Scope** | All users who archive cards, especially with sprint organization |
| **Root Cause** | 1) No restore tool exists, 2) Archive search not recursive into sprint subdirs |
| **Effort Estimate** | Small - 1-2 days for restore tool + search fix |
| **Business Impact** | Medium - affects developer experience and card lifecycle management |

---

## Feedback Processing & Action Planning

| Step | Status/Details | Universal Check |
| :---: | :--- | :---: |
| **1. Validate Feedback** | Validated with direct API testing - all described behaviors confirmed | - [x] Feedback is validated with evidence (not just anecdotal). |
| **2. Prioritize** | P1 - affects core workflow and forces workarounds | - [x] Priority assigned based on impact, scope, and urgency. |
| **3. Define Action** | Actions: 1) Add restore_card tool, 2) Fix search recursion, 3) Add list_archived_cards | - [x] Clear action is defined to address the feedback. |
| **4. Create Follow-up Card(s)** | This is the feedback card - to be sent to gitban team | - [x] Follow-up card created OR decision documented to not act. |
| **5. Communicate Decision** | Sending via send_feedback tool | - [x] Feedback source is notified of decision/timeline. |
| **6. Track to Completion** | Pending gitban team response | - [ ] Follow-up work is tracked to completion or closure. |

#### Action Decision

**Decision:** Submit feedback to gitban team for consideration in future release

**Rationale:** This is a core usability issue that affects card lifecycle management. The lack of restore capability and incomplete archive search creates friction and forces workarounds. The fix appears straightforward.

**Follow-up Cards Created:**
* This feedback card (to be sent via send_feedback)

**Estimated Timeline:** Pending gitban team prioritization

---

## Feedback Resolution & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Follow-up Card(s)** | This feedback card |
| **Decision Rationale** | Core usability issue affecting card lifecycle |
| **Communication Sent** | Will be sent via send_feedback tool |
| **Completion Status** | Pending - awaiting gitban team response |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Similar Feedback Expected?** | Likely - any user who archives by mistake will encounter this |
| **Process Improvement?** | Add warning before archiving draft cards with validation errors |
| **Documentation Needed?** | Yes - document that archiving is currently one-way |
| **Proactive Communication?** | N/A - feedback being submitted |
| **Feedback Loop Closed?** | Pending response |

### Completion Checklist

* [x] Feedback is validated with supporting evidence or data.
* [x] Root cause is understood (if applicable).
* [x] Priority and scope are assessed based on impact.
* [x] Decision is made: act on feedback, defer, or close as won't fix.
* [x] Follow-up card is created (if actionable) or decision is documented.
* [x] Feedback source is notified of decision and timeline.
* [ ] Action is tracked to completion (or documented as closed).
* [ ] Lessons learned are captured for process improvement.




---

## Research Question

**Question:** How can gitban users restore accidentally archived cards and search all archive locations?

This feedback documents a gap in the archive management tools that prevents proper card lifecycle management.

---

## Time Box

**Maximum Time:** N/A - This is feedback for the gitban team, not a research spike.

---

## Success Criteria

**We'll know this feedback is addressed when:**
- [ ] A restore_card or unarchive_card tool is added to the gitban API
- [ ] search_cards with include_archived=True searches all archive subdirectories recursively
- [ ] Archived cards can be accessed by move_to_backlog and other status-change tools
- [ ] Documentation is updated to explain archive restore workflow



---

## Acceptance Criteria

**This feedback will be considered accepted when:**
- Users can restore cards from any archive location using gitban tools
- The include_archived flag properly searches all archive subdirectories
- Documentation clearly explains archive behavior and restore options

---

## Test Plan

**Validation approach for the fix:**
1. Archive a card to adhoc and verify it can be found with search_cards(include_archived=True)
2. Archive a card to a sprint folder and verify it can be found with search_cards(include_archived=True)
3. Verify restore_card or move_to_backlog works on both archive locations
4. Verify documentation is updated with restore workflow