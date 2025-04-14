''' NOTE
Helper File:

This class only deletes from certain tables in the database. 
It clears the cache and the performance log query tables if needed.
Used primarily for testing and verifying results. 


NOTE NONE OF THESE FUNCTIONS REMOVE DATA FROM DATABASE, SIMPLY CHANGE THE CACHE AND PERFORMANCE QUERY LOG

'''
import sqlite3
import getpass

db_path = "vector_db.sqlite"

class Remove:
    def __init__(self, path = db_path):
        self.db_path = path

    def _create_connection(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def clear_cache(self):
        password = getpass.getpass("Enter password to clear cache: ")
        if password == "team2pass":
            with self._create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cache")
                conn.commit()
            print("Cache cleared.")
        else:
            print("Incorrect password.")

    def clear_query_log(self):
        password = getpass.getpass("Enter password to clear query logs: ")
        if password == "team2pass":
            with self._create_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM query_logs")
                conn.commit()
            print("Query logs cleared.")
        else:
            print("Incorrect password.")