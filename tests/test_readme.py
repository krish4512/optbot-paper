"""Root README regression tests (docs only). They pin the plain-English overview so wording cannot silently drift:
the mermaid flowchart, the three-way (a)/(b)/(c) separation, the honesty points and the currency paragraph, and that the
numbers quoted in the README still match the shipped default config inside the current bootstrap."""
import importlib.util
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
FLAT = " ".join(README.split())
BOOT = ROOT / "optbot_v0.6.33_bootstrap.py"


@pytest.fixture(scope="module")
def files():
    spec = importlib.util.spec_from_file_location("boot067", BOOT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.FILES


def mermaid_block():
    m = re.search(r"```mermaid\n(.*?)\n```", README, re.S)
    assert m, "README must contain a ```mermaid fenced block"
    return m.group(1)


# ---- (i) flowchart
def test_mermaid_block_present_once_and_is_a_flowchart():
    assert README.count("```mermaid") == 1
    assert mermaid_block().lstrip().startswith("flowchart TD")


@pytest.mark.parametrize("label", ["Kill switch on?", "Risk limits allow?", "Candidate found?", "Exit rule hit?",
                                   "Data valid?", "Regular session?", "Fill within limit?", "Market hours?",
                                   "Tick starts", "End tick", "Paper position opened", "Rejected, reasons logged",
                                   "Write daily and weekly report"])
def test_flowchart_has_the_named_decision_points_and_end_states(label):
    assert label in mermaid_block()


def test_flowchart_edges_only_reference_defined_nodes_and_labels_are_short():
    body = mermaid_block().splitlines()[1:]
    defined = {}
    for line in body:
        for nid, label in re.findall(r"\b([A-Za-z][A-Za-z0-9]*)(?:\(\[|\{|\[)([^\]\}\)]+)(?:\]\)|\}|\])", line):
            defined[nid] = label
    assert len(defined) >= 20
    for line in body:
        stripped = re.sub(r"\b[A-Za-z][A-Za-z0-9]*(?:\(\[|\{|\[)[^\]\}\)]+(?:\]\)|\}|\])", lambda m: m.group(0).split("[")[0].split("{")[0].split("(")[0], line)
        stripped = re.sub(r"--\s*\w+\s*-->|-->", " ", stripped)
        for tok in stripped.split():
            assert tok in defined, (line, tok)
    assert max(len(v) for v in defined.values()) <= 50          # short enough to read


def test_flowchart_every_branch_of_a_decision_is_labelled_yes_no():
    body = mermaid_block()
    for node in ("M", "V", "X", "KX", "R", "K", "C", "L", "F", "RP"):
        outs = re.findall(rf"^\s*{node} -- (yes|no) -->", body, re.M)
        assert sorted(outs) == ["no", "yes"], node


# ---- (ii) three-way separation, in order
def test_three_way_separation_headings_exist_in_order():
    heads = [
        "## (a) What the bot actually does today in a default run",
        "## (b) Optional, research-only capabilities (evaluation tools)",
        "## (c) Known gaps / not built",
    ]
    pos = [README.index(h) for h in heads]
    assert pos == sorted(pos)
    assert README.index("## How a trade works") < pos[0]
    assert README.index("## What this is") < README.index("## How a trade works")


def test_section_b_says_evaluation_tools_not_in_default_decision_path():
    b = README[README.index("## (b)"):README.index("## (c)")]
    assert "evaluation tools, not part of the default decision path" in b
    for name in ("stats.py", "blackscholes.py", "risk.py", "backtest.py", "pricing.py", "off by default",
                 "quant.bs_pricing_enabled", "Nothing in the bot uses these for sizing or risk control"):
        assert name in b, name


def test_section_c_lists_the_known_gaps():
    c = README[README.index("## (c)"):README.index("## Getting the code")]
    for needle in ("No real market data", "No broker connection", "scheduled GitHub workflow is disabled", "disabled_manually",
                   "No demonstrated edge", "What would be required before any real-money use"):
        assert needle in c, needle


def test_section_a_does_not_claim_the_quant_library_drives_decisions():
    a = README[README.index("## (a)"):README.index("## (b)")]
    assert "Uses **none** of the quant library to make decisions" in a


# ---- (iii) honesty + currency
def test_honesty_points_are_near_the_top():
    top = README[:README.index("## What this is")]
    low = " ".join(top.lower().split())
    for needle in ("simulation only", "synthetic data only", "no edge demonstrated", "config assumption",
                   "not a measured market implied volatility", "gamma p&l identity", "does not delta-hedge",
                   "no profit claims", "financial advice"):
        assert needle in low, needle


CURRENCY = ("Currency convention (simulation).** All money in reports, the walk-forward table and the optional "
            "`quant_analytics` output is paper USD simulation units. Starting capital is configured in CAD "
            "(`capital.paper_capital_cad`) and converted once to USD with config `fx.usd_cad` (a test input, not a market "
            "rate). No currency conversion is applied to P&L (simulated; no currency conversion is made). Nothing here is "
            "a CAD performance figure.")


def test_currency_paragraph_is_verbatim_and_near_the_top():
    assert CURRENCY in FLAT
    assert FLAT.index(CURRENCY) < FLAT.index("What this is")


def test_currency_wording_matches_the_units_note_in_the_shipped_code(files):
    src = files["src/optbot/quant/__init__.py"]
    for ph in ("paper USD simulation units", "capital.paper_capital_cad", "fx.usd_cad", "no currency conversion is made"):
        assert ph in src and ph in README


def test_no_profit_claims():
    low = README.lower()
    for phrase in ("guaranteed profit", "will make money", "profitable strategy", "proven edge", "beats the market"):
        assert phrase not in low


# ---- grounded in the current code: quoted numbers match the shipped default config
def test_readme_numbers_match_default_config(files):
    cfg = tomllib.loads(files["config/default.toml"])
    v = lambda *path: __import__("functools").reduce(lambda d, k: d[k], path, cfg)["value"]   # noqa: E731
    assert v("risk", "max_premium_per_trade_pct") == 0.10 and "`max_premium_per_trade_pct` = 10% of equity" in README
    assert v("risk", "max_total_premium_pct") == 0.30 and "(at most `max_total_premium_pct` = 30% of equity)" in README
    assert (v("risk", "daily_loss_halt_pct"), v("risk", "weekly_loss_halt_pct"), v("risk", "total_loss_halt_pct")) == (0.03, 0.06, 0.15)
    assert "(3%)" in README and "(6%)" in README and "(15%)" in README
    assert v("risk", "max_open_structures") == 3 and "`risk.max_open_structures` (3)" in README
    assert (v("risk", "max_orders_per_minute"), v("risk", "max_orders_per_day")) == (6, 40)
    assert v("strategy", "long_straddle", "target_dte") == 30 and v("strategy", "long_straddle", "min_dte") == 21
    assert v("strategy", "long_straddle", "max_dte") == 45 and "(21..45)" in README
    assert v("strategy", "long_strangle", "otm_pct") == 0.03
    assert v("strategy", "long_straddle", "slippage_allowance") == 0.05 and "(0.05)" in README
    assert v("strategy", "long_straddle", "quantity") == 1 and v("strategy", "long_strangle", "quantity") == 1
    assert v("strategy", "put_credit_spread", "enabled") is False
    assert "put_credit_spread" not in v("risk", "allowed_structures")
    assert v("fill", "mode") == "conservative" and v("fill", "slippage_ticks") == 1 and v("fill", "tick_size") == 0.01
    assert v("exit", "force_close_days_before_last_trade") == 1 and v("exit", "max_holding_days") == 21
    assert v("exit", "stop_loss_pct_of_max_loss") == 0.5 and v("exit", "profit_target_pct_of_cost") == 0.5
    assert v("exit", "entry_cutoff_days_before_last_trade") == 5
    assert v("data", "max_underlying_age_s") == 5 and v("data", "max_mark_age_s") == 60
    assert v("data", "max_spread_pct_of_mid") == 0.10 and v("data", "min_open_interest") == 500
    assert v("capital", "paper_capital_cad") == 500 and v("fx", "usd_cad") == 1.41 and "US$354.61" in README
    assert round(500 / 1.41, 2) == 354.61
    assert v("quant", "bs_pricing_enabled") is False and v("quant", "bs_implied_vol") == 0.18
    assert v("risk", "settlement_supported_underlyings") == ["SPX", "XSP"]


def test_readme_file_and_test_counts_match_the_bootstrap(files):
    assert f"({len(files)} files, " in README
    assert BOOT.name in README
    assert 'version = "0.6.33"' in files["pyproject.toml"]


def test_readme_names_only_cli_commands_that_exist(files):
    cli = files["src/optbot/cli.py"]
    for cmd in re.findall(r"optbot (replay|tick|run|report|dashboard|demo-dashboard|walkforward-synthetic|kill)\b", README):
        assert f'"{cmd}"' in cli, cmd


def test_workflow_file_is_described_as_pinned_and_disabled():
    wf = (ROOT / ".github" / "workflows" / "synthetic-validation.yml").read_text()
    assert "optbot_v0.5.2_bootstrap.py" in wf and "optbot_v0.5.2_bootstrap.py" in README
    assert "disabled_manually" in README


def test_readme_describes_the_rejection_diagnostics_and_the_command_exists(files):
    for needle in ("Rejection diagnostics (v0.6.2)", "optbot report --kind rejections", "Why no trades opened",
                   "smallest `capital.paper_capital_cad`", "change no strategy rule, limit, default or trade"):
        assert needle in README, needle
    assert '"rejections"' in files["src/optbot/cli.py"] and "diagnostics.py" in " ".join(files)
    assert "10011" in README and "10010" in README


def test_readme_states_the_test_count_and_the_bootstrap_ships_tests(files):
    n_tests = sum(len(re.findall(r"^\s*def test_", v, re.M)) for k, v in files.items() if k.startswith("tests/"))
    assert n_tests > 0 and "2663 tests" in README


def test_readme_describes_the_v063_dashboard_and_its_limit(files):
    for needle in ("Dashboard (v0.6.3)", "headline state", "REJECTING ALL CANDIDATES", "pipeline", "open-positions table",
                   "paper USD", "--total-days"):
        assert needle in README, needle
    assert '"--total-days"' in files["src/optbot/cli.py"] and "_render_top" in files["src/optbot/dashboard.py"]


def test_readme_describes_the_v064_per_position_marks_and_the_digest_change(files):
    for needle in ("Per-position marks (v0.6.4)", "position_marks", "journal schema 2", "raw journal and report digests changed once",
                   "byte-identical to before", "never zero", "valued at cost"):
        assert needle in README, needle
    assert "a mark for each separate position is not stored" not in README         # the v0.6.3 limitation is resolved
    assert "position_marks" in files["src/optbot/posmarks.py"] and "JOURNAL_SCHEMA_VERSION = 2" in files["src/optbot/posmarks.py"]
    assert "| 37 |" in files["docs/DECISIONS.md"]


def test_readme_describes_the_v065_analytics_section_and_keeps_it_out_of_decisions(files):
    for needle in ("Informational analytics (v0.6.5)", "Analytics (informational only - never used for any trading decision)",
                   "config assumption (UNCONFIRMED), not market data", "`unknown`, never zero", "not evidence of edge or profitability",
                   "adds no journal event", "appended to weekly reports", "only the reporting and CLI layers import it"):
        assert needle in README, needle
    a = README[README.index("## (a)"):README.index("## (b)")]
    assert "Uses **none** of the quant library to make decisions" in a and "never read by anything that decides" in a
    assert "analytics.py" in " ".join(files) and "SECTION_TITLE" in files["src/optbot/analytics.py"]
    assert "| 38 |" in files["docs/DECISIONS.md"]


def test_readme_describes_the_v066_doctor_command_and_its_limits(files):
    for needle in ("`optbot doctor` (v0.6.6)", "read-only (it writes nothing and never creates a directory)", "pass/warn/fail",
                   "READY for: local synthetic replay only. BLOCKED for: real-data paper run (4 blockers), live trading (6 blockers: not authorized, no broker path).",
                   "--target synthetic-replay|paper-data|live", "`live` is always blocked", "cannot see whether the GitHub workflow is enabled",
                   "READY never means a strategy has an edge", "optbot doctor --target paper-data"):
        assert needle in README, needle
    c = README[README.index("## (c)"):README.index("## Getting the code")]
    assert "optbot doctor" in c                                                    # the gaps section points at the one command
    assert '"doctor"' in files["src/optbot/cli.py"] and "def run_doctor" in files["src/optbot/doctor.py"]
    assert "| 39 |" in files["docs/DECISIONS.md"]


def test_readme_describes_the_v067_provider_contract_as_a_specification_only(files):
    for needle in ("provider contract", "docs/PROVIDER_CONTRACT.md", "optbot.data.contract", "28 rules", "a validator for one snapshot",
                   "a reusable conformance suite", "It is a specification only", "no feed was built", "does not unblock a real-data run"):
        assert needle in README, needle
    c = README[README.index("## (c)"):README.index("## Getting the code")]
    assert "provider contract" in c                                                  # listed under the known gaps, not as a capability
    assert "def validate_provider_snapshot" in files["src/optbot/data/contract.py"] and "docs/PROVIDER_CONTRACT.md" in files
    assert "| 40 |" in files["docs/DECISIONS.md"] and "class ProviderContractSuite" in files["tests/provider_contract.py"]
    assert "DataProvider" not in " ".join(l for l in files["src/optbot/data/contract.py"].splitlines() if l.startswith("class "))   # no provider class added


def test_readme_describes_the_v068_regime_comparison_and_the_command_flag_exists(files):
    for needle in ("Multi-regime comparison (v0.6.8", "--regimes all", "invented", "not evidence about real markets",
                   "no edge has been demonstrated", "cost-study gate", "trending-up", "range-bound", "vol-spike"):
        assert needle in README, needle
    assert '"--regimes"' in files["src/optbot/cli.py"] and "synthetic_regimes.py" in " ".join(files)


def test_readme_describes_the_v069_seed_robustness_and_the_flag_exists(files):
    for needle in ("--seeds N", "min / median / max", "results vary across seeds", "randomness in made-up data", "no edge has been demonstrated",
                   "byte-identical to v0.6.8"):
        assert needle in README, needle
    assert '"--seeds"' in files["src/optbot/cli.py"]


def test_readme_describes_the_v0610_cost_sensitivity_and_the_flag_exists(files):
    for needle in ("--cost-scenarios", "UNCONFIRMED assumption", "illustrative brackets", "bounds on real costs", "not evidence about real markets",
                   "byte-identical to v0.6.9"):
        assert needle in README, needle
    assert '"--cost-scenarios"' in files["src/optbot/cli.py"]


def test_readme_describes_the_v0611_stress_scenarios_and_the_flag_exists(files):
    for needle in ("--stress", "invented shocks", "arbitrary choices", "not calibrated to any real event", "not evidence of robustness in real markets",
                   "no edge has been demonstrated", "byte-identical to v0.6.10"):
        assert needle in README, needle
    assert '"--stress"' in files["src/optbot/cli.py"] and "synthetic_stress.py" in " ".join(files)


def test_readme_describes_the_v0612_window_sweep_and_the_flag_exists(files):
    for needle in ("--windows-sweep", "arbitrary choices", "not evidence about real markets", "no edge has been demonstrated", "byte-identical to v0.6.11"):
        assert needle in README, needle
    assert '"--windows-sweep"' in files["src/optbot/cli.py"]
