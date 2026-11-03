WITH sc AS (
  SELECT
    user_session,
    split_part(category_code, '.', 1) AS category,
    MAX((event_type = 'view')::INT)     AS viewed,
    MAX((event_type = 'cart')::INT)     AS carted,
    MAX((event_type = 'purchase')::INT) AS purchased
  FROM 'data/nov.parquet'
  WHERE category_code IS NOT NULL
  GROUP BY 1, 2
)
SELECT
  category,
  SUM(viewed) AS viewed_sessions,
  ROUND(100.0 * SUM(viewed * carted) / SUM(viewed), 2) AS view_to_cart_pct,
  ROUND(100.0 * SUM(viewed * carted * purchased) / NULLIF(SUM(viewed * carted), 0), 2) AS cart_to_purchase_pct
FROM sc
GROUP BY 1
HAVING SUM(viewed) > 100000
ORDER BY viewed_sessions DESC;
