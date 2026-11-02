# optbot-paper

Paper-only options study bot. SIMULATION ONLY: no live orders, no broker SDK, no real market data, no profit claims. No edge demonstrated.

This repository holds one file, `optbot_v0.4.1_bootstrap.py`, that recreates the full source tree (72 files, 358 tests).

    python3 optbot_v0.4.1_bootstrap.py optbot
    cd optbot && python3 -m venv .venv && .venv/bin/pip install -e ".[test]" && .venv/bin/pytest
    .venv/bin/optbot demo-dashboard --out dashboard.html

The demo dashboard uses a synthetic replay clock and synthetic data; it is not real time and not real trading.
