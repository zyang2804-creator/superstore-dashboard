"""
Margin Watch — a one-page dashboard for the US regional sales director of Global Superstore.

BANA409 Data App in-class group exercise. See README.md for the written answers to Steps 1-4.
"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

plt.style.use("seaborn-v0_8")

# ---------------------------------------------------------------------------
TEAM_NAME = "teamfin"            # <- your team name goes here
APP_TITLE = "Margin Watch"
MARKET = "US"                    # the director owns the US market only
DATA_PERIOD = "Data: Jan 2011 - Dec 2014 (Global Superstore sample, Kaggle snapshot)"
REFRESH = ("In production: refreshed nightly from the order system; reviewed Monday morning when the "
           "week's discount approvals are set.")
# ---------------------------------------------------------------------------

st.set_page_config(page_title=f"{APP_TITLE} - {TEAM_NAME}", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("data/superstore.csv", parse_dates=["Order Date", "Ship Date"])
    df["Discount band"] = pd.cut(
        df.Discount, [-0.001, 0.0, 0.1, 0.2, 0.3, 1.0],
        labels=["0%", "1-10%", "11-20%", "21-30%", "more than 30%"])
    return df


df = load_data()
us = df[df.Market == MARKET]

# --- the one filter the director actually uses -----------------------------
regions = ["All regions"] + sorted(us.Region.unique())
chosen = st.sidebar.selectbox("Region", regions)
view = us if chosen == "All regions" else us[us.Region == chosen]

# --- 1. title with the team name, 2. one-line caption ----------------------
st.title(f"{APP_TITLE} - {TEAM_NAME}")
st.caption(
    f"For the **US regional sales director** of a global retailer: which discounts are turning the "
    f"region's orders into losses, and how deep they can safely go. "
    f"Showing: **{chosen}**. Use the sidebar to switch region."
)
st.caption(f"{DATA_PERIOD}  ·  {REFRESH}")

# --- 3. three headline numbers --------------------------------------------
market_margin = us.Profit.sum() / us.Sales.sum() * 100
margin = view.Profit.sum() / view.Sales.sum() * 100
loss_share = (view.Profit < 0).mean() * 100
market_loss_share = (us.Profit < 0).mean() * 100
deep_share = (view.Discount >= 0.3).mean() * 100

# a comparison against the whole market only means something once a region is picked
show_delta = chosen != "All regions"
c1, c2, c3 = st.columns(3)
c1.metric("Sales", f"${view.Sales.sum() / 1e6:,.2f}M",
          f"{view['Order ID'].nunique():,} orders", delta_color="off")
c2.metric("Profit margin", f"{margin:.1f}%",
          f"{margin - market_margin:+.1f} pts vs US market" if show_delta else None)
c3.metric("Order lines sold below cost", f"{loss_share:.1f}%",
          f"{loss_share - market_loss_share:+.1f} pts vs US market" if show_delta else None,
          delta_color="inverse")

st.divider()

# --- 4. the supporting charts ---------------------------------------------
left, right = st.columns([1, 1])

with left:
    st.subheader("Why: margin by discount depth")
    band = view.groupby("Discount band", observed=True).agg(
        sales=("Sales", "sum"), profit=("Profit", "sum"), lines=("Profit", "size"))
    band["margin"] = band.profit / band.sales * 100
    band["share"] = band.sales / view.Sales.sum() * 100

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    colors = ["#54A24B" if m > 0 else "#E45756" for m in band.margin]
    bars = ax.bar(band.index.astype(str), band.margin, color=colors)
    ax.axhline(0, color="black", lw=0.8)
    for b, m, s in zip(bars, band.margin, band.share):
        ax.text(b.get_x() + b.get_width() / 2, m + (2 if m >= 0 else -6),
                f"{m:.0f}%\n{s:.0f}% of sales", ha="center", fontsize=8)
    ax.set_ylabel("Profit margin %")
    ax.set_ylim(band.margin.min() - 16, band.margin.max() + 16)
    ax.set_title("")
    plt.tight_layout()
    st.pyplot(fig)

    worst = band.loc[band.margin.idxmin()] if len(band) else None
    if worst is not None:
        st.caption(f"The band that loses the most is **{band.margin.idxmin()}**, "
                   f"{worst.share:.0f}% of this view's sales at {worst.margin:.0f}% margin.")

with right:
    st.subheader("Where: margin by product line")
    sub = view.groupby("Sub-Category").agg(
        sales=("Sales", "sum"), profit=("Profit", "sum"), discount=("Discount", "mean"))
    sub["margin"] = sub.profit / sub.sales * 100
    sub = sub.sort_values("margin")

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.barh(sub.index, sub.margin,
            color=["#E45756" if m < 0 else ("#F58518" if m < 10 else "#54A24B") for m in sub.margin])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Profit margin %")
    ax.tick_params(axis="y", labelsize=7)
    plt.tight_layout()
    st.pyplot(fig)

    st.caption("Bars under zero are product lines sold below cost. The lever is the discount on the "
               "worst bar, not the product itself.")

# --- bottom: detail for whoever wants to dig in ---------------------------
st.subheader("The ten product lines losing the most money in this view")
tbl = (view.groupby("Sub-Category")
       .agg(**{"Order lines": ("Profit", "size"),
               "Average discount": ("Discount", "mean"),
               "Sales": ("Sales", "sum"),
               "Profit": ("Profit", "sum")})
       .sort_values("Profit").head(10))
tbl["Average discount"] = (tbl["Average discount"] * 100).round(1).astype(str) + "%"
tbl["Margin %"] = (tbl.Profit / tbl.Sales * 100).round(1)
st.dataframe(
    tbl.style.format({"Sales": "${:,.0f}", "Profit": "${:,.0f}", "Margin %": "{:.1f}%"}),
    width='stretch')

# --- what could mislead the reader ---------------------------------------
st.caption(
    "**Read with care:** sales are **gross of returns** — 4.7% of orders are returned and the refund is "
    "not stored as a negative row, so revenue here is slightly optimistic. `Postal Code` is missing on "
    "4 rows in 5, so this page never groups by it. A line lost at -$3 and one lost at -$30,000 count the "
    "same in the loss-share metric, which is why the dollar figure sits next to it in the table."
)
st.caption(f"Dataset: Global Superstore sample (Kaggle). Built by {TEAM_NAME} for BANA409.")
