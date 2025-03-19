import sqlite3
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import os
import time


''' 
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    text TEXT,                     -- The actual text content
    metadata TEXT,                 -- JSON string with source information
    category TEXT,                 -- Classification category
    usage_count INTEGER DEFAULT 0, -- How often used in scenarios
    effectiveness_score REAL DEFAULT 0 -- Performance metric (0.0-1.0)
);

CREATE TABLE embeddings (
    chunk_id INTEGER PRIMARY KEY,
    vector BLOB,                   -- Binary vector representation (384 dimensions)
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);
'''

db_path = "vector_dv.sqlite"
# CACHE_FILE = "/home/team2/databases/vector/cache.json" # REPLACE WITH CACHE FILE


class Connect:
    def __init__(self, path = db_path):
        self.db_path = path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.conn = None    # Values of these will change in connect function
        self.cursor = None  # Values of these will change in connect function
        self.cache = {}
        self._connect()
        
        # Json Way
        # self._load_cache()

        # Cache table way
        # self._create_caching_tables()


    def _connect(self) -> None:
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            self.conn = None
            self.cursor = None
            print(f"Error connecting to the database: {e}")

        except Exception as generic_e: #catch any other errors.
            self.conn = None
            self.cursor = None
            print(f"An unexpected error occured: {generic_e}")


    def _verify_connection(self):  # Function for defnesive programming
        return self.conn is not None and self.cursor is not None


    def close_connection(self) -> None:
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    # First way using json file
    # def _load_cache(self):
    #     if os.path.exists(CACHE_FILE):
    #         try:
    #             with open(CACHE_FILE, "r") as f:
    #                 self.cache = json.load(f)
    #         except (json.JSONDecodeError, OSError):
    #             print("Cache file is empty or corrupt")
    #             self.cache = {}
    #     else:
    #         self.cache = {}

    # def _save_cache(self):
    #     with open(CACHE_FILE, "w") as f:
    #         json.dump(self.cache, f, indent = 4)


    # Second way using cache table
    def _create_caching_tables(self):
        """Creates a persistent cache table if it doesn't exist and created corresponding performance tracking table"""
        if self._verify_connection():
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    query TEXT PRIMARY KEY,
                    category TEXT,
                    results TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT,
                    category TEXT,
                    execution_time REAL,
                    source TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def _log_query_performance(self, query, category, execution_time, source):
        self.cursor.execute(
            "INSERT INTO query_log (query, category, execution_time, source) VALUES (?, ?, ?, ?)",
            (query, category, execution_time, source)
        )
        self.conn.commit()

    def _get_cached_result(self, query, category):
        """Checks if a query result exists in cache."""
        self.cursor.execute("SELECT results FROM cache WHERE query = ? AND category = ?", (query, category))
        cached_result = self.cursor.fetchone()
        return json.loads(cached_result[0]) if cached_result else None
    
    def _cache_result(self, query, category, results):
        """Stores search results in cache."""
        results_json = json.dumps(results)
        self.cursor.execute("REPLACE INTO cache (query, category, results) VALUES (?, ?, ?)", (query, category, results_json))
        self.conn.commit()

    def search(self, query, top_n = 3, category = None) -> list[dict]:
        '''Searches the vector database with a certain query'''
        if not self._verify_connection():
            print("No database connection")
            return []
        
        start_time = time.time()
        
        # Json Way
        # cache_key = f"{query}::{category}"
        # if cache_key in self.cache:
        #     print("Returning cached results")
        #     return self.cache[cache_key]

        # Cache Table way
        cached_results = self._get_cached_result(query, category)
        if cached_results:
            execution_time = time.time() - start_time
            self._log_query_performance(query, category, execution_time, "cache")
            print("Returning cached results.")
            return cached_results
        

        
        # Convert query to embedding
        query_embedding = self.model.encode([query])[0] # [0] is used since we only passed one query, the output will only be one vector
        

        # Build the SQL Query
        sql_query = "SELECT c.id, c.text, c.metadata, c.category, c.usage_count, c.effectiveness_score, e.vector \
                    FROM chunks C \
                    JOIN embeddings e on c.id = e.chunk_id"
        if category:    
            sql_query += f" WHERE c.category = ?"   # ? is a parameterized query {category} could lead to SQL injections


        # Execute the Query
        params = (category,) if category else ()
        self.cursor.execute(sql_query, params)
        results = self.cursor.fetchall()

        # Compute Similarities
        similarities = []
        for id, text, metadata, category, usage, effectiveness, vector in results:
            vector = np.frombuffer(vector, dtype=np.float32)
            similarity = np.dot(query_embedding, vector)

            similarities.append((id, text, metadata, category, similarity))
        
        similarities.sort(key= lambda x: x[4], reverse = True)
        top_results = similarities[:top_n]


        # Format Results
        formatted_results = []
        for id, text, metadata, category, similarity in top_results:
            formatted_results.append({
                "id": id,
                "text": text,
                "metadata": json.loads(metadata),
                "category": category,
                "similarity": float(similarity)
            })
        
        # JSON way
        # self.cache[cache_key] = formatted_results
        # self._save_cache()

        # Cache table way
        self._cache_result(query, category, formatted_results)
        execution_time = time.time() - start_time
        self._log_query_performance(query, category, execution_time, "database")
        print("Not in cache")
        return formatted_results
        

def main():
    connection = Connect()
    results = connection.search("Behavior of second grader")
    # print(results)
    results2 = connection.search("Behavior of second grader")
    # print(results2)
main()

    

