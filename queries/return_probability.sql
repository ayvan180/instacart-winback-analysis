-- For each user, compute the maximum gap that appears in their history.
-- A user who has a 5-day gap somewhere "survived" the 5-day mark.
-- A user who never has a gap >= 10 days "did not survive" past 10.
-- 
-- Return probability at gap X = 
--    P(user has at least one gap >= X+1 | user has at least one gap >= X)
--
-- We compute the survival curve: P(reaching gap X) for X = 1..30

WITH user_max_gap AS (
    SELECT 
        user_id,
        MAX(days_since_prior_order) AS max_gap
    FROM orders
    WHERE days_since_prior_order IS NOT NULL
    GROUP BY user_id
),
gap_bins AS (
    SELECT UNNEST(generate_series(1, 30)) AS gap_threshold
),
survival AS (
    SELECT 
        gb.gap_threshold,
        COUNT(CASE WHEN umg.max_gap >= gb.gap_threshold THEN 1 END) AS users_reached,
        COUNT(*) AS total_users
    FROM gap_bins gb
    CROSS JOIN user_max_gap umg
    GROUP BY gb.gap_threshold
)
SELECT 
    gap_threshold,
    users_reached,
    total_users,
    ROUND(users_reached * 100.0 / total_users, 2) AS pct_reached
FROM survival
ORDER BY gap_threshold;