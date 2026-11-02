# optbot-paper

Paper-only options study bot (development version, not production-ready, not running anywhere). SIMULATION ONLY: no live orders, no broker SDK, no real market data in this repository, no profit claims. No edge demonstrated.

`optbot_v0.5.1_bootstrap.py` recreates the full source tree (82 files, 477 tests). Older bootstraps (v0.5, v0.4.1) are kept for reference only.

    python3 optbot_v0.5.1_bootstrap.py optbot
    cd optbot && python3 -m venv .venv && .venv/bin/pip install -e ".[test]" && .venv/bin/pytest
    .venv/bin/optbot demo-dashboard --out dashboard.html
    .venv/bin/optbot tick --once --state-dir DIR   # one restart-safe cycle for a scheduled job

See docs/READINESS.md inside the tree for what was verified with synthetic data and what was not.

Never commit provider quote data here. The demo dashboard uses a synthetic replay clock and synthetic data; it is not real time and not real trading.
