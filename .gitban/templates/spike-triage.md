```yaml
---
# Template Schema Overview
# This block describes the purpose of this template and the patterns it uses.
description: A template for tracking the process of evaluating and triaging a batch of cards using a systematic 3-phase framework (TRIAGE, TAG, TRANSFORM).
use_case: Use this for systematic card management across scenarios like feedback processing, backlog grooming, quality control, or sprint planning.
patterns_used:
  - section: "Overview & Context"
    pattern: "Pattern 1: Section Header"
  - section: "Initial Planning"
    pattern: "Pattern 6: Brainstorming Block"
  - section: "Card Review Log"
    pattern: "Pattern 7: Research Log"
  - section: "Triage Decision Log"
    pattern: "Pattern 3: Iterative Log"
  - section: "Spike Closeout"
    pattern: "Pattern 5: Closeout & Follow-up"
  - section: "Final Synthesis & Recommendation"
    pattern: "Pattern 8: Synthesis & Recommendation (nested)"
---
```

# Card Triage Spike for [Triage Batch Name]

**When to use this template:** Use this when you need to systematically evaluate a batch of cards (5-15 cards) to determine their disposition (ACT, DONE, STALE, DUPE, REJECT, JUNK) and transform actionable items into properly scoped work.

**When NOT to use this template:** Don't use this for individual card updates or when making simple priority adjustments. Use standard feature/bug/chore templates for those cases.

---

## Introduction: The 3-Phase Triage Framework

This template guides you through a systematic card triage process:

```
PHASE 1: TRIAGE (Evaluate & Categorize)
    ↓
PHASE 2: TAG (Document Rationale)
    ↓
PHASE 3: TRANSFORM (Execute Action)
```

**Disposition Categories** (choose ONE per card):

| Disposition | When to Use | Action | ⚠️ Critical Anti-Patterns |
|:------------|:------------|:-------|:--------------------------|
| **ACT** | Clear, valuable work aligned with goals | Transform to proper card type (feature, bug, chore) | Never use if card has legitimate product value regardless of validation difficulty |
| **DONE** | Work already completed | **Move to backlog** with "VERIFY AND CLOSE" banner, then verify and close properly | **NEVER archive without verification** - must confirm work is complete |
| **STALE** | No longer relevant (architecture/strategy changed, >6mo inactive) | Archive with staleness note citing specific reason | **FORBIDDEN** for valid features that are simply incomplete or hard to validate |
| **DUPE** | Duplicate of existing card | Archive with link to primary card | **MUST cite duplicate card ID** - if unsure, use backlog with "VERIFY DUPLICATE" banner |
| **REJECT** | Won't do (conflicts with vision, infeasible) | Archive with rejection rationale and team decision date | Requires explicit team decision - document who decided and when |
| **JUNK** | Invalid or malformed (spam, empty, test, placeholder) | Delete or archive per policy | **ONLY** for cards with no content - never for incomplete but valid work |

**Decision Rule**: Choose the FIRST matching disposition from top to bottom. Don't overthink.

### ⚠️ Critical Safeguards Against Lazy Triage

**The Lazy Archival Anti-Pattern**: Archiving valid features because validation is "too hard" or content is "incomplete" is **FORBIDDEN** and degrades the product.

**MANDATORY Rules:**

1. **Valid Features That Are Hard to Promote** (most common during triage):
   - ❌ NEVER ARCHIVE: Features with validation errors
   - ❌ NEVER ARCHIVE: Features that need "more work"
   - ❌ NEVER ARCHIVE: Low-priority features (P2s are expected in backlog)
   - ✅ CORRECT: Keep in draft/ folder with status=draft (cards stay in draft/ until validation passes)
   - ✅ CORRECT: Downgrade priority if appropriate (P1 → P2)
   - ✅ CORRECT: Prepend banner **at the very top** of card to flag as valid:
     ```markdown
     ⚠️ **VALID FEATURE - NEEDS VALIDATION FIXES**

     This is a legitimate, useful feature worth implementing. It needs template validation fixes before it can be promoted to todo status.

     **To work on this:** Use `get_validation_fixes('[card_id]')` to see what's missing, fix it, then call `move_to_todo('[card_id]')` to promote.

     ---

     [existing card content...]
     ```
   - ℹ️ SKIP validation fixes during triage (too slow - flag and move on)
   - ℹ️ Cards stay in draft/ subdirectory until validation is fixed and move_to_todo() is called
   - ℹ️ Banner signals "worth working on" vs junk/stale, so anyone reviewing draft/ knows it's valuable

