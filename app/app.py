import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

AGG = Path(__file__).parent / "aggregates"
SLATE = "#8FA3B5"   # sessions / volume
TEAL = "#1F6F78"    # baseline / healthy
RISK = "#C2255C"    # money at risk
INK = "#16222E"
HIGH_BANDS = ["4. 500-1000", "5. 1000+"]
BAND_ORDER = ["1. under 100", "2. 100-250", "3. 250-500", "4. 500-1000", "5. 1000+"]

st.set_page_config(page_title="Growth Analyst Copilot", layout="wide")

if not (AGG / "funnel.csv").exists():
    st.error("Dashboard data not found. Run `python build_aggregates.py` from the project folder first.")
    st.stop()


@st.cache_data
def load(name):
    return pd.read_csv(AGG / f"{name}.csv")


def n(x):
    return f"{int(round(x)):,}"


def money(x):
    x = float(x)
    if x >= 1e9:
        return f"{x / 1e9:.2f}B"
    if x >= 1e6:
        return f"{x / 1e6:.1f}M"
    if x >= 1e3:
        return f"{x / 1e3:.0f}K"
    return f"{x:.0f}"


def style(fig, height=380):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=90, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


funnel = load("funnel").iloc[0]
daily = load("daily")
cats = load("categories")
subs = load("subcategories")
bands = load("price_bands")

total = funnel["total_sessions"]
viewed = funnel["viewed"]
carted = funnel["carted"]
bought = funnel["bought_after_cart"]
abandoned = carted - bought

with st.sidebar:
    st.header("How to read this")
    st.write("**Session**: one visit to the store, as recorded in the event log.")
    st.write("**Carted session**: a session that viewed a product and added one to the cart.")
    st.write("**Abandoned cart**: a carted session with no purchase in the same session.")
    st.write(
        "**Revenue at risk**: the price of the most expensive item in each abandoned cart, "
        "added up. It is an upper bound, because some shoppers come back and buy later."
    )
    st.write("Revenue is in the dataset's own price units.")
    st.caption("Data: eCommerce behavior data from a multi-category store (Kaggle, Open CDP), November 2019.")

st.title("Growth Analyst Copilot")
st.write(
    "Where an online store loses shoppers between viewing and buying, and how much money sits in the carts "
    "that never check out. One month of real event data, analysed at session level."
)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Categories", "Price and revenue", "A/B test planner"])

# ------------------------------------------------------------------ Overview
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sessions", n(total))
    c2.metric("Sessions with a purchase", f"{funnel['any_purchase'] / total:.1%}")
    c3.metric("Cart to purchase", f"{bought / carted:.1%}")
    c4.metric("Abandoned carts", n(abandoned))

    left, right = st.columns([2, 3])
    with left:
        fig = go.Figure(
            go.Funnel(
                y=["Viewed a product", "Added to cart", "Bought"],
                x=[viewed, carted, bought],
                texttemplate="%{value:,.0f}<br>%{percentPrevious:.1%}",
                marker=dict(color=[SLATE, TEAL, TEAL]),
            )
        )
        fig.update_layout(title="Session funnel")
        st.plotly_chart(style(fig), width="stretch")
    with right:
        d = daily.copy()
        d["day"] = pd.to_datetime(d["day"])
        d["rate"] = d["any_purchase"] / d["sessions"]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=d["day"], y=d["sessions"], name="Sessions", marker_color=SLATE, opacity=0.3),
            secondary_y=True,
        )
        fig.add_trace(
            go.Scatter(x=d["day"], y=d["rate"], name="Sessions with a purchase", mode="lines+markers",
                       line=dict(color=TEAL, width=3)),
            secondary_y=False,
        )
        bf = pd.Timestamp("2019-11-29")
        if d["day"].min() <= bf <= d["day"].max():
            fig.add_shape(type="line", x0=bf, x1=bf, y0=0, y1=1, yref="paper",
                          line=dict(color=RISK, dash="dash", width=1.5))
            fig.add_annotation(x=bf, y=1.0, yref="paper", text="Black Friday", showarrow=False,
                               xanchor="right", font=dict(color=RISK))
        fig.update_yaxes(tickformat=".1%", secondary_y=False, title_text="Purchase rate")
        fig.update_yaxes(secondary_y=True, title_text="Sessions", showgrid=False)
        fig.update_layout(title="Daily purchase rate and traffic")
        st.plotly_chart(style(fig), width="stretch")

# ---------------------------------------------------------------- Categories
with tab2:
    st.subheader("Which categories lose the most?")
    metric = st.radio("Rank categories by", ["Abandoned carts", "Revenue at risk"], horizontal=True)
    col = "abandoned_sessions" if metric == "Abandoned carts" else "revenue_at_risk"
    color = SLATE if metric == "Abandoned carts" else RISK
    top = cats.sort_values(col).tail(12)
    fig = go.Figure(go.Bar(x=top[col], y=top["category"], orientation="h", marker_color=color))
    fig.update_layout(title=f"Top categories by {metric.lower()}")
    st.plotly_chart(style(fig, 420), width="stretch")

    t = cats.copy()
    t["View to cart"] = (t["carted_sessions"] / t["viewed_sessions"]).map("{:.1%}".format)
    t["Cart to purchase"] = (t["bought_sessions"] / t["carted_sessions"]).map("{:.1%}".format)
    t["Viewed sessions"] = t["viewed_sessions"].map(n)
    t["Abandoned carts"] = t["abandoned_sessions"].map(n)
    t["Revenue at risk"] = t["revenue_at_risk"].map(money)
    t = t.rename(columns={"category": "Category"})
    st.dataframe(
        t[["Category", "Viewed sessions", "View to cart", "Cart to purchase", "Abandoned carts", "Revenue at risk"]],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "A session can touch several categories, so these rows do not add up to the overall funnel. "
        "Events without a category are left out."
    )

