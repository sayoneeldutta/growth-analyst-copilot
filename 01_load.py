import duckdb

con = duckdb.connect()
con.sql("SET memory_limit='4GB'")  # use '2GB' if you hit memory errors

con.sql("""
    COPY (SELECT * FROM read_csv_auto('data/2019-Nov.csv'))
    TO 'data/nov.parquet' (FORMAT PARQUET)
""")

print(con.sql("""
    SELECT event_type, COUNT(*) AS n
    FROM 'data/nov.parquet'
    GROUP BY 1 ORDER BY n DESC
"""))
