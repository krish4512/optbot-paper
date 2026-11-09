# Mission control (PROTOTYPE, for review)

**Simulation only. Synthetic (made-up) data only. A static snapshot: it is not connected to anything and nothing in it is running.**
This is a first visual prototype of a one-screen dashboard. It does not replace `optbot dashboard`, changes no optbot code or
command, and adds no dependency. No edge has been demonstrated; nothing here is a profit, readiness or accessibility claim.

- `mission_control.html`: the whole page (HTML, CSS and plain JavaScript in one file; no network, no external fonts or libraries).
  Open it in a browser as a file.
- `build_snapshot.py`: rewrites the data block inside that file. It runs the project's own synthetic replay in a temporary
  directory, builds the existing dashboard model and reads the journal the replay wrote. Standard library only.

```bash
python3 optbot_v0.6.53_bootstrap.py /tmp/optbot
```

```bash
python3 prototypes/mission_control/build_snapshot.py --tree /tmp/optbot
```

## What the screen shows

One fixed screen, no scrolling anywhere. Lists that do not fit are paged (‹ ›), and every record can be reached.

- **Header**: the bot avatar and its state, three flags (simulation only, synthetic data, static snapshot), and **two different
  clocks**: CAPTURED is the real time the file was generated (its age is computed by your browser); SIMULATED CALENDAR is the
  made-up replay clock inside the synthetic run. Every time in the panels and the log is on the simulated clock. The run's
  calendar can be later than the capture date: those are not real dates and not future trades.
- **Pipeline** (left): the five real optbot stages with their recorded counts. Select a stage to list its records.
- **Overview** (centre): a globe used as a diagram. Circles are strategies, coloured by their last evaluation; filled diamonds
  are open trades (upper ring), hollow diamonds are closed trades (lower ring); a line joins a strategy to each trade it opened.
  Positions are conceptual, not geography and not exposure. Select a node for its recorded reason, trades, risk decisions and
  the linked log lines.
- **Records** (right): trades, the last evaluation of every strategy with its reason, the risk decisions, the skip reasons,
  the status table, and the current selection.
- **Statistics strip** and **event log** (bottom): simulated ledger figures and the recorded journal, oldest first.
- Small screens: three tabs (Overview, Pipeline, Records) above the log. The statistics strip is replaced by Records > Status.

## Motion, and what it does not mean

- The globe's rotation is a visual effect only (3 degrees per second). It does not mean anything is computed, scanned or
  watched. It can be paused, it stops when a node is selected, and it is off when the system asks for reduced motion.
- The sphere is grey and the header says IDLE because the recorded run status is STOPPED. It takes colour, and the bot avatar
  moves, only if the recorded status is RUNNING. Elapsed wall time never animates anything.
- There are no pulses, no scanning, no invented activity. Replay playback is not implemented.

## Where every value comes from

Everything is copied or counted from the synthetic replay's own records by `build_snapshot.py`. Nothing is typed in by hand.

| On screen | Source |
|---|---|
| IDLE / NOT RUNNING, run text | model `run.status`, `headline.display_state` |
| Captured time and age | model `generated_at` (real clock at build time); age = browser clock minus that |
| Simulated calendar, day, last tick, last session | model `headline.progress`, `run.last_tick_local`, `headline.session` |
| Flags, data source, mode | model `banner`, `freshness.sources`, `freshness.synthetic`, `mode` |
| Pipeline stages and counts | model `pipeline.steps` (label, count, sub) |
| Trades (legs, opened, cost, status, result) | model `trades` |
| Strategy nodes: last evaluation and reason | journal `no_trade` / `intent` / `decision` / `execution` events at the last evaluated tick; reason text from the model's `rejection_summary` labels |
| Strategy totals (proposed, skips) | counts of journal `intent` and `no_trade` events |
| Risk decisions | journal `decision` events joined to their `intent` and `execution` by id |
| Skip reasons | model `rejection_summary.top_reasons` |
| Status table and statistics strip | model `money`, `blocks`, `freshness`, `retention`, `ledger_unavailable`, `stages` |
| Event log lines | journal events, summarised field by field (kind, strategy, legs, prices, reasons) |
| Linked log lines | events whose own record names the strategy or the trade (`sid`, intent id) |

Derived here, not recorded as such: the short log wording, the per-strategy counts, the grouping of events by trade, the
positions of the nodes (a layout choice), and the snapshot age. Unavailable values are shown as `unavailable` or `n/a`.

**Kept in the file:** every key event of the run (proposals, risk decisions, fills, ledger entries, exits, reports, data
source) plus the most recent 240 events of any kind. The fixture run has 2,258 journal events; older skip, tick, reconcile and
mark events are not in the file, and the log footer says so.

## Checked, and limits

Checked in headless Chromium (this fixture only) at 1280x800, 1280x720, 1440x900, 390x844 and 390x700: the document and every
panel have scroll size equal to client size, no element is outside the viewport, no text is cut off, every page of every list
adds up to its item count, and selecting each of the 8 globe nodes keeps the read-out, the selection list and the linked log
within their boxes. No network request is made. Smallest text is 10.5 px (labels); body text is 11.5 to 13 px.

Not done: other browsers, real phones, zoomed text, viewports smaller than 390x700, a screen reader, a state other than this
finished synthetic replay (a running, never-run or unreadable-ledger state has not been rendered), light theme, print.
At 390x700 the globe is small (about 90 px across) and node labels can overlap.
