# Margin Watch — a Streamlit dashboard for a regional sales director

**BANA409 — Data App in-class group exercise. Built by Zonghao Yang.**

This is the written answer to Steps 1–4 of the exercise. The app itself is `app.py`
(`uv run streamlit run app.py`); the analysis behind the numbers is `eda.ipynb`; the data file is built
by `prepare_data.py`.

---

## Step 1 — The dataset and the decision-maker

### The dataset

| | |
|---|---|
| **Name / link** | *Global Superstore Data* — <https://www.kaggle.com/datasets/rohitgrewal/global-superstore-data> |
| **What it is** | The classic Global Superstore retail sample, distributed as three sheets: **Orders**, **Returns**, **People** |
| **One row is** | **One line of one order** — a product, a quantity and a discount. An order with three products is three rows. |
| **Period** | **1 Jan 2011 – 31 Dec 2014** (48 complete months) |
| **Size** | 51,290 order lines · 25,035 orders · 1,590 customers · 13 sales reps |
| **Real or synthetic?** | **Synthetic.** It is a teaching/demo sample, not a real company's books. We say so here because it changes how the numbers should be read: the *sizes* are not a real retailer's, but the *patterns* (discounting away the margin) are exactly the ones real retail dashboards exist to catch. |
| **What we committed** | One CSV, `data/superstore.csv` (~13 MB). We joined the **Returns** sheet onto Orders as a `Returned` flag in `prepare_data.py` and committed the joined file rather than the 18 MB workbook — the exercise asks for one small CSV, and we say here that we did it. |

We chose it over a hotel-bookings or SaaS-churn dataset because the decision it supports is a *recurring
money decision*, and because it contains a built-in trap: revenue and profit point in opposite directions.

### The decision-maker — one person, not "everyone"

**The Regional Sales Director of the US market.** One person, four regions (Central, East, South, West),
one weekly meeting where discount requests are approved.

---

## Step 2 — Why this deserves a dashboard

**1. Who looks at it, and how often?**
The US regional sales director, **every Monday morning** while setting that week's discount approvals,
plus whenever a rep asks for an exception on a large order.

**2. What decision does it support?**
*"If the director sees that a region's profit margin is being eaten by order lines discounted more than
30%, they will cap the discount the region's reps may approve without escalation — starting with the
product lines that lose money at those discounts."*

**3. What do they do today, and what does it cost?**
Today they ask finance for a monthly extract, or trust the reps. Both are slow and both miss the point:
finance reports **revenue by region**, which grew every year and therefore looks like good news. The
cost is visible in the data — **10,361 order lines sold at more than 30% off carry $1,547,656 of revenue
and −$793,526 of profit**, and **24.5% of all order lines lose money**. A monthly extract cannot be
filtered to the one region a rep is asking about *this week*, so exceptions get approved on the size of
the deal rather than on its margin.

**4. Why a dashboard rather than a weekly email, a report, or an alert?**
Because the same three numbers have to be re-read for a **different region** each time, and the answer
has to be drillable one level down to a product line. A weekly email is stale by the time the discount
is approved; a one-off report answers last quarter's question and invites no follow-up; an alert can
tell you something is wrong but cannot tell you *which region, which product line, how deep the discount
is* — which is the whole decision. Only an interactive page with a region filter can do that.

---

## Step 3 — What matters, what we cut, and what could mislead

### What the EDA found (full notebook: `eda.ipynb`)

The file is 51,290 lines over 48 complete months, with essentially no missing data except **Postal Code,
missing on 41,296 of 51,290 rows — 4 rows in 5**. Revenue rises every year — 2011 $2.26M → 2014 $4.30M, **+90%**
— and margin goes nowhere: 11.0%, 11.5%, 11.9%, 11.7%. Revenue is not the story.

Discount is. The discount column is **bimodal** — **56.6% of order lines sell at full price** and
another **31.8% sell at 20% off or more** — so its average (14.3%) describes nothing. Sorted into bands,
the margin falls off a cliff:

| Discount band | Order lines | Sales | Profit | Margin | Loss-making lines | Share of sales |
|---|---|---|---|---|---|---|
| 0% | 29,009 | $6,992,411 | $1,770,695 | **+25.3%** | **0.0%** | 55.3% |
| 1–10% | 4,679 | $1,962,619 | $338,189 | +17.2% | 19.3% | 15.5% |
| 11–20% | 6,274 | $1,757,261 | $173,255 | +9.9% | 23.3% | 13.9% |
| 21–30% | 967 | $382,555 | −$21,156 | **−5.5%** | 62.2% | 3.0% |
| **more than 30%** | **10,361** | **$1,547,656** | **−$793,526** | **−51.3%** | **92.5%** | 12.2% |

Inside the US market — the region the director actually owns — the same pattern separates the regions:

