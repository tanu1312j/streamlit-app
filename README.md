# Streamlit Personal Finance Toolbox

This repository contains a small Streamlit app that provides several personal-finance helper tools: savings planner, insurance recommendations, realtime advice (market signals), and a portfolio rebalancer. It is intended as a local development project and educational demo.

## Quick start (macOS / zsh)

1. Create and activate a virtualenv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the smoke test (headless checks):

```bash
export PYTHONPATH=.
python3 scripts/smoke_test.py
```

3. Start the Streamlit app:

```bash
.venv/bin/python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
# then open http://localhost:8501
```

## Files of interest

- `app.py` — Streamlit UI (Savings, Insurance, Realtime Advice, Rebalance)
- `tools/` — backend helpers used by the UI (savings_model, insurance_model, realtime_advice, rebalancer, market_data, etc.)
- `core/` — small shared modules (schemas, config)
- `scripts/smoke_test.py` — quick validator that runs all tools in a headless fashion

## Notes on optional dependencies

- `yfinance` is used optionally by the realtime advice and market data helpers. Network timeouts or missing `yfinance` are handled gracefully by the app, but installing `yfinance` will provide live behavior:

```bash
pip install yfinance
```

- For better Streamlit dev performance, install `watchdog`:

```bash
pip install watchdog
```

## Running tests and debug tips

- Use `PYTHONPATH=.` when running helper scripts so local modules import correctly.
- If your Streamlit session hangs on external downloads (yfinance), the UI uses short timeouts; you can re-run problematic flows manually or inspect the logs.

## Committing & pushing

Typical workflow:

```bash
git checkout -b fix/streamlit-ui
git add .
git commit -m "chore: update Streamlit app and tool wiring"
git push -u origin fix/streamlit-ui
# create PR on GitHub via web UI or `gh pr create`
```

## Troubleshooting

- If push fails with authentication errors, run `gh auth login` or set up SSH keys and use the SSH remote URL.
- If you accidentally committed `.venv` or large files, `git rm -r --cached .venv` then update `.gitignore`.

## License

Add your preferred license file (`LICENSE`) if you plan to publish this project.

---
Small, local demo — adapt as needed for production.
