import os
import duckdb

SRC = "data/nov.parquet"
OUT = "app/aggregates"
FOLLOW_UP = 7 * 86400  # every cart gets a full 7-day follow-up
WINDOWS = [("1h", 3600), ("6h", 21600), ("1d", 86400), ("3d", 259200), ("7d", 604800)]
BAD_START, BAD_END = "2019-11-14 00:00:00", "2019-11-18 00:00:00"  # suspect days (end exclusive)

os.makedirs(OUT, exist_ok=True)
os.makedirs("data/tmp", exist_ok=True)

con = duckdb.connect()
con.sql("SET memory_limit='4GB'")
con.sql("SET temp_directory='data/tmp'")
con.sql("SET TimeZone='UTC'")

print("1/3 Extracting cart and purchase events...")
con.sql(f"""
COPY (
  SELECT user_id, user_session, event_type, product_id, category_code, price,
         epoch(CAST(LEFT(CAST(event_time AS VARCHAR), 19) AS TIMESTAMP)) AS ts
  FROM '{SRC}'
  WHERE event_type IN ('cart', 'purchase')
) TO 'data/cart_purchase.parquet' (FORMAT PARQUET)
""")
data_end = con.sql("SELECT MAX(ts) FROM 'data/cart_purchase.parquet'").fetchall()[0][0]

print("2/3 Finding abandoned carts and what happened next...")
# One row per abandoned session, described by its most expensive cart item.
# Cohort: a full 7-day follow-up must fit in the data and must not touch the suspect days.
con.sql(f"""
CREATE TABLE ab AS
SELECT e.user_id, e.user_session,
       MAX(e.ts)                         AS last_cart_ts,
       arg_max(e.product_id, e.price)    AS lead_product,
       arg_max(e.category_code, e.price) AS lead_category,
       MAX(e.price)                      AS lead_price
FROM 'data/cart_purchase.parquet' e
JOIN 'data/sessions.parquet' s ON s.user_session = e.user_session
WHERE e.event_type = 'cart' AND e.price > 0 AND e.user_id IS NOT NULL
  AND s.viewed = 1 AND s.carted = 1 AND s.purchased = 0
GROUP BY 1, 2
HAVING arg_max(e.category_code, e.price) IS NOT NULL
   AND MAX(e.ts) <= {data_end} - {FOLLOW_UP}
   AND NOT (MAX(e.ts) > epoch(TIMESTAMP '{BAD_START}') - {FOLLOW_UP}
            AND MAX(e.ts) < epoch(TIMESTAMP '{BAD_END}'))
""")
con.sql("CREATE VIEW pur AS SELECT * FROM 'data/cart_purchase.parquet' WHERE event_type = 'purchase'")

# Earliest later purchase by the same user: same product, same category, or anything.
con.sql(f"""
CREATE TABLE res AS
SELECT a.*, r.dt_prod, r.dt_cat, r.dt_any
FROM ab a
LEFT JOIN (
  SELECT a2.user_id, a2.user_session,
         MIN(p.ts - a2.last_cart_ts) FILTER (WHERE p.product_id = a2.lead_product)       AS dt_prod,
         MIN(p.ts - a2.last_cart_ts) FILTER (WHERE p.category_code = a2.lead_category)   AS dt_cat,
         MIN(p.ts - a2.last_cart_ts)                                                      AS dt_any
  FROM ab a2
  JOIN pur p ON p.user_id = a2.user_id
            AND p.ts > a2.last_cart_ts AND p.ts <= a2.last_cart_ts + {FOLLOW_UP}
  GROUP BY 1, 2
) r ON r.user_id = a.user_id AND r.user_session = a.user_session
""")

print("3/3 Writing app/aggregates/recovery.csv ...")
cols = []
for tier in ("prod", "cat", "any"):
    for name, secs in WINDOWS:
        cond = f"dt_{tier} <= {secs}"
        cols.append(f"COUNT(*) FILTER (WHERE {cond}) AS n_{tier}_{name}")
        cols.append(f"COALESCE(ROUND(SUM(lead_price) FILTER (WHERE {cond})), 0) AS v_{tier}_{name}")
con.sql(f"""
COPY (
  SELECT lead_category AS category_code,
         CASE WHEN lead_price < 100  THEN '1. under 100'
              WHEN lead_price < 250  THEN '2. 100-250'
              WHEN lead_price < 500  THEN '3. 250-500'
              WHEN lead_price < 1000 THEN '4. 500-1000'
              ELSE '5. 1000+' END AS price_band,
         COUNT(*) AS abandoned,
         ROUND(SUM(lead_price)) AS value,
         {", ".join(cols)}
  FROM res
  GROUP BY 1, 2
  ORDER BY 1, 2
) TO '{OUT}/recovery.csv' (HEADER, DELIMITER ',')
""")

print("Done. Whole cohort:")
print(con.sql("""
  SELECT COUNT(*) AS abandoned_carts,
         ROUND(100.0 * AVG(COALESCE((dt_prod <= 604800)::INT, 0)), 1) AS same_product_7d_pct,
         ROUND(100.0 * AVG(COALESCE((dt_cat  <= 604800)::INT, 0)), 1) AS same_category_7d_pct,
         ROUND(100.0 * AVG(COALESCE((dt_any  <= 604800)::INT, 0)), 1) AS any_purchase_7d_pct
  FROM res
"""))