# ------------------------------------------------------------ Price and revenue
with tab3:
    st.subheader("Where is the money, by price?")
    options = sorted(subs["category_code"])
    default = "electronics.smartphone" if "electronics.smartphone" in options else (
        subs.sort_values("revenue_at_risk")["category_code"].iloc[-1]
    )
    code = st.selectbox("Product category", options, index=options.index(default))

    b = bands[bands["category_code"] == code].set_index("price_band").reindex(BAND_ORDER).fillna(0).reset_index()
    tot_ab = b["abandoned_sessions"].sum()
    tot_rev = b["revenue_at_risk"].sum()

    if tot_ab == 0 or tot_rev == 0:
        st.info("No abandoned carts with a price in this category.")
    else:
        b["share_ab"] = b["abandoned_sessions"] / tot_ab
        b["share_rev"] = b["revenue_at_risk"] / tot_rev
        label = b["price_band"].str.replace(r"^\d\. ", "", regex=True)
        fig = go.Figure()
        fig.add_bar(x=label, y=b["share_ab"], name="Share of abandoned carts", marker_color=SLATE)
        fig.add_bar(x=label, y=b["share_rev"], name="Share of revenue at risk", marker_color=RISK)
        fig.update_layout(barmode="group", title=f"{code}: carts versus money, by price band")
        fig.update_yaxes(tickformat=".0%")
        fig.update_xaxes(title_text="Price of the most expensive item in the cart")
        st.plotly_chart(style(fig), width="stretch")

        hi = b[b["price_band"].isin(HIGH_BANDS)]
        st.info(
            f"Carts priced 500 or more are **{hi['share_ab'].sum():.0%}** of abandoned carts "
            f"but **{hi['share_rev'].sum():.0%}** of the revenue at risk."
        )

        t = pd.DataFrame(
            {
                "Price band": label,
                "Carted sessions": b["carted_sessions"].map(n),
                "Abandoned carts": b["abandoned_sessions"].map(n),
                "Cart to purchase": (1 - b["abandoned_sessions"] / b["carted_sessions"].replace(0, float("nan")))
                .map("{:.1%}".format),
                "Revenue at risk": b["revenue_at_risk"].map(money),
            }
        )
        st.dataframe(t, hide_index=True, width="stretch")
        st.caption("Revenue at risk is an upper bound: some shoppers return and buy in a later session.")

# ------------------------------------------------------------- A/B test planner
with tab4:
    st.subheader("Plan an A/B test for high-priced carts")
    st.write(
        "Test an idea (for example a payment-plan prompt) on carts priced 500 or more. "
        "Defaults come from the category chosen on the previous tab."
    )
    hb = bands[(bands["category_code"] == code) & (bands["price_band"].isin(HIGH_BANDS))]
    seg_carts = hb["carted_sessions"].sum()
    seg_base = 1 - hb["abandoned_sessions"].sum() / seg_carts if seg_carts > 0 else 0.40
    seg_daily = max(100, int(round(seg_carts / 30))) if seg_carts > 0 else 1000

    a, b_, c = st.columns(3)
    base = a.number_input("Baseline cart to purchase rate (%)", 1.0, 95.0, float(round(100 * seg_base, 1)), 0.5) / 100
    mde = b_.slider("Smallest lift worth detecting (percentage points)", 0.5, 5.0, 2.0, 0.5) / 100
    daily_n = c.number_input("Eligible carted sessions per day", 50, 5_000_000, seg_daily, 100)
    d1, d2 = st.columns(2)
    power = d1.select_slider("Power (chance of detecting a real lift)", [0.7, 0.8, 0.9], value=0.8)
    alpha = d2.select_slider("Significance level", [0.01, 0.05, 0.10], value=0.05)

    if base + mde >= 1:
        st.error("Baseline plus lift must stay below 100%.")
    else:
        solver = NormalIndPower()

        def per_group(lift):
            eff = proportion_effectsize(base + lift, base)
            return math.ceil(solver.solve_power(eff, alpha=alpha, power=power, ratio=1.0, alternative="two-sided"))

        size = per_group(mde)
        days = max(7, math.ceil(2 * size / daily_n))
        extra = daily_n * 30 * mde

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Sessions per group", n(size))
        m2.metric("Sessions in total", n(2 * size))
        m3.metric("Run time", f"{days} days")
        m4.metric("Extra purchases per month if the lift is real", n(extra))

        lifts = [x / 200 for x in range(1, 11) if base + x / 200 < 1]
        fig = go.Figure(go.Scatter(x=[x * 100 for x in lifts], y=[per_group(x) for x in lifts],
                                   mode="lines+markers", line=dict(color=TEAL, width=3), name="Sessions per group"))
        fig.add_trace(go.Scatter(x=[mde * 100], y=[size], mode="markers", name="Your choice",
                                 marker=dict(color=RISK, size=14)))
        fig.update_xaxes(title_text="Lift to detect (percentage points)")
        fig.update_yaxes(title_text="Sessions per group")
        fig.update_layout(title="Smaller lifts need far more traffic")
        st.plotly_chart(style(fig), width="stretch")
        st.caption(
            "Runs at least 7 days to cover weekday and weekend behaviour. "
            "The extra-purchases figure assumes the lift is real; it is an illustration, not a result."
        )
