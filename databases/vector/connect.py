import sqlite3
import numpy as np
import json
import time
from sentence_transformers import SentenceTransformer
import faiss

# NOTE Rows 0-17980 are the professor's database
# NOTE The clear_cache and clear_query_log functions require a password. Right now it is just team2pass


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


CREATE TABLE IF NOT EXISTS cache (
    query TEXT PRIMARY KEY,
    category TEXT,
    results TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT,
    category TEXT,
    execution_time REAL,
    source TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

'''

db_path = "vector_db.sqlite"    # Will most likely need to change this to path using os
model = SentenceTransformer('all-MiniLM-L6-v2')

class Connect:
    def __init__(self, path = db_path, mod = model):
        self.db_path = path
        self.model = mod

        self.model.encode(["warmup"])       # Running the model with a warmup loads all the libraries, improving efficiency on first use

        try:
            with self._create_connection() as conn:
                self._create_caching_tables(conn)
                self._create_indexes(conn)
        except Exception as e:
            print(f"Error during setup: {e}")
        
    def _create_connection(self):
        return sqlite3.connect(self.db_path, timeout=10)
    
    def _create_indexes(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON chunks(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_id ON chunks(id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_query_category ON cache(query, category);")
            conn.commit()
        except Exception as e:
            print(f"Error creating indexes: {e}")

    def _create_caching_tables(self, conn):
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                query TEXT PRIMARY KEY,
                category TEXT,
                results TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                category TEXT,
                execution_time REAL,
                source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def _get_cached_result(self, conn, query, category=None):
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT results FROM cache WHERE query = ? AND category = ?", (query, category))
        else:
            cursor.execute("SELECT results FROM cache WHERE query = ?", (query,))
        cached_result = cursor.fetchone()
        return json.loads(cached_result[0]) if cached_result else None
        
    def _cache_result(self, conn, query, category, results):
        cursor = conn.cursor()
        r = json.dumps(results)
        cursor.execute("REPLACE INTO cache (query, category, results) VALUES (?, ?, ?)", (query, category, r))
        conn.commit()

    def _log_query_performance(self, conn, query, category, execution_time, source):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO query_logs (query, category, execution_time, source) VALUES (?, ?, ?, ?)",
            (query, category, execution_time, source)
        )
        conn.commit()

    def search(self, query, top_n=3, cate=None):
        start_time = time.time()

        # Establish connection 
        with self._create_connection() as conn:
            cursor = conn.cursor()
            # Check cache 
            cached_results = self._get_cached_result(conn, query, cate)
            if cached_results:
                execution_time = time.time() - start_time
                c = "All" if cate == None else cate
                self._log_query_performance(conn, query, c, execution_time, "cache")
                print(f"Returning Cached Results in {execution_time} seconds")
                return cached_results
            
            # Build the SQL Query
            sql_query = "SELECT c.id, c.text, e.vector FROM chunks c JOIN embeddings e ON c.id = e.chunk_id"
            if cate:    
                sql_query += f" WHERE c.category = ?"   # ? is a parameterized query {category} could lead to SQL injections


            # Execute the Query
            params = (cate,) if cate else ()
            cursor.execute(sql_query, params)
            results = cursor.fetchall()

            if not results:
                print("No data found in database.")
                return []
            
            # Get results from results
            ids = [row[0] for row in results]
            texts = [row[1] for row in results]
            embeddings = np.array([np.frombuffer(row[2], dtype=np.float32) for row in results])

            # Build FAISS index
            index = faiss.IndexFlatL2(embeddings.shape[1])
            index.add(embeddings)

            # Encode query
            query_embedding = self.model.encode([query]).astype(np.float32)


            # Search index
            distances, indices = index.search(query_embedding, top_n)

            # Retrievew corresponding knowledge texts
            knowledge = [texts[idx] for idx in indices[0] if idx < len(texts)]


            # Add to cache
            self._cache_result(conn, query, cate, knowledge)
            execution_time = time.time() - start_time
            self._log_query_performance(conn, query, cate, execution_time, "database")
            print(f"Computed in database in {execution_time} seconds")
            return knowledge


def main():
    pass
    # conn = sqlite3.connect(db_path, timeout = 10)
    # cursor = conn.cursor()

    # cursor.execute("pragma journal_mode")
    # result = cursor.fetchone()
    # print(f"Journal mode: {result[0]}")
    # conn = Connect()

if __name__ == "__main__":
    main()