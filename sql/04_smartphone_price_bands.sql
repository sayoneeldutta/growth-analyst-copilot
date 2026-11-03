WITH s AS (
  SELECT
    user_session,
    MAX(CASE WHEN event_type = 'cart' THEN price END) AS max_cart_price,
    MAX((event_type = 'cart')::INT)     AS carted,
    MAX((event_type = 'purchase')::INT) AS purchased
  FROM 'data/nov.parquet'
  WHERE category_code = 'electronics.smartphone' AND price > 0
  GROUP BY 1
)
SELECT
  CASE
    WHEN max_cart_price < 100  THEN '1. under 100'
    WHEN max_cart_price < 250  THEN '2. 100-250'
    WHEN max_cart_price < 500  THEN '3. 250-500'
    WHEN max_cart_price < 1000 THEN '4. 500-1000'
    ELSE '5. 1000+'
  END AS price_band,
  COUNT(*) AS carted_sessions,
  SUM(1 - purchased) AS abandoned_sessions,
  ROUND(100.0 * SUM(purchased) / COUNT(*), 2) AS cart_to_purchase_pct
FROM s
WHERE carted = 1
GROUP BY 1
ORDER BY 1;
