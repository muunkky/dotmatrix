# Roadmap Usage Guide

This guide explains how to use the `docs/roadmap.yaml` file for strategic planning while maintaining day-to-day task tracking in the Gitban system.

## Overview

The data platform uses a **two-tier planning system**:

1. **Strategic Roadmap** (`docs/roadmap/roadmap.yaml`) - Long-term planning, milestones, features
2. **Tactical Gitban** (`.gitban/cards/`) - Day-to-day tasks, sprint work

This separation ensures strategic clarity while maintaining agility in execution.

## Roadmap Structure

### Hierarchy

```
versions (V1, V2, ...)
  └─ milestones (M1, M2, M3, ...)
      └─ features (groups of related work)
          └─ projects (specific deliverables)
```

### Status Values

Each level uses one of three statuses:
- **`todo`** - Not started, planned for future
- **`in_progress`** - Active work happening now
- **`done`** - Completed and delivered

## When to Use the Roadmap

### ✅ DO Update the Roadmap For:

- **Adding new features or milestones** to the plan
- **Changing milestone due dates** based on new information
- **Marking milestones complete** when all features delivered
- **Adding new projects** to existing features
- **Updating project TDD specs** as requirements become clearer
- **Recording major strategic pivots** or priority changes

### ❌ DO NOT Update the Roadmap For:

- **Individual task progress** (use Gitban cards)
- **Daily status updates** (that's what Gitban is for)
- **Developer assignments** (Gitban cards have owners)
- **Detailed technical notes** (those go in code comments or docs)

## Working with Milestones

### Milestone Lifecycle

1. **Planning Phase** (`todo`)
   - Review milestone description and success criteria
   - Ensure all features are defined with clear outcomes
   - Estimate timeline and identify dependencies

2. **Execution Phase** (`in_progress`)
   - Create Gitban cards for projects using feature IDs as sprint tags
   - Work projects in sequence order when specified
   - Update `docs_ref` links as documentation is created

3. **Completion Phase** (`done`)
   - Verify all success criteria met
   - Update milestone status to `done`
   - Conduct retrospective and document lessons learned

### Example: Planning M1

```yaml
m1:
  title: "M1: Core Infrastructure & First Ingestion"
  status: "in_progress"
  due_date: "2025-10-31"
  success_criteria:
    - "Terraform successfully deploys all infrastructure"
    - "At least one successful sync from HubSpot to BigQuery"
```

**Planning Steps:**

1. Review M1 features: `infra-core` and `ingestion-sources`
2. Create Gitban cards for ready projects (e.g., `terraform-setup`)
3. Tag cards with feature ID: `INFRACORE-todo-P1-...`
4. Track day-to-day progress in Gitban
5. When M1 complete, update `status: "done"` and move to M2

## Working with Features

Features group related projects toward a common goal.

### Feature Structure

```yaml
infra-core:
  id: "infra-core"
  title: "Core GCP Infrastructure via Terraform"
  description: "Provision all foundational cloud resources..."
  priority: "critical"  # critical | high | medium | low
  depends_on: []        # optional, list of feature IDs
  projects:
    # ... project definitions
```

### Feature Priorities

- **`critical`** - Blocking other work, must complete ASAP
- **`high`** - Important for milestone success, prioritize
- **`medium`** - Valuable but not blocking, schedule accordingly
- **`low`** - Nice to have, defer if time constrained

## Working with Projects

Projects are the smallest unit in the roadmap - specific deliverables with TDD specs.

### Project Structure

```yaml
terraform-setup:
  id: "terraform-setup"
  title: "Setup Terraform Cloud & GCP Provider"
  description: "Configure Terraform Cloud workspace..."
  owner: ""              # GitHub username, leave blank until assigned
  tdd_spec: "terraform plan runs successfully..."
  docs_ref: "docs/setup/terraform-setup.md"
  sequence: 1            # optional, indicates execution order
  depends_on: []         # optional, list of project IDs
```

### TDD Spec Guidelines

The `tdd_spec` field defines **done** for a project. Good TDD specs are:

- **Testable**: Can be verified objectively
- **Specific**: Clear success criteria, not vague goals
- **Measurable**: Quantifiable when possible

**Examples:**

✅ Good: "terraform apply creates three datasets with correct IAM bindings"
❌ Bad: "Terraform works properly"

✅ Good: "Airbyte UI accessible at URL, health check returns 200"
❌ Bad: "Airbyte is deployed"

### Docs Reference

The `docs_ref` field points to documentation for the project:

- Can be `"TBD"` when project is first planned
- Should reference actual doc location when created
- Can point to runbooks, architecture docs, or ADRs
- Update as documentation is written

## Integration with Gitban

### Creating Gitban Cards from Projects

When ready to work on a project from the roadmap:

1. **Identify the project** in `roadmap.yaml`
   ```yaml
   terraform-setup:
     id: "terraform-setup"
     title: "Setup Terraform Cloud & GCP Provider"
   ```

2. **Create Gitban card** with feature ID as sprint tag:
   ```bash
   # Using Gitban MCP
   create_card(
     title="Setup Terraform Cloud & GCP Provider",
     priority="P0",
     card_type="feature",
     status="backlog",
     sprint="INFRACORE"  # Feature ID as sprint tag
   )
   ```

3. **Work the card** through Gitban workflow:
   - Take card: moves to `in_progress`
   - Complete card: moves to `done`
   - Archive card: removed from active board

4. **Update roadmap** when all projects in a feature are done:
   ```yaml
   infra-core:
     status: "done"  # All projects completed
   ```

### Sprint Planning Workflow

1. **Review roadmap** for current milestone
2. **Select features** to work in upcoming sprint
3. **Create Gitban cards** for feature projects
4. **Use sprint tags** to group related cards (feature IDs)
5. **Track progress** in Gitban daily
6. **Update roadmap** at milestone boundaries

### Example Sprint Plan

**Sprint Goal:** Complete M1 infrastructure setup

**From Roadmap:**
- Feature: `infra-core` (6 projects)
- Feature: `ingestion-sources` (partially)

**Gitban Cards Created:**
```
INFRACORE-backlog-P0-feature-setup-terraform-cloud-xyz123.md
INFRACORE-backlog-P0-feature-define-bigquery-datasets-abc456.md
INFRACORE-backlog-P1-feature-create-service-accounts-def789.md
...
```

**Sprint Execution:**
- Move cards through workflow (backlog → todo → in_progress → done)
- Archive completed cards at sprint end
- Update roadmap if feature fully complete

## Roadmap Maintenance

### Monthly Review Process

1. **Review progress** on current milestone
2. **Adjust due dates** if needed based on actual velocity
3. **Refine future milestones** as understanding improves
4. **Add new features** as requirements emerge
5. **Update project TDD specs** that were initially `"TBD"`
6. **Archive completed versions** when all milestones done

### Updating the Roadmap

#### Adding a New Feature

```yaml
features:
  new-feature:
    id: "new-feature"
    title: "Descriptive Feature Name"
    description: "What this feature accomplishes and why it matters"
    priority: "high"
    projects:
      first-project:
        id: "first-project"
        title: "First Project Title"
        owner: ""
        tdd_spec: "Clear, testable success criteria"
        docs_ref: "docs/path/to/doc.md"
```

#### Completing a Milestone

When all features in a milestone are done:

```yaml
m1:
  status: "done"  # Changed from "in_progress"
  # Optionally add actual completion date
  completed_date: "2025-11-05"
```

#### Adjusting Timeline

```yaml
m2:
  due_date: "2025-12-31"  # Extended from 2025-12-15
  # Consider adding a note explaining the change
```

## Best Practices

### 1. Keep Roadmap Strategic

The roadmap should answer:
- **What** are we building? (features)
- **Why** are we building it? (descriptions, success criteria)
- **When** do we plan to deliver? (milestone due dates)

Leave **how** and **who** to Gitban cards.

### 2. Use Semantic IDs

Project IDs become reference points:
- Use kebab-case: `terraform-setup`, not `Terraform Setup`
- Be descriptive: `staging-properties`, not `proj1`
- Prefix for context: `stg_hubspot__contacts` for dbt models

### 3. Keep TDD Specs Current

As you learn more about a project:
- Replace `"TBD"` with actual test criteria
- Make specs more specific and measurable
- Update when requirements change

### 4. Link Everything

Create a web of references:
- Roadmap → Documentation (`docs_ref`)
- Documentation → Roadmap (link to `roadmap.yaml`)
- ADRs → Roadmap (explain decisions for features)
- Gitban Cards → Roadmap (sprint tags = feature IDs)

### 5. Review Regularly

Schedule recurring reviews:
- **Weekly**: Check milestone progress, adjust sprint planning
- **Monthly**: Update roadmap, refine future milestones
- **Quarterly**: Review version progress, plan next version

## Tools & Automation

### Parsing the Roadmap

The roadmap is YAML, so it's easily parsed by tools:

```python
import yaml

with open('docs/roadmap.yaml') as f:
    roadmap = yaml.safe_load(f)

# Get all M1 projects
m1_projects = roadmap['versions']['v1']['milestones']['m1']['features']

# Find critical features
critical = [f for f in features if f.get('priority') == 'critical']
```

### Integration Ideas

Future automation possibilities:
- **Dashboard**: Visualize roadmap progress
- **Alerts**: Notify when milestones approach due dates
- **Sync Check**: Compare roadmap to Gitban cards, identify gaps
- **Reports**: Generate progress reports for stakeholders

## Common Scenarios

### Scenario 1: Starting a New Milestone

1. Open `docs/roadmap.yaml`
2. Find the milestone (e.g., `m2`)
3. Review all features and projects
4. Create Gitban cards for first wave of projects
5. Update milestone status to `in_progress`
6. Commit the status change

### Scenario 2: Feature Taking Longer Than Expected

1. Assess remaining work (check Gitban cards)
2. If blocking milestone, consider:
   - Extending milestone due date
   - Moving less critical features to next milestone
   - Adding resources (more team members)
3. Update roadmap with decision
4. Document reasoning in commit message

### Scenario 3: Requirements Change Mid-Milestone

1. Create ADR documenting the change and rationale
2. Update affected feature descriptions in roadmap
3. Update project TDD specs to reflect new requirements
4. Update or create new Gitban cards as needed
5. Commit changes with clear explanation

### Scenario 4: New Feature Request

1. Determine which milestone it belongs to
2. Add feature to appropriate milestone in roadmap
3. Define initial projects (can be refined later)
4. Set priority and dependencies
5. Create Gitban cards if working on it immediately

## See Also

- [Project Roadmap](../roadmap.yaml) - The actual roadmap document
- [Gitban MCP Documentation](../../.gitban/README.md) - Task tracking system
- [Architecture Overview](../architecture/overview.md) - Technical context
- [ADRs](../adrs/) - Architectural decisions
- [Contributing Guide](../CONTRIBUTING.md) - Contribution workflow

## Questions?

If you're unsure whether something belongs in the roadmap or Gitban:

**Ask yourself:**
- Is this a strategic milestone or feature? → Roadmap
- Is this a day-to-day task or sprint work? → Gitban
- Will this take more than 2 weeks? → Probably a feature (roadmap)
- Is this a single deliverable? → Probably a project (roadmap) or card (Gitban)

When in doubt, err on the side of Gitban for execution details and roadmap for strategic planning.