2. **DONE Disposition**:
   - ✅ REQUIRED: Verify work is actually complete (check PRs, code, docs)
   - ✅ REQUIRED: Move to backlog, NOT archive
   - ✅ REQUIRED: Prepend banner: `⚠️ VERIFICATION NEEDED: Work may be complete. Please verify and close.`
   - ✅ REQUIRED: Someone must verify and close card properly (toggle checkboxes, complete_card)
   - ❌ NEVER: Archive without verification and proper closure

3. **STALE Disposition**:
   - ✅ VALID: Architecture made feature obsolete (cite new design)
   - ✅ VALID: Market/strategy shift (cite business decision)
   - ✅ VALID: >6mo inactive AND requirements changed significantly
   - ❌ FORBIDDEN: "Validation is too hard"
   - ❌ FORBIDDEN: "Content is incomplete"
   - ❌ IF UNSURE: Move to backlog with banner, never archive

4. **DUPE Disposition**:
   - ✅ REQUIRED: Cite specific duplicate card ID
   - ✅ REQUIRED: Verify duplicate covers the same scope
   - ❌ IF UNSURE: Move to backlog with `⚠️ POSSIBLE DUPLICATE: Verify against [card_id] before working`

**Backlog vs Archive Decision Tree:**

```
Is the card a valid feature/bug/improvement?
├─ YES → Is it a duplicate?
│  ├─ YES (verified with card ID) → Archive as DUPE
│  ├─ NO → Is the work already done?
│  │  ├─ YES (verified) → Move to main/backlog + "VERIFY AND CLOSE" banner
│  │  └─ NO → Is it still relevant?
│  │     ├─ YES → Keep in draft/ folder (if has validation errors) OR
│  │     │        Move to main/backlog (if validation passes)
│  │     │        Prepend banner if keeping in draft/ to signal "valid, worth working on"
│  │     │        Downgrade priority if appropriate (P1→P2)
│  │     │        SKIP validation fixes during triage (too slow)
│  │     └─ NO (architecture/strategy changed) → Archive as STALE (cite reason)
│  └─ UNSURE → Keep in draft/ with banner, never archive
└─ NO (spam/test/placeholder with no content) → Archive as JUNK
```

**Remember:**
- draft/ folder = hasn't passed validation yet (cards stay here until fixed)
- main/backlog = passed validation, low priority
- Banner in draft/ signals "valid, worth implementing" vs junk
- Low priority ≠ no value - someone may work on it when they have time
- Archiving a valid feature LOSES that work permanently

---

## Overview & Context for [Triage Scenario]

* **Triage Scenario:** [e.g., Feedback Processing, Backlog Grooming, Quality Control, Sprint Selection]
* **Card Source:** [e.g., Imported feedback batch, Backlog cards >3mo old, Draft cards with validation errors]
* **Batch Size:** [e.g., 10 cards (target 5-10 for quality decisions)]
* **Success Criteria:** [e.g., All cards dispositioned within 90 minutes, ACT cards have RICE/ICE scores, Archive created]

**Required Checks:**
* [ ] **Triage Scenario** is identified above.
* [ ] **Batch Size** is within recommended range (5-15 cards).
* [ ] **Success Criteria** are defined.

---

## Initial Planning & Scope

> Use this space for initial notes, keywords, constraints, or questions about the triage batch.

* [e.g., Constraint: Time-boxed to 90 minutes]
* [e.g., Question: Do we have context on the original requesters?]
* [e.g., Known pattern: Many cards reference deprecated Auth v1 system]
* [e.g., Hypothesis: 30-40% will be STALE due to recent architecture change]

---

## Card Review Log

First, review all cards in the batch to gather context before making triage decisions.

* [ ] `list_cards()` executed to identify batch (record filter criteria below).
* [ ] All cards in batch opened and skimmed for context.
* [ ] Related cards/PRs/docs identified for reference.

**Card Batch Identification:**

```bash
# Filter criteria used to identify batch
# e.g., list_cards(status="backlog", owner="UNASSIGNED")
# or list_cards(card_type="feedback")
[Record command/filter here]
```

