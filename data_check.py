import duckdb

con = duckdb.connect()

# Load orders
con.execute("CREATE TABLE orders AS SELECT * FROM read_csv_auto('data/orders.csv')")

# Quick stats
n_orders = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
n_users = con.execute("SELECT COUNT(DISTINCT user_id) FROM orders").fetchone()[0]

print(f"Orders: {n_orders:,}")
print(f"Users: {n_users:,}")

# Peek at structure
print("\nFirst 5 rows:")
print(con.execute("SELECT * FROM orders LIMIT 5").fetchdf())