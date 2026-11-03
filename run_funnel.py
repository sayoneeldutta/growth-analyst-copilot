import duckdb

con = duckdb.connect()
con.sql("SET memory_limit='4GB'")
print(con.sql(open("sql/01_funnel.sql").read()))