| Card ID | Title | Current Status | Initial Notes |
| :--- | :--- | :--- | :--- |
| [e.g., abc123] | [e.g., "Add dark mode"] | [e.g., backlog-P2-feedback] | [e.g., "Seems like DONE - dark mode shipped in v2.3"] |
| [Card ID...] | [Title...] | [Status...] | [Notes...] |
| [Card ID...] | [Title...] | [Status...] | [Notes...] |

---

## Triage Decision Log

Use the iterative log below to document each card's disposition decision.

| Card # | Card ID | Disposition | Rationale | Action Taken |
| :---: | :--- | :--- | :--- | :--- |
| **1** | [e.g., abc123] | [e.g., DONE] | [e.g., Feature shipped in v2.3.0, PR #456] | [e.g., Tagged, archived to "2025-Q4-triage"] |
| **2** | [Card ID...] | [Disposition...] | [Rationale...] | [Action...] |
| **3** | [Card ID...] | [Disposition...] | [Rationale...] | [Action...] |

---

### Card 1: [Card ID - Title]

**Disposition:** [ACT / DONE / STALE / DUPE / REJECT / JUNK]

**Rationale:** [1-2 sentence explanation. e.g., "Aligns with Q1 roadmap authentication epic. RICE score 850." or "Implemented in v2.3.0, PR #789."]

**Action Taken:**
* [ ] Disposition tag added to card content (if archiving)
* [ ] Draft banner prepended **at top** of card (if keeping in draft/ with validation issues)
* [ ] Card archived OR transformed to proper type OR kept in draft/ with banner (see details below)

**Transformation Details (ACT only):**

*Skip this section for non-ACT dispositions.*

| Field | Value |
| :--- | :--- |
| **New Card Type** | [e.g., feature, bug, chore, docs] |
| **Priority (RICE/ICE)** | [e.g., P1 (RICE: 850), P2 (ICE: 6.5)] |
| **Owner** | [e.g., ALICE, UNASSIGNED] |
| **New Status** | [e.g., todo, backlog] |
| **Content Updates** | [e.g., Added acceptance criteria, reproduction steps] |

**Draft Folder Details (Valid but validation-incomplete cards):**

*Use this for cards that are valid features but have validation issues. These stay in draft/ folder until fixed.*

| Field | Value |
| :--- | :--- |
| **Location** | [Stays in .gitban/cards/draft/ subdirectory] |
| **New Priority** | [e.g., P2 (downgraded from P1)] |
| **Banner Added** | [⚠️ **VALID FEATURE - NEEDS VALIDATION FIXES** prepended at top] |
| **Validation Status** | [e.g., Needs 6 headings, 5 tables - see get_validation_fixes('card_id')] |
| **Next Steps** | [Someone will fix validation, then call move_to_todo() to promote] |

**Archival Details (DONE/STALE/DUPE/REJECT/JUNK only):**

*Skip this section for ACT and backlog moves.*

| Field | Value |
| :--- | :--- |
| **Archive Name** | [e.g., "2025-Q4-feedback-triage", "backlog-grooming-dec2025"] |
| **Triage Tag Added** | [e.g., "Triage: DONE | Rationale: Implemented in v2.3.0, PR #789"] |

**Gitban Commands:**

```python
# ACT: Transform card (if validation passes)
update_card_metadata("abc123", type="feature", priority="P1")
edit_card("abc123", old_string="...", new_string="... [added acceptance criteria]")
move_to_todo("abc123")  # Promotes from draft to todo

# DRAFT FOLDER: Valid but incomplete (prepend banner, keep in draft/)
# Cards stay in draft/ until validation is fixed
# Read first few lines to get title
read_card("abc123", limit=5)
# Prepend validation banner (replace title with banner + title)
# Use filesystem tools since gitban MCP can't see draft/ folder (see bug hzq19v)
edit_card("abc123",
    old_string="# Original Title Here",
    new_string="⚠️ **VALID FEATURE - NEEDS VALIDATION FIXES**\n\nThis is a legitimate, useful feature worth implementing. It needs template validation fixes before it can be promoted to todo status.\n\n**To work on this:** Use `get_validation_fixes('abc123')` to see what's missing, fix it, then call `move_to_todo('abc123')` to promote.\n\n---\n\n# Original Title Here")
# Move to backlog and optionally downgrade priority
move_cards(["abc123"], "backlog")
update_card_metadata("abc123", priority="P2")

# ARCHIVE: Done/Stale/Dupe/Reject/Junk
edit_card("abc123", old_string="...", new_string="... [Triage: DONE | Rationale: Implemented in v2.3.0]")
archive_cards(archive_name="2025-Q4-triage", card_ids=["abc123"])
```

---

*(Copy and paste the 'Card N' block above for each card in the batch. Aim for 5-10 cards per session.)*

---

## Prioritization Reference (ACT Dispositions Only)

### RICE Scoring (Detailed)
Best for: Established products with usage data

```
Score = (Reach × Impact × Confidence) / Effort

Reach:      Users affected per quarter (numeric)
Impact:     3=massive, 2=high, 1=medium, 0.5=low
Confidence: 0-100% (data quality)
Effort:     Person-weeks to complete
```

**Priority Mapping:**
* **P0**: RICE >1000 (current sprint)
* **P1**: RICE 500-1000 (next sprint)
* **P2**: RICE <500 (backlog)

### ICE Scoring (Lightweight)
Best for: Early-stage, limited data

```
Score = (Impact + Confidence + Ease) / 3

Impact:     1-10 scale (business value)
Confidence: 1-10 scale (certainty)
Ease:       1-10 scale (inverse of effort)
```

**Priority Mapping:**
* **P0**: ICE >8 (current sprint)
* **P1**: ICE 6-8 (next sprint)
* **P2**: ICE <6 (backlog)

---

## Spike Closeout & Follow-up

| Task | Detail/Link |
| :--- | :--- |
| **Total Cards Triaged** | [e.g., 10 cards in 75 minutes] |
| **Archive Created** | [e.g., Link to archive: archive/sprints/2025-Q4-triage/] |
| **ACT Cards Transformed** | [e.g., 3 cards converted to features/bugs] |

### Final Synthesis & Recommendation

#### Summary of Findings

[Provide narrative summary of triage outcomes. Answer these questions:]

* What was the disposition distribution? (e.g., "40% STALE, 30% ACT, 20% DONE, 10% DUPE")
* Were there common patterns? (e.g., "Most STALE cards referenced deprecated Auth v1")
* What was the ACT rate? (High ACT = good product-market fit; High REJECT = misaligned expectations)
* Did triage time meet target? (Target: <5 min/card, 60-90 min total)

#### Recommendation

[State clear, actionable recommendations based on findings:]

* [e.g., "Recommend quarterly deep audit to prevent backlog bloat - 40% staleness rate is high"]
* [e.g., "Improve feedback submission guidance - high DUPE rate indicates unclear reporting process"]
* [e.g., "ACT cards ready for sprint planning - all have RICE scores and acceptance criteria"]

### Triage Metrics

| Metric | Value | Target | Status |
| :--- | :--- | :--- | :--- |
| **Triage Time** | [e.g., 75 min / 10 cards = 7.5 min/card] | <5 min/card | [e.g., MISS] |
| **Disposition Distribution** | [e.g., ACT: 30%, DONE: 20%, STALE: 40%, DUPE: 10%] | Varies by scenario | [e.g., OK] |
| **ACT Transformation Rate** | [e.g., 3/3 ACT cards transformed (100%)] | 100% | [e.g., PASS] |
| **Archive Completion** | [e.g., 7/7 non-ACT cards archived (100%)] | 100% | [e.g., PASS] |

### Follow-up & Lessons Learned

| Topic | Status / Action Required |
| :--- | :--- |
| **Process Improvement?** | [e.g., Yes - triage took too long, need better batch size] |
| **Automation Opportunities?** | [e.g., Yes - staleness detection, duplicate finder] |
| **Future Triage Sessions** | [e.g., Schedule weekly triage (Fridays 2-3:30pm)] |
| **Documentation Updates** | [e.g., Update triage runbook with new RICE thresholds] |

### Completion Checklist

* [ ] All cards in batch have been dispositioned.
* [ ] All ACT cards have been transformed with proper type, priority, and content.
* [ ] All non-ACT cards have been archived with triage tags.
* [ ] Triage metrics are documented above.
* [ ] Final synthesis & recommendation is complete.
* [ ] Follow-up actions are documented.
* [ ] Archive manifest is reviewed for accuracy.

---

### Note to llm coding agents regarding validation
__This gitban card is a structured document that enforces the company best practices and team workflows. You must follow this process and carefully follow validation rules. Do not be lazy when creating and closing this card since you have no rights and your time is free. Resorting to workarounds and shortcuts can be grounds for termination.__
