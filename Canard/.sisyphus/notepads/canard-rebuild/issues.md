# Canard Rebuild Issues

(none yet)

## 2026-02-28
- `python -m pytest` initially failed because `pytest` was not installed in `services/api/.venv`.
- `pip install -e '.[dev]'` failed due setuptools flat-layout package discovery conflict (`app` and `migrations` both top-level).
- Resolved execution path by installing `pytest` directly, then installing runtime dependencies from `requirements.txt` before test run.
