# CMYK Accuracy Test Suite

**When to use this template:** Use this for validating that the CMYK accuracy fix works correctly across different test cases.

---

## User Testing Overview

* **Testing Focus:** CMYK pixel count accuracy after bug fix
* **Testing Type:** Accuracy validation and regression testing
* **Target Users:** Automated tests + manual verification
* **Testing Goals:** Verify rendered CMYK pixels match source within acceptable tolerance
* **Success Criteria:** All color channels within user-defined error threshold
* **Duration:** 1-2 hours for test creation and validation
* **Related Work:** CMYKFIX sprint - Bug fix card cju1m7

**Required Checks:**
* [x] **Testing focus** is clearly defined and scoped.
* [x] **Target users** are identified and recruited.
* [x] **Success criteria** are measurable and specific.

---

## Test Planning & Preparation

* [ ] Test scenarios defined (specific tasks users will perform).
* [ ] Test environment prepared (tools, accounts, data seeded).
* [ ] Test script/guide created (facilitator instructions, questions to ask).
* [ ] Observation protocol defined (what to observe, how to record).
* [x] User recruitment completed (participants confirmed, scheduled).
* [x] Consent forms prepared (if recording sessions or collecting data).
* [x] Testing tools ready (screen recording, note-taking, feedback forms).

| Preparation Item | Status / Link | Notes |
| :--- | :--- | :--- |
| **Test Scenarios** | 4 scenarios defined | Different image types and sizes |
| **Test Environment** | Local dev environment | Using pytest framework |
| **Test Script** | tests/test_cmyk_accuracy.py | New test file to create |
| **Observation Protocol** | Pixel count comparison | Expected vs actual |
| **User Recruitment** | Automated + Claude | N/A for automated tests |

---

## Test Scenarios & Tasks

| Scenario # | Scenario Description | Tasks to Complete | Success Criteria | Status |
| :---: | :--- | :--- | :--- | :---: |
| **1** | Basic CMYK halftone | Reconstitute and check accuracy | <5% error per channel | - [ ] Tested |
| **2** | High saturation colors | Test with pure cyan/magenta/yellow | <5% error per channel | - [ ] Tested |
| **3** | Edge cases - partial circles | Test clusters at image boundaries | No crashes, reasonable accuracy | - [ ] Tested |
| **4** | Regression - existing tests | All current tests still pass | 100% pass rate | - [ ] Tested |

---

## User Testing Sessions Log

| Session # | User / Profile | Scenario Tested | Observations / Issues | Outcome |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Automated pytest | All scenarios | TBD after bug fix | TBD |
| **2** | Manual verification | Visual inspection | TBD after bug fix | TBD |

---

## Findings & Recommendations

| Task | Detail/Link |
| :--- | :--- |
| **Test Sessions Completed** | TBD |
| **Scenarios Tested** | 4 scenarios planned |
| **Issues Identified** | TBD |
| **Findings Report** | Will be in test output |

### Completion Checklist

* [ ] All planned testing sessions completed.
* [ ] All scenarios tested with target users.
* [ ] Observations documented for each session.
* [ ] Issues identified and prioritized by severity.
* [ ] Findings synthesized into narrative summary.
* [ ] Recommendations are clear and actionable.
* [ ] Follow-up feature cards created for issues.
* [ ] Documentation updated based on insights.

---

## Acceptance Criteria

- [ ] test_cmyk_accuracy.py created with comprehensive tests
- [ ] All test scenarios pass after bug fix
- [ ] Error thresholds match user-defined values from card fx7toj
- [ ] No regressions in existing test suite
- [ ] Tests are automated and repeatable

## Test Plan

### Test Implementation

1. **Create test_cmyk_accuracy.py**:
   - [ ] Test sum(cluster.cyan) == source_cyan_decomposed
   - [ ] Test rendered pixels match expected within threshold
   - [ ] Test edge clusters handled correctly
   - [ ] Test various image sizes

2. **Run full test suite**:
   - [ ] pytest tests/test_cmyk_accuracy.py
   - [ ] pytest tests/ (full regression)

3. **Manual verification**:
   - [ ] Visual inspection of reconstituted images
   - [ ] Confirm no obvious artifacts
