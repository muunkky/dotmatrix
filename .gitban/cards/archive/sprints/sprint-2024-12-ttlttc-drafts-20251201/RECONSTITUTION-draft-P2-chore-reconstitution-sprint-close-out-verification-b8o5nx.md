## Description

Sprint close-out verification for RECONSTITUTION sprint. Ensures all cards are complete, tests pass, and documentation is updated.

## Tasks

- [ ] All sprint cards marked as done
- [ ] All tests pass (`pytest tests/test_cluster_renderer.py`)
- [ ] CLI help shows `--reconstitute` flag
- [ ] Manual test: `dotmatrix -i test_dotmatrix.png --convex-edge --palette cmyk --reconstitute`
- [ ] Verify reconstituted.png generated in run directory
- [ ] Verify manifest.json includes reconstituted.png
- [ ] Archive sprint cards to sprint-reconstitution-YYYYMMDD
- [ ] Update changelog with new feature

## Acceptance Criteria

- [ ] Sprint cards archived
- [ ] Tests passing
- [ ] Feature documented in changelog