| Region | Sales | Margin | Loss-making lines | Lines at 30%+ off |
|---|---|---|---|---|
| **Central** | $501,240 | **7.9%** | **31.9%** | **27.7%** |
| East | $678,781 | 13.5% | 19.4% | 16.2% |
| South | $391,722 | 11.9% | 16.0% | 10.6% |
| **West** | $725,458 | **14.9%** | **9.9%** | **3.7%** |

Central discounts deeply and keeps far less of what it sells: it earns **$39,706 on $501,240 of sales**,
while West earns **$108,418 on $725,458** — roughly a third of the profit on two thirds of the revenue.
At product level the single loss-maker is **Tables: −$64,083 at an average 29% discount**.

The US market totals the page opens on: **$2.30M sales, 12.5% margin, 18.7% of order lines sold below
cost.**

### The three headline numbers

1. **Sales** — context, and the number a discount decision is measured against.
2. **Profit margin %** — the headline. It answers "is anything wrong right now?" with one figure, and it
   is the number revenue growth hides.
3. **Order lines sold below cost %** — the alarm. 18.7% across the US market, 31.9% in Central.

Sales alone would be the *wrong* headline here: it grew every year of the sample.

### The supporting charts (two, and why these two)

1. **Margin by discount depth.** This is the mechanism behind number 2. It is the chart that answers
   *why* the margin is where it is, and it points at a lever — the discount — that the director can
   actually move, unlike product cost or shipping.
2. **Margin by product line.** Once the director believes the discount story, the next question is
   *where to start*, and this chart answers it: the sub-categories whose bars sit below zero.

### The filter (one)

**Region.** The director owns four of them and nothing else; a filter for city, segment or ship mode
would change the audience from a person to a report.

### Two things we chose NOT to show

1. **A world map of sales by country.** It is the prettiest thing in this dataset and it would not change
   a single decision: country totals do not tell the director which discount to cap, and the country
   names are not standardised. It would take the top of the page and bury the margin number.
2. **A top-10 customers table.** With 1,590 customers, a leaderboard invites one-off exceptions — "keep
   this customer happy" — when the decision the dashboard exists to support is a *policy* about discount
   depth. The detail table we did keep is by product line, because that is where the policy lands.

### What could mislead the reader, and how the page handles it

- **Revenue is gross of returns.** 1,172 of 25,035 orders (4.7%) were returned, and the refunds are
  stored as a flag on the order, not as negative rows — so every sales figure is optimistic. *Handled:*
  a caption under the table states it, rather than quietly netting it off and losing the traceability.
- **"Average discount" is meaningless on this data** (bimodal), so the page never shows it as a headline;
  discounts appear only as bands, and as a per-row average in the table with the band chart beside it.
- **A loss-making *share* counts a −$3 line the same as a −$30,000 one.** *Handled:* the dollar loss is
  always shown beside the share — in the band labels and in the table's `Profit` column.
- **Postal Code is missing on 4 rows in 5.** *Handled:* the page never groups by it — the lowest
  geography it uses is region. A postcode map would have looked precise and been built on 20% of the data.
- **The data is synthetic.** *Handled:* stated in Step 1 and in the last caption of the page, so nobody
  quotes these specific dollar amounts as a real retailer's.

### The order of the page, top to bottom

**Top** — title, the one-line "who this is for", the data period line, and the three numbers: the answer
to "is anything wrong right now?". **Middle** — the two charts that explain *why* those numbers are what
they are. **Bottom** — the ten worst product lines for whoever wants to dig in, then the caveats. Many
readers never scroll, so nothing a decision needs sits below the fold.

---

## Step 4 — How fresh the numbers need to be

**Answered:** orders and returns land in the order system **nightly**. The director reviews this page
**every Monday morning**, in the meeting where the week's discount approvals are set, and again when a
rep requests an exception. Nightly is the right cadence because the *decision* is weekly and the data
only changes when an order closes; **real-time refresh would add cost and change no decision**, because
nobody caps a discount at 3pm because the margin moved at 2pm.

**The one exception:** if the share of order lines sold at more than 30% off in any single region crosses
its four-year maximum in a week, that should leave the dashboard as a **same-day alert** rather than wait
for Monday — it means a rep has changed behaviour between reviews, which is exactly the thing the director
is trying to control.

**Line on the page:**
*Data: Jan 2011 – Dec 2014 (Global Superstore sample, Kaggle snapshot) · In production: refreshed nightly
from the order system; reviewed Monday morning when the week's discount approvals are set.*

---

## Running it

```bash
uv run streamlit run app.py                  # http://localhost:8501
uv run python test_app.py                    # checks the six required elements
uv run --with xlrd python prepare_data.py    # rebuilds data/superstore.csv (workbook not committed)
```

Deployed on Streamlit Cloud with **Python 3.14**.
