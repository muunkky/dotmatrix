# Feature: Minimum Distance Between Circles Filter

## Description
Add `--min-distance` CLI flag to prevent overlapping circle detections by enforcing minimum distance threshold between detected circle centers.

## Acceptance Criteria
- [x] `--min-distance N` CLI flag (default: 20px)
- [x] Pass minDist to cv2.HoughCircles()
- [x] Tests written first (TDD RED)
- [x] Implementation passes (TDD GREEN)
- [x] Docs updated (CHANGELOG, README, ROADMAP)

## Implementation
- [x] Add CLI flag to cli.py
- [x] Update detect_circles() signature with min_distance param
- [x] Pass to cv2.HoughCircles as 2nd arg
- [x] Write TDD tests (varied distances)
- [x] Update documentation

## Technical Notes
- cv2.HoughCircles minDist = 2nd positional parameter
- Distance measured between circle centers
