WITH sc AS (
  SELECT
    user_session,
    category_code,
    MAX((event_type = 'view')::INT)     AS viewed,
    MAX((event_type = 'cart')::INT)     AS carted,
    MAX((event_type = 'purchase')::INT) AS purchased
  FROM 'data/nov.parquet'
  WHERE category_code LIKE 'electronics.%'
  GROUP BY 1, 2
)
SELECT
  category_code,
  SUM(viewed) AS viewed_sessions,
  SUM(viewed * carted) AS carted_sessions,
  SUM(viewed * carted * (1 - purchased)) AS abandoned_sessions,
  ROUND(100.0 * SUM(viewed * carted * purchased) / NULLIF(SUM(viewed * carted), 0), 2) AS cart_to_purchase_pct
FROM sc
GROUP BY 1
HAVING SUM(viewed * carted) > 5000
ORDER BY abandoned_sessions DESC
LIMIT 15;
