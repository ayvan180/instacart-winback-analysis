"""
Generate the 3 figures used in the dashboard and README.
Run once: python generate_figures.py

Requires Jupyter to be shut down (releases DuckDB lock).
"""

import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Setup
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False
sns.set_style("whitegrid")

FIGURES_DIR = Path("figures")
FIGURES_DIR.mkdir(exist_ok=True)

con = duckdb.connect("analysis.duckdb", read_only=True)
print("Connected to DuckDB.")

# ---------- Pull data ----------
print("Computing survival data...")
survival_df = con.execute("""
    WITH user_max_gap AS (
        SELECT user_id, MAX(days_since_prior_order) AS max_gap
        FROM orders
        WHERE days_since_prior_order IS NOT NULL
        GROUP BY user_id
    ),
    gap_bins AS (SELECT UNNEST(generate_series(1, 30)) AS gap_threshold)
    SELECT 
        gb.gap_threshold,
        COUNT(CASE WHEN umg.max_gap >= gb.gap_threshold THEN 1 END) AS users_reached,
        COUNT(*) AS total_users,
        ROUND(COUNT(CASE WHEN umg.max_gap >= gb.gap_threshold THEN 1 END) * 100.0 
              / COUNT(*), 2) AS pct_reached
    FROM gap_bins gb
    CROSS JOIN user_max_gap umg
    GROUP BY gb.gap_threshold
    ORDER BY gap_threshold
""").fetchdf()

survival_df['next_reached'] = survival_df['users_reached'].shift(-1)
survival_df['drop_rate'] = (100 - survival_df['next_reached'] / survival_df['users_reached'] * 100).round(2)

print("Computing per-order data...")
per_order_df = con.execute("""
    SELECT 
        total_orders,
        COUNT(*) AS n_users,
        ROUND(AVG(CASE WHEN max_gap = 30 THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_gap_30
    FROM user_segments
    WHERE total_orders <= 50
    GROUP BY total_orders
    ORDER BY total_orders
""").fetchdf()

# ---------- Figure 1: Survival curve ----------
print("Saving survival.png...")
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(survival_df['gap_threshold'], survival_df['pct_reached'],
        marker='o', linewidth=2, color='steelblue')
ax.axvline(x=14, color='red', linestyle='--', alpha=0.5, label='Recommended trigger (day 14)')
ax.set_xlabel('Days since prior order')
ax.set_ylabel('% of users reaching this gap')
ax.set_title('Survival: probability of reaching gap X')
ax.legend()
fig.tight_layout()
fig.savefig(FIGURES_DIR / "survival.png", dpi=120, bbox_inches='tight')
plt.close(fig)

# ---------- Figure 2: Hazard ----------
print("Saving hazard.png...")
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(survival_df['gap_threshold'], survival_df['drop_rate'],
       color='indianred', alpha=0.7)
ax.axvline(x=14, color='red', linestyle='--', alpha=0.5)
ax.set_xlabel('Days since prior order')
ax.set_ylabel("Drop rate (% who don't reach next day)")
ax.set_title('Hazard: probability of churning at each gap')
fig.tight_layout()
fig.savefig(FIGURES_DIR / "hazard.png", dpi=120, bbox_inches='tight')
plt.close(fig)

# ---------- Figure 3: Inverted-U ----------
print("Saving inverted_u.png...")
fig, ax1 = plt.subplots(figsize=(10, 5))

color1 = 'tab:blue'
ax1.set_xlabel('Total orders placed by user')
ax1.set_ylabel('% with at least one 30-day gap', color=color1)
ax1.plot(per_order_df['total_orders'], per_order_df['pct_gap_30'],
         marker='o', color=color1, linewidth=2, label='30-day gap rate')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.axvspan(8, 19, alpha=0.15, color='red', label='Danger zone (8-19 orders)')

ax2 = ax1.twinx()
color2 = 'tab:gray'
ax2.set_ylabel('Users in segment', color=color2)
ax2.bar(per_order_df['total_orders'], per_order_df['n_users'],
        alpha=0.2, color=color2)
ax2.tick_params(axis='y', labelcolor=color2)

ax1.set_title('30-day gap rate by user tenure: an inverted-U pattern')
fig.tight_layout()
fig.savefig(FIGURES_DIR / "inverted_u.png", dpi=120, bbox_inches='tight')
plt.close(fig)

con.close()
print("\nDone. Three figures saved to figures/")