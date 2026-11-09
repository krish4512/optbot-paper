#!/usr/bin/env python3
"""Rebuild the data block inside mission_control.html (PROTOTYPE; simulation only; synthetic data only).

It runs the project's own SYNTHETIC replay in a temporary directory, builds the existing dashboard model
(optbot.dashboard.build_model) and reads the journal that replay wrote. Nothing is invented here: every value put
in the page is a recorded journal field or a field of the existing model (see README.md for the mapping).
No network, no dependency beyond the extracted optbot tree, no change to any optbot code or command.

    python3 optbot_v0.6.53_bootstrap.py /tmp/optbot            # extract the tree somewhere outside the repo
    python3 prototypes/mission_control/build_snapshot.py --tree /tmp/optbot
"""
import argparse
import contextlib
import io
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTML = HERE / "mission_control.html"
OPEN, CLOSE = '<script id="snapshot" type="application/json">', "</script>"
KEY_KINDS = ("chain_seen", "intent", "decision", "execution", "ledger", "exit_signal", "exit_done", "report")
LOG_WINDOW = 240            # most recent journal events of every kind kept in the page (the key events of the whole run are kept too)


def leg(key: str) -> str:
    p = key.split("|")            # underlying|root|style|expiry|right|strike
    return f"{p[4]}{p[5]} exp {p[3]}" if len(p) == 6 else key


def build(tree: Path, days: int, capital_cad: str) -> dict:
    sys.path.insert(0, str(tree / "src"))
    from optbot import cli, dashboard as dash
    from optbot.config import load_config
    from optbot.events import Journal

    def local(ts):
        return dash._local(dash._parse(ts)) if ts else None

    with tempfile.TemporaryDirectory() as td:
        sd = Path(td) / "state"
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(["replay", "--synthetic", "--days", str(days), "--state-dir", str(sd), "--capital-cad", capital_cad])
        if rc != 0:
            raise SystemExit(f"synthetic replay failed with exit code {rc}")
        cfg = load_config()
        cfg.override("capital.paper_capital_cad", float(capital_cad), "mission-control prototype (same value as the replay)")
        m = dash.build_model(sd, cfg, datetime.now(timezone.utc))
        events = Journal(sd / "journal.jsonl").entries()

    intents = {e["id"]: e for e in events if e["kind"] == "intent"}
    execs = {e["intent_id"]: e for e in events if e["kind"] == "execution"}
    labels = {r["code"]: r["label"] for r in ((m.get("rejection_summary") or {}).get("top_reasons") or [])}

    def action(intent_id: str, strategy: str) -> str:
        return "open" if intent_id.endswith("-open") else ("close" if strategy == "exit_manager" else "order")

    def sid_of(e: dict):
        """The structure (trade) an event belongs to, when the record itself says so."""
        if e.get("sid"):
            return e["sid"]
        ident = e.get("id") or e.get("intent_id") or ""
        for marker in ("-open", "-close"):
            if marker in ident:
                return ident[:ident.index(marker)]
        return None

    def owner(e: dict):
        """The strategy an event belongs to: the skip's own strategy, else the strategy that opened the structure."""
        if e["kind"] == "no_trade":
            who, _, code = e["reason"].partition(":")
            return who if code else "do_nothing"
        sid = sid_of(e)
        return sid.split("-", 1)[0] if sid else None

    def reason_text(raw: str) -> str:
        code = raw.split(":", 1)[-1]
        return labels.get(code) or dash.plain_reason(raw)

    def line(e: dict) -> dict:
        k = e["kind"]
        if k == "no_trade":
            who, _, code = e["reason"].partition(":")
            tag, msg = "SKIP", f"{who if code else 'do_nothing'} {e.get('symbol', '')}: {code or who}"
        elif k == "intent":
            exps = {key.split("|")[3] for key, _, _ in e["legs"] if key.count("|") == 5}
            legs = (" + ".join(f"{s.lower()} {q} {key.split('|')[4]}{key.split('|')[5]}" for key, s, q in e["legs"]) + f" exp {exps.pop()}" if len(exps) == 1 else
                    " + ".join(f"{s.lower()} {q} {leg(key)}" for key, s, q in e["legs"]))
            tag, msg = "PROPOSE", f"{e['strategy']} {e['symbol']}: {legs}, limit net {e['limit_net']}"
        elif k == "decision":
            i = intents.get(e["id"], {})
            verdict = "approved" if e["approved"] else "REJECTED: " + "; ".join(map(str, e["reasons"]))
            tag, msg = "RISK", f"{i.get('strategy', '?')} {action(e['id'], i.get('strategy', ''))}: {verdict}" + (f", max loss {e['max_loss']}" if e.get("max_loss") else "")
        elif k == "execution":
            tag = "FILL"
            msg = f"{e.get('strategy', '?')} {action(e['intent_id'], e.get('strategy', ''))}: " + (f"paper fill, net cash {dash._money(e['net_cash'])}, fees {dash._money(e['fee_total'])}" if e["ok"] else f"NOT FILLED: {e['reason']}")
        elif k == "ledger":
            op = e.get("op", "?")
            detail = (f"initial cash {dash._money(e['initial_cash'])}" if op == "init" else
                      f"{e.get('side', '')} {e.get('qty', '')} {leg(e.get('key', ''))} @ {e.get('price', '')}" if op == "trade" else str(e.get("sid", "")))
            tag, msg = "LEDGER", f"{op}: {detail}"
        elif k == "exit_signal":
            extra = ", ".join(f"{k} {e[k]}" for k in ("pnl", "threshold") if e.get(k) is not None)
            tag, msg = "EXIT?", f"{e.get('strategy', '?')} {e.get('underlying', '')}: {e.get('reason', '?')}" + (f" ({extra})" if extra else "")
        elif k == "exit_done":
            tag, msg = "EXIT", f"{e.get('strategy', '?')}: closed by {e.get('reason', '?')}"
        elif k == "health":
            tag, msg = "TICK", f"session {e.get('session', '?')}, open {e.get('open_structures', '?')}, stale {e.get('stale_count', '?')}, equity {dash._money(e['equity']) if e.get('equity') is not None else 'n/a'}"
        elif k == "reconcile":
            tag, msg = "RECON", "ok" if e.get("ok") else "FAILED: " + "; ".join(map(str, e.get("errors", [])))
        elif k == "position_marks":
            tag, msg = "MARKS", f"{e.get('n_positions', '?')} open position(s) valued, {e.get('n_unvalued', '?')} unvalued"
        elif k == "report":
            tag, msg = "REPORT", f"wrote {e.get('name', '?')}"
        elif k == "chain_seen":
            tag, msg = "SOURCE", f"{e.get('source', '?')} {e.get('symbol', '')}" + (" (synthetic, made-up)" if e.get("synthetic") else "")
        else:
            tag, msg = k.upper()[:7], ""
        return {"t": local(e["ts"]), "k": tag, "m": msg, "key": k in KEY_KINDS, "s": owner(e), "sid": sid_of(e)}

    # log: every key event of the run, plus the most recent LOG_WINDOW events of any kind (in journal order, no duplicates)
    keep = sorted({i for i, e in enumerate(events) if e["kind"] in KEY_KINDS} | set(range(max(0, len(events) - LOG_WINDOW), len(events))))
    log = [line(events[i]) for i in keep]

    # the last tick on which the strategies were evaluated
    evals = [e for e in events if e["kind"] in ("no_trade", "intent")]
    last_ts = evals[-1]["ts"] if evals else None
    last_tick = []
    for e in (x for x in evals if x["ts"] == last_ts):
        if e["kind"] == "no_trade":
            who, _, code = e["reason"].partition(":")
            last_tick.append({"strategy": who if code else "do_nothing", "symbol": e.get("symbol", ""), "outcome": "NO TRADE", "reason": reason_text(e["reason"]), "code": code or who})
        else:
            d = next((x for x in events if x["kind"] == "decision" and x["id"] == e["id"]), None)
            x = execs.get(e["id"])
            outcome = "PROPOSED" if d is None else ("REJECTED" if not d["approved"] else ("FILLED" if x and x["ok"] else "APPROVED"))
            last_tick.append({"strategy": e["strategy"], "symbol": e["symbol"], "outcome": outcome, "reason": "; ".join(map(str, (d or {}).get("reasons", []))) or f"limit net {e['limit_net']}", "code": ""})

    decisions = []
    for d in (e for e in events if e["kind"] == "decision"):
        i, x = intents.get(d["id"], {}), execs.get(d["id"])
        decisions.append({"t": local(d["ts"]), "strategy": i.get("strategy", "?"), "symbol": i.get("symbol", ""), "action": action(d["id"], i.get("strategy", "")), "sid": sid_of(d), "owner": owner(d),
                          "approved": bool(d["approved"]), "reasons": [str(r) for r in d["reasons"]], "max_loss": d.get("max_loss"),
                          "filled": None if x is None else bool(x["ok"]), "fill_note": None if x is None else (f"net cash {dash._money(x['net_cash'])}" if x["ok"] else str(x["reason"]))})

    # one summary per strategy: what the last evaluation said, and what it did over the whole run (counts of recorded events)
    names = [x["strategy"] for x in last_tick] + [t["strategy"] for t in m["trades"]]
    strategies = []
    for name in dict.fromkeys(names):
        last = next((x for x in last_tick if x["strategy"] == name), None)
        mine = [t for t in m["trades"] if t["strategy"] == name]
        strategies.append({"name": name, "last": last,
                           "skips": sum(1 for e in events if e["kind"] == "no_trade" and owner(e) == name),
                           "proposed": sum(1 for e in events if e["kind"] == "intent" and e["strategy"] == name),
                           "trades": len(mine), "open": sum(1 for t in mine if t["status"] == "open"), "closed": sum(1 for t in mine if t["status"] != "open")})

    stage = {s["id"]: s for s in m["stages"]}
    steps = {s["id"]: s for s in m["pipeline"]["steps"]}
    h, run, mo = m["headline"], m["run"], m["money"]
    return {
        "meta": {"generated_at": m["generated_at"], "generated_local": m["generated_local"], "optbot_version": m["version"],
                 "fixture": f"optbot replay --synthetic --days {days} --capital-cad {capital_cad} (made-up prices, replay clock)",
                 "journal_events": len(events), "log_window": LOG_WINDOW, "log_key_events": sum(1 for e in events if e["kind"] in KEY_KINDS)},
        "flags": {"simulation": m["banner"]["simulation"], "synthetic": bool(m["freshness"]["synthetic"]), "sources": m["freshness"]["sources"],
                  "mode": m["mode"]["badge"], "mode_text": m["mode"]["text"]},
        "run": {"status": run["status"], "display_state": h["display_state"], "display_text": h["display_text"], "last_tick_local": run["last_tick_local"],
                "progress": h["progress"]["text"], "first_day": h["progress"].get("first_day"), "last_day": h["progress"].get("last_day"), "session": h["session"]["text"], "session_code": h["session"]["raw"]},
        "links": {k: {"name": stage[k]["name"], "state": stage[k]["state"]} for k in stage if k != "simulator"},
        "safety": {"kill_switch": m["blocks"]["kill_switch"], "halts": m["blocks"]["halts"], "stale_count": m["freshness"]["stale_count"],
                   "newest_quote_local": m["freshness"]["newest_quote_local"], "chain_problems": m["retention"]["journal_chain_problems"],
                   "ledger_unavailable": bool(m["ledger_unavailable"])},
        "money": {k: mo[k] for k in ("currency", "label", "starting_capital", "cash", "equity", "equity_partial", "realized", "fees", "unrealized")},
        "pipeline": {k: {"label": steps[k]["label"], "count": steps[k]["count"], "sub": steps[k]["sub"]} for k in steps},
        "trades": [{k: t[k] for k in ("sid", "opened_local", "underlying", "strategy", "legs", "cost_incl_fees", "status", "status_text", "result")} for t in m["trades"]],
        "evaluation": {"last_tick_local": local(last_ts), "last_tick": last_tick, "decisions": decisions,
                       "reasons": [{"label": r["label"], "code": r["code"], "count": r["count"]} for r in ((m.get("rejection_summary") or {}).get("top_reasons") or [])],
                       "ticks": (m.get("rejection_summary") or {}).get("ticks"), "regular_ticks": (m.get("rejection_summary") or {}).get("regular_ticks")},
        "strategies": strategies,
        "log": log,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tree", required=True, help="an extracted optbot tree (the directory that contains src/ and config/), outside this repo")
    ap.add_argument("--days", type=int, default=24)
    ap.add_argument("--capital-cad", default="400000")
    a = ap.parse_args()
    snap = build(Path(a.tree).resolve(), a.days, a.capital_cad)
    text = HTML.read_text(encoding="utf-8")
    i = text.index(OPEN) + len(OPEN)
    j = text.index(CLOSE, i)
    HTML.write_text(text[:i] + "\n" + json.dumps(snap, indent=1, sort_keys=True).replace("</", "<\\/") + "\n" + text[j:], encoding="utf-8")
    print(f"wrote {HTML} ({len(snap['log'])} log lines, {len(snap['trades'])} trades, journal events {snap['meta']['journal_events']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
