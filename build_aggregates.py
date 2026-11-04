import os
import duckdb

SRC = "data/nov.parquet"
OUT = "app/aggregates"
MIN_VIEWED = 5000  # ignore tiny categories so charts stay readable

os.makedirs(OUT, exist_ok=True)
os.makedirs("data/tmp", exist_ok=True)

con = duckdb.connect()
con.sql("SET memory_limit='4GB'")
con.sql("SET temp_directory='data/tmp'")
con.sql("SET TimeZone='UTC'")


def save(name, query):
    con.sql(f"COPY ({query}) TO '{OUT}/{name}.csv' (HEADER, DELIMITER ',')")
    n = con.sql(f"SELECT COUNT(*) FROM '{OUT}/{name}.csv'").fetchall()[0][0]
    print(f"  wrote {name}.csv ({n} rows)")


print("1/3 Building session table (slowest step, a few minutes)...")
con.sql(f"""
COPY (
  SELECT user_session,
         MIN(LEFT(CAST(event_time AS VARCHAR), 10)) AS day,
         MAX((event_type = 'view')::INT)     AS viewed,
         MAX((event_type = 'cart')::INT)     AS carted,
         MAX((event_type = 'purchase')::INT) AS purchased
  FROM '{SRC}'
  GROUP BY 1
) TO 'data/sessions.parquet' (FORMAT PARQUET)
""")

print("2/3 Building session-by-category table...")
con.sql(f"""
COPY (
  SELECT user_session, category_code,
         MAX((event_type = 'view')::INT)     AS viewed,
         MAX((event_type = 'cart')::INT)     AS carted,
         MAX((event_type = 'purchase')::INT) AS purchased,
         MAX(CASE WHEN event_type = 'cart' AND price > 0 THEN price END) AS cart_price
  FROM '{SRC}'
  WHERE category_code IS NOT NULL
  GROUP BY 1, 2
) TO 'data/session_category.parquet' (FORMAT PARQUET)
""")

print("3/3 Writing dashboard files to app/aggregates ...")

save("funnel", """
  SELECT COUNT(*)                        AS total_sessions,
         SUM(viewed)                     AS viewed,
         SUM(viewed * carted)            AS carted,
         SUM(viewed * carted * purchased) AS bought_after_cart,
         SUM(purchased)                  AS any_purchase
  FROM 'data/sessions.parquet'
""")

save("daily", """
  SELECT day,
         COUNT(*)                         AS sessions,
         SUM(viewed * carted)             AS carted,
         SUM(viewed * carted * purchased) AS bought_after_cart,
         SUM(purchased)                   AS any_purchase
  FROM 'data/sessions.parquet'
  GROUP BY 1 ORDER BY 1
""")

METRICS = """
  SUM(viewed)                                        AS viewed_sessions,
  SUM(viewed * carted)                               AS carted_sessions,
  SUM(viewed * carted * purchased)                   AS bought_sessions,
  SUM(viewed * carted * (1 - purchased))             AS abandoned_sessions,
  ROUND(COALESCE(SUM(viewed * carted * (1 - purchased) * cart_price), 0)) AS revenue_at_risk
"""

save("categories", f"""
  WITH t AS (
    SELECT user_session, split_part(category_code, '.', 1) AS category,
           MAX(viewed) AS viewed, MAX(carted) AS carted,
           MAX(purchased) AS purchased, MAX(cart_price) AS cart_price
    FROM 'data/session_category.parquet'
    GROUP BY 1, 2
  )
  SELECT category, {METRICS}
  FROM t GROUP BY 1
  HAVING SUM(viewed) >= {MIN_VIEWED}
  ORDER BY 2 DESC
""")

save("subcategories", f"""
  SELECT split_part(category_code, '.', 1) AS category, category_code, {METRICS}
  FROM 'data/session_category.parquet'
  GROUP BY 1, 2
  HAVING SUM(viewed) >= {MIN_VIEWED}
  ORDER BY 3 DESC
""")

save("price_bands", """
  WITH b AS (
    SELECT category_code, purchased, cart_price,
           CASE WHEN cart_price < 100  THEN '1. under 100'
                WHEN cart_price < 250  THEN '2. 100-250'
                WHEN cart_price < 500  THEN '3. 250-500'
                WHEN cart_price < 1000 THEN '4. 500-1000'
                ELSE '5. 1000+' END AS price_band
    FROM 'data/session_category.parquet'
    WHERE carted = 1 AND cart_price IS NOT NULL
  )
  SELECT category_code, price_band,
         COUNT(*)                                  AS carted_sessions,
         SUM(1 - purchased)                        AS abandoned_sessions,
         ROUND(SUM((1 - purchased) * cart_price))  AS revenue_at_risk
  FROM b
  GROUP BY 1, 2
  ORDER BY 1, 2
""")

print("Done. Headline numbers for a sanity check:")
print(con.sql(f"SELECT * FROM '{OUT}/funnel.csv'"))
