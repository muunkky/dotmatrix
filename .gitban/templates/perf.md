
## Performance Issue

[Description of performance problem and its impact on users or system - REQUIRED]

**Value**: [Why optimizing this matters - user experience, cost savings, scalability]

**Estimated Effort**: [Time estimate - e.g., 4-8 hours, 2-3 days]

---

## Current Performance

[Quantified measurements of current performance]

### Primary Metric

- **Metric**: [Response time / throughput / memory usage / etc.]
- **Current Value**: [Current measurement - e.g., 500ms, 2GB RAM]
- **Target Value**: [Target measurement - e.g., 200ms, 1GB RAM]
- **Improvement Goal**: [X% faster / Y% less memory / etc.]

### Supporting Metrics

- **Metric 2**: [Current value]
- **Metric 3**: [Current value]

### Performance Impact

**User Impact**:
- **Severity**: [Critical / High / Medium / Low]
- **Frequency**: [Always / Under load / Specific scenarios]
- **Affected Users**: [All users / Power users / Specific use case]

**System Impact**:
- **Resource Usage**: [CPU / Memory / Disk / Network]
- **Scalability**: [Limits growth / Costs money / Blocks features]
- **Reliability**: [Causes timeouts / Crashes / Errors]

---

## Root Cause

[Analysis of what's causing the performance issue]

### Investigation Findings

[What profiling/analysis revealed]

- **Hot Spot 1**: [Code location and what it does]
  - `[file:line]`: [Description]
  - **Time Spent**: [X% of total / Y seconds]

- **Hot Spot 2**: [Code location]
  - `[file:line]`: [Description]
  - **Time Spent**: [X% of total / Y seconds]

### Performance Bottleneck

[Primary cause of slowdown]

- **Type**: [Algorithm complexity / N+1 queries / Memory allocation / Network I/O / etc.]
- **Location**: [Where in code]
- **Trigger**: [What causes this to be slow]

### Profiling Data

```
[Profiling output showing hot spots]
```

### Why This Is Slow

[Technical explanation of root cause]

- [Explanation of inefficiency]
- [What could be better]

---

## Optimization Approach

[Strategy for improving performance]

### High-Level Strategy

[Overall approach to optimization]

- **Approach**: [Algorithm change / Caching / Batch processing / Async / etc.]
- **Expected Improvement**: [X% faster]
- **Complexity**: [Simple / Medium / Complex]
- **Risk**: [Low / Medium / High]

### Specific Optimizations

1. **[Optimization 1]**: [Description]
   - **Technique**: [What optimization technique]
   - **Expected Impact**: [How much improvement]
   - **Risk**: [Potential issues]

2. **[Optimization 2]**: [Description]
   - **Technique**: [What optimization technique]
   - **Expected Impact**: [How much improvement]
   - **Risk**: [Potential issues]

### Code Changes

**Before (slow):**
```[language]
[Current slow code]
```

**After (optimized):**
```[language]
[Optimized code]
```

**Explanation**: [Why new code is faster]

---

## Implementation

[Step-by-step optimization plan]

### Phase 1: Baseline & Setup

1. **Establish Baseline**:
   - [ ] Capture current performance metrics
   - [ ] Document test scenarios
   - [ ] Set up benchmarking harness
   - [ ] Identify representative workloads

### Phase 2: Optimization

2. **[Optimization 1]**:
   - [ ] Implement optimization
   - [ ] Measure impact
   - [ ] Verify correctness
   - [ ] Document changes

3. **[Optimization 2]**:
   - [ ] Implement optimization
   - [ ] Measure impact
   - [ ] Verify correctness
   - [ ] Document changes

### Phase 3: Validation

4. **Final Validation**:
   - [ ] Run full benchmark suite
   - [ ] Verify all tests pass
   - [ ] Measure production impact
   - [ ] Update documentation

---

## Benchmarking

[Measuring performance improvements]

### Benchmark Setup

**Tool**: [pytest-benchmark / criterion / JMH / k6 / etc.]

**Test Scenarios**:
1. [Scenario 1]: [Description of workload]
2. [Scenario 2]: [Description of workload]
3. [Scenario 3]: [Description of workload]

### Benchmark Results

**Before Optimization**:
```
[Benchmark results]
```

**After Optimization**:
```
[Benchmark results]
```

### Performance Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| [Metric 1] | [Value] | [Value] | [X%] |
| [Metric 2] | [Value] | [Value] | [Y%] |
| [Metric 3] | [Value] | [Value] | [Z%] |

### Success Criteria

- [ ] Target performance achieved: [Target metric value]
- [ ] No regression in other metrics
- [ ] Performance improvement consistent across scenarios
- [ ] Improvement verified in production-like environment

---

## Trade-offs

[What was sacrificed for performance]

### Code Complexity

- **Before**: [Complexity level]
- **After**: [Complexity level]
- **Impact**: [How this affects maintainability]
- **Mitigation**: [Documentation, comments, tests]

### Memory vs Speed

- **Trade-off**: [More memory for speed / Less memory but slower]
- **Justification**: [Why this trade-off makes sense]

### Readability

- **Impact on Readability**: [How optimization affects code clarity]
- **Mitigation**: [Comments explaining optimization]

### Feature Limitations

- **Constraints**: [Any functionality limitations from optimization]
- **Workarounds**: [How to handle edge cases]

---

## Prerequisites

[Requirements before optimizing]

**⚠️ DO NOT START THIS CARD UNLESS:**

- [ ] [Performance issue is measurable and reproducible]
- [ ] [Root cause is understood]
- [ ] [Benchmarking setup is ready]
- [ ] [Baseline metrics are captured]

**Why**: [Optimize based on data, not hunches]

### Required Tools

- [ ] Profiling tools
- [ ] Benchmarking tools
- [ ] Performance monitoring

### Required Knowledge

- [ ] Understanding of performance bottleneck
- [ ] Knowledge of optimization techniques
- [ ] Proficiency with profiling tools

---

## Related Cards

[Connections to features or technical work]

### Enables

**Enables**: [Card ID] - [Feature made possible by better performance]

[Features unblocked by optimization]

### Related

**Related**: [Card ID] - [Related performance work]

[Other optimization opportunities]

---

## Notes

[Additional context or performance considerations]

### Profiling Methodology

[How performance was analyzed]

- [Methodology used]
- [Tools used]

### Optimization Insights

[Lessons learned from optimization]

- [Insight 1]
- [Insight 2]

### Future Optimizations

[Additional improvements to consider]

- [Opportunity 1]
- [Opportunity 2]

### Resources

[Helpful performance resources]

- [Performance guide]: [Link]
- [Profiling tutorial]: [Link]

---

## Progress Notes

[Track optimization progress session by session]

**Session [YYYY-MM-DD] ([Your Name]):**

✅ **Completed:**
- [Optimization implemented]
- [Performance measured]

📊 **Metrics:**
- Before: [Measurement]
- After: [Measurement]
- Improvement: [X%]

🔄 **In Progress:**
- [Current optimization work]

⚠️ **Issues:**
- [Problem encountered]: [Resolution]

📋 **Next Session:**
1. [Next optimization]
2. [Additional profiling needed]

**Performance Notes:**
[Observations about performance characteristics]

---

<!--
EXTENSION POINTS:

## Scalability Analysis
[How performance changes with load/data size]

## Cost Analysis
[Infrastructure cost savings from optimization]

## Resource Profiling
[Detailed CPU/memory/I/O analysis]

## Distributed Systems Performance
[Optimizing across multiple services]

Add project-specific sections as needed!
-->
## Additional Notes (optional)

**📝 FREEFORM SECTION - Add anything you need from this point onward!**

Feel free to add any custom sections, notes, or documentation specific to your project below this line. No validation is enforced here - organize additional information however works best for your workflow.
