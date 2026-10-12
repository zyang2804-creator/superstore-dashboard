#!/usr/bin/env python3
"""
Check app.py against the six elements the exercise requires (Step 5).

Run:  uv run python test_app.py

Uses Streamlit's own AppTest, so the app is actually executed — no screenshots, no guessing.
"""
from streamlit.testing.v1 import AppTest

APP = "app.py"
TEAM_NAME = "Zonghao Yang"   # keep this in sync with app.py


def run(region=None):
    at = AppTest.from_file(APP, default_timeout=180).run()
    if at.exception:
        raise SystemExit(f"app raised: {at.exception[0].value}")
    if region is not None:
        at.sidebar.selectbox[0].select(region).run()
        if at.exception:
            raise SystemExit(f"app raised after selecting {region}: {at.exception[0].value}")
    return at


at = run()
caps = " ".join(c.value for c in at.caption)
metrics = [(m.label, m.value) for m in at.get("metric")]
charts = len(at.get("image"))

checks = [
    ("1. title with the team name", len(at.title) == 1 and TEAM_NAME in at.title[0].value),
    ("2. one-line caption: who it is for and what it decides",
     "regional sales director" in caps and "into losses" in caps),
    ("3. headline metrics via st.metric", len(metrics) == 3 and
     [l for l, _ in metrics] == ["Sales", "Profit margin", "Order lines sold below cost"]),
    ("4. at least one supporting chart", charts >= 1),
    ("5. one filter, the region selector",
     len(at.selectbox) == 1 and at.sidebar.selectbox[0].label == "Region"),
    ("6. data period and refresh frequency line",
     "Jan 2011 - Dec 2014" in caps and "refreshed nightly" in caps and "Monday" in caps),
]

print("Six required elements")
for label, good in checks:
    print(f"  {'PASS' if good else 'FAIL'}  {label}")
print(f"   metrics: {metrics}")
print(f"   charts rendered: {charts}")

print("\nThe filter has to change what the page says")
seen = {}
for region in ["All regions", "Central", "East", "South", "West"]:
    a = run(region)
    m = [(x.label, x.value) for x in a.get("metric")]
    seen[region] = (m[0][1], m[1][1], m[2][1])
    print(f"   {region:<12} sales {m[0][1]:>7}   margin {m[1][1]:>6}   below cost {m[2][1]:>6}")
distinct = len(set(seen.values()))
print(f"   {distinct} distinct results across 5 region choices"
      + ("  <- filter works" if distinct == 5 else "  <- WARNING: filter may not be wired up"))

failed = [l for l, g in checks if not g]
print("\n" + ("all six elements present" if not failed else f"MISSING: {failed}"))
raise SystemExit(0 if not failed else 1)
