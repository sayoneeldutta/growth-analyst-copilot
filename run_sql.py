import sys, duckdb

con = duckdb.connect()
con.sql("SET memory_limit='4GB'")
print(con.sql(open(sys.argv[1]).read()).df().to_string())
