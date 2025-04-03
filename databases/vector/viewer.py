''' NOTE
Helper File:

This class only views (does not modify) the database. 
Used primarily for testing and verifying results. 

'''



import sqlite3

db_path = "vector_db.sqlite" # Find actual directory where knowledge base exists

# Since Viewer is READ ONLY OPERATIONS, a connection can be established the entire time. 
class Viewer:
    def __init__(self, path = db_path):
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()

    def view_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for table in self.cursor.fetchall():
            print(table[0])

    def count_rows(self):
        self.cursor.execute("SELECT COUNT(*) FROM chunks")
        print("Chunks Rows:", self.cursor.fetchone()[0])
        self.cursor.execute("SELECT COUNT(*) FROM embeddings")
        print("Embeddings Rows:", self.cursor.fetchone()[0])

    def show_rows(self, limit=5):
        print("\n--- Chunks ---")
        self.cursor.execute("SELECT * FROM chunks ORDER BY id DESC LIMIT ?", (limit,))
        for row in self.cursor.fetchall():
            print(row)

        print("\n--- Embeddings ---")
        self.cursor.execute("SELECT * FROM embeddings ORDER BY chunk_id DESC LIMIT ?", (limit,))
        for row in self.cursor.fetchall():
            print(row)

    def view_performance_log(self, query=None, category=None):
        if query and category:
            self.cursor.execute(
                "SELECT * FROM query_logs WHERE query = ? AND category = ?", (query, category)
            )
        elif query:
            self.cursor.execute("SELECT * FROM query_logs WHERE query = ?", (query,))
        else:
            self.cursor.execute("SELECT * FROM query_logs")

        logs = self.cursor.fetchall()
        if not logs:
                print("No performance logs found")
                return

        print(f"{'ID':<5} {'Query':<30} {'Category':<15} {'Exec_Time(s)':<15} {'Source':<10} {'Timestamp'}")
        print("-" * 95)
        for log in logs:
            print(f"{log[0]:<5} {log[1]:<30} {str(log[2]):<15} {log[3]:<15.4f} {log[4]:<10} {log[5]}")

    def view_cache(self):
        self.cursor.execute("SELECT query, category FROM cache")
        logs = self.cursor.fetchall()
        if not logs:
            print("No rows found in cache")

        for row in logs:
            print(f"Query: {row[0]:<50} | Category: {row[1]}")


    def __del__(self):
        self.conn.close()

# def main():
#     view = Viewer()
#     view.count_rows()
#     # view.show_rows(6)

# if __name__ == "__main__":
#     main()
        