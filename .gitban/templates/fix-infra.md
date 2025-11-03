
## Bug Description

[What's broken in infrastructure - REQUIRED]

**Summary**: [Brief infrastructure bug description - REQUIRED]

[Description of the infrastructure issue]

---

## System Context

[Where it happens - REQUIRED (at least service + environment)]

**Affected service**: [Affected service or component]

**Environment**: [Environment name] [staging/production/dev]

**Region/AZ**: [if applicable] (optional)

**Deployment version**: [version/commit hash] (optional)

---

## Fix Implementation

[How to fix it - REQUIRED (may be "investigate first")]

**Approach**: [Fix approach and strategy]

[Describe the fix approach and changes needed]

**Changes required**:
- [Configuration or infrastructure change 1]
- [Configuration or infrastructure change 2]

---

## System Evidence (optional)

[Logs, metrics, traces - may not have yet]

**System logs**: [CloudWatch/DataDog/Splunk link] (optional)

**Metrics dashboard**: [Grafana/Datadog link] (optional)

**APM traces**: [link] (optional)

**Infrastructure diagram**: [link or describe] (optional)

---

## Service Dependencies (optional)

[May not know until investigation]

**Upstream dependencies**: [list] (optional)

**Downstream consumers**: [list] (optional)

**Database**: [which DB, connection pool status] (optional)

**External services**: [third-party dependencies] (optional)

---

## Infrastructure as Code Changes (optional)

[IaC updates - may be manual fix first]

**IaC files affected**:
- [ ] Terraform modules: [list specific .tf files] (optional)
- [ ] CloudFormation stacks: [list stack names] (optional)
- [ ] Kubernetes manifests: [list YAML files] (optional)

**Infrastructure diff**:
- Resources being modified: [list] (optional)
- Configuration changes: [what's changing] (optional)

**Rollback via IaC**:
- [ ] Previous IaC state tagged/committed (optional)
- [ ] Rollback command documented (optional)
- [ ] Rollback tested in staging (optional)

---

## Incident Timeline (optional)

[For postmortem - not required for initial bug report]

- **[Time]**: Incident detected (optional)
- **[Time]**: Investigation began (optional)
- **[Time]**: Root cause identified (optional)
- **[Time]**: Fix deployed (optional)
- **[Time]**: Incident resolved (optional)

---

## Testing & Verification (optional)

[How to verify the fix works]

**Verification steps**:
- [ ] Fix tested in dev environment (optional)
- [ ] Smoke tests pass (optional)
- [ ] Monitoring shows resolution (optional)
- [ ] No new errors introduced (optional)

---

## Additional Notes (optional)

📝 FREEFORM SECTION - Add anything project-specific

[Any other relevant information]
