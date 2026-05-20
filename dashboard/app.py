"""
Instacart Win-Back Trigger Analysis — Interactive Dashboard

Run with: streamlit run dashboard/app.py
Requires: figures/{survival,hazard,inverted_u}.png — generate with `python generate_figures.py`
"""

import streamlit as st
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(
    page_title="Win-Back Trigger Analysis",
    page_icon="📦",
    layout="wide"
)

# ---------- Paths ----------
PROJECT_ROOT = Path(__file__).parent.parent
FIGURES = PROJECT_ROOT / "figures"

# ---------- Header ----------
st.title("Win-Back Trigger Analysis")
st.markdown(
    "**Question:** Past what reorder gap does a user become unlikely to return — "
    "and should the trigger threshold be segmented by user tenure?"
)
st.markdown("Analysis of 3.4M orders across 206k Instacart users.")
st.divider()

# ---------- Section 1 ----------
st.header("1. Survival curve: when do users disappear?")

col1, col2 = st.columns(2)
with col1:
    st.image(str(FIGURES / "survival.png"), use_container_width=True)
with col2:
    st.image(str(FIGURES / "hazard.png"), use_container_width=True)

st.info(
    "**Finding:** No single sharp elbow exists in the observable range. "
    "Drop rate climbs gradually from day 7 onwards with multiple similar inflection candidates. "
    "Day 14 selected as conservative starting hypothesis (first gap where drop rate exceeds 1%)."
)

st.divider()

# ---------- Section 2 ----------
st.header("2. Who's actually at risk?")

col3, col4 = st.columns([2, 1])
with col3:
    st.image(str(FIGURES / "inverted_u.png"), use_container_width=True)
with col4:
    st.markdown("**Why this matters**")
    st.markdown(
        "The 30-day-gap rate peaks among users with 8-19 orders, then *declines* "
        "for heavier users. If gap rate were just a function of more chances to record one, "
        "the curve would monotonically rise — instead it has a clear inverted-U shape."
    )
    st.markdown(
        "**Translation:** users in the 8-19 order band are the ones still forming "
        "a habit but not yet locked in. They are where retention interventions have "
        "the highest expected impact."
    )

st.divider()

# ---------- Section 3 ----------
st.header("3. Recommendation")

st.markdown(
    """
    A single global win-back trigger threshold is suboptimal. Instead:
    
    | Segment | Suggested action | Rationale |
    |---|---|---|
    | **Light users (≤7 orders)** | Invest in onboarding, not win-back | Most are not-yet-engaged trialists; win-back is wasted spend |
    | **Medium users (8-19 orders)** | Aggressive win-back at day 14 | Habit forming, at real risk, intervention has highest expected lift |
    | **Heavy users (20+ orders)** | Light-touch reminder at day 21+, if anything | Self-recovering; aggressive win-back risks signal-jamming |
    
    **Next steps in production:**
    - A/B test day-7 vs day-14 vs day-21 triggers on the medium segment
    - Re-run with uncapped timestamps and proper Kaplan-Meier survival framework
    - Test creative/offer variations within the trigger window (push vs email vs WhatsApp)
    """
)

st.divider()

# ---------- Section 4 ----------
with st.expander("Methodology and limitations"):
    st.markdown(
        """
        - **Right-censoring:** Instacart caps `days_since_prior_order` at 30. We cannot 
          distinguish a 30-day pause from a 90-day disappearance, which would matter for 
          truly understanding the back-end of the churn curve.
        - **Max-gap-per-user proxy:** A user who paused once for 14 days and then ordered 
          50 more times is not the same as a user who paused for 14 days and never returned. 
          Our metric conflates these. A production analysis would use Kaplan-Meier survival 
          on per-order intervals.
        - **Dataset characteristics:** US Instacart, 2017, single grocery vertical. 
          Generalization to other quick-commerce categories (or to India 2026 specifically) 
          requires re-running on local data.
        - **Sample-size caveat at high tenure:** Users with 30+ orders have small n (1k-2k 
          per tenure value), so the right side of the inverted-U is noisier than the left.
        """
    )

st.caption("Source: Instacart Market Basket Analysis (public dataset). Analysis by Navya Agarwal.")