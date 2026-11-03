WITH s AS (
  SELECT
    user_session,
    MAX((event_type = 'view')::INT)     AS viewed,
    MAX((event_type = 'cart')::INT)     AS carted,
    MAX((event_type = 'purchase')::INT) AS purchased
  FROM 'data/nov.parquet'
  GROUP BY 1
)
SELECT
  COUNT(*)                         AS total_sessions,
  SUM(viewed)                      AS viewed,
  SUM(viewed * carted)             AS viewed_then_carted,
  SUM(viewed * carted * purchased) AS full_funnel,
  SUM(purchased)                   AS any_purchase
FROM s;
