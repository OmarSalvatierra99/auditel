# Repository Guidelines

## Project Structure & Module Organization
`app.py` is the main Flask entrypoint and contains routes, session handling, logging, and the TF-IDF search flow. `config.py` holds minimal project constants such as `PORT`. Put reusable helpers in `scripts/` (`auth.py`, `utils.py`), UI templates in `templates/`, and front-end assets in `static/css`, `static/js`, and `static/img`. Keep tests in `tests/`, deployment files in `deploy/`, and prompt/reference material in `prompts/`.

## Build, Test, and Development Commands
Set up a virtual environment before working:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

The app runs locally on port `5003` by default. Use `venv/bin/pytest tests/ -v` to run the test suite, and `curl http://localhost:5003/api/health` for a quick health check after local changes.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, `snake_case` for functions and variables, `CapWords` for classes, and `UPPER_SNAKE_CASE` for constants. Keep Flask route code readable and move shared logic into `scripts/` when it grows beyond a single handler. Match filenames to purpose, such as `templates/login.html` or `tests/test_app.py`. No formatter or linter is configured here, so keep imports grouped, comments sparse, and diffs small.

## Testing Guidelines
This repository uses `pytest` with the Flask test client. Add tests under `tests/test_*.py`; shared fixtures belong in `tests/conftest.py`. Cover endpoint status codes, login/session behavior, and any change to auth helpers or search logic. When fixing a bug, add or update a regression test in the same change.

## Commit & Pull Request Guidelines
Recent commits use short imperative subjects, sometimes with maintenance prefixes, for example `Homogenize configuration` or `Clean project: update scripts...`. Keep commit messages concise, imperative, and scoped to one logical change. Pull requests should include a short summary, test evidence, linked issue or task when applicable, and screenshots for template or CSS changes.

## Security & Configuration Tips
Do not commit `.env`, secrets, generated logs, or shared user data. `SECRET_KEY` must be set locally, and user access depends on the shared catalog referenced in `.env.example`. Treat deployment files in `deploy/` as production-facing changes and update them only when the runtime behavior actually changes.
