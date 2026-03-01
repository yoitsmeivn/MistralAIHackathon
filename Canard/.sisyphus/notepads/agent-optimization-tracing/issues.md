# Issues — agent-optimization-tracing

## Session: ses_358eff8f8ffebYyXD6HWlJMrS0 (2026-03-01)

(none yet — tracking in progress)

## Session: backend-fixes-persona-call-complete (2026-03-01)

### Test Environment Issue
- Full test run `python -m pytest tests -q` failed with 6 failures in `tests/test_audio_features.py` due to missing dependency `pydub` (`ModuleNotFoundError`).
- This is environment/dependency related and not caused by the backend code changes in this task.

## Session: campaign-launch-crash-fix (2026-03-01)

### Observed Warnings
- Frontend build warns about a large bundle chunk (`index-*.js` > 500 kB). Build still succeeds; no blocking errors.
