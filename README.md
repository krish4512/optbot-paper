# optbot-paper

Paper-only options study bot (development version, not production-ready, not running anywhere). SIMULATION ONLY: no live orders, no broker SDK, no real market data in this repository, no profit claims. No edge demonstrated.

`optbot_v0.6.1_bootstrap.py` recreates the full source tree (95 files, 1279 tests). Older bootstraps (v0.6.0, v0.5.2, v0.5.1, v0.5, v0.4.1) are kept for reference only and are unchanged.

    python3 optbot_v0.6.1_bootstrap.py optbot
    cd optbot && python3 -m venv .venv && .venv/bin/pip install -e ".[test]" && .venv/bin/pytest
    .venv/bin/optbot demo-dashboard --out dashboard.html
    .venv/bin/optbot tick --once --state-dir DIR   # one restart-safe cycle for a scheduled job
    .venv/bin/optbot walkforward-synthetic --days 40 --train-days 10 --test-days 5   # v0.6.0, SYNTHETIC only

## New in v0.6.0 (units wording clarified in v0.6.1): quant foundations (library code, stdlib only)

`src/optbot/quant/` adds `stats.py` (returns, mean/variance, standard error, autocorrelation, Sharpe and its t-statistic),
`blackscholes.py` (prices, Greeks, put-call parity helper, implied volatility by bisection, `math.erf` normal CDF),
`risk.py` (Kelly and half-Kelly, historical VaR / expected shortfall, max drawdown), `backtest.py` (a walk-forward harness over the
existing synthetic data path and paper pipeline) and `pricing.py` (optional Black-Scholes pricing of the synthetic chain, with premium,
expiry breakevens and Greeks in the journal and daily report).

- **Default OFF.** The Black-Scholes wire-in runs only when `quant.bs_pricing_enabled = true`. With the shipped config, synthetic chains,
  journal, ledger, orders and equity are identical to v0.5.2 (golden-digest tests). The one visible difference in reports is the config-parameter
  tally (76 of 86 UNCONFIRMED, was 71 of 81), because five `[quant]` parameters were added.
- **Simulation only, synthetic data only, no edge demonstrated.** The walk-forward harness fits nothing; on a driftless synthetic random walk,
  window results are noise plus cost drag. Entries stay mechanical; nothing adds a signal.
- **Implied volatility here is a config assumption** (`quant.bs_implied_vol`), not a measured market implied volatility.
- **The gamma P&L identity** (realised vs implied variance) applies to delta-hedged positions. **This bot does not delta-hedge.**
- **Currency convention (simulation).** All money in reports, the walk-forward table and the optional `quant_analytics` output is paper USD simulation units. Starting capital is configured in CAD (`capital.paper_capital_cad`) and converted once to USD with config `fx.usd_cad` (a test input, not a market rate). No currency conversion is applied to P&L (simulated; no currency conversion is made). Nothing here is a CAD performance figure.
- The Sharpe t-statistic is per-period Sharpe x sqrt(N), assumes iid returns and is not corrected for multiple testing.

See docs/READINESS.md inside the tree for what was verified with synthetic data and what was not.

The scheduled workflow `.github/workflows/synthetic-validation.yml` stays pinned to `optbot_v0.5.2_bootstrap.py` on purpose (its recorded synthetic input hash and state are tied to that build); it is not changed by v0.6.0.

Never commit provider quote data here. The demo dashboard uses a synthetic replay clock and synthetic data; it is not real time and not real trading.
