import sqlite3
import numpy as np
import json
import hashlib
from sentence_transformers import SentenceTransformer


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

db_path = "/home/team2/data/team2_data/knowledge_base/vector_db.sqlite"

class Connect:
    def __init__(self, path = db_path):
        self.db_path = path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.conn = None    # Values of these will change in connect function
        self.cursor = None  # Values of these will change in connect function
        self.cache = {}
        self._connect()


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

    def _setup_cache(self):
        pass 
        # TODO Create a different table in DB, create new DB, or create an import file

    def _hash_query(self, query: str, category: str = None) -> str:
        '''Generates the hash of a query'''
        query_string = f"{query}_{category if category else 'ALL'}"
        return hashlib.sha256(query_string.encode()).hexdigest()
        # Not using normal hash because it will produce different output on queries
        # when you restart the script
        # Encode used to convert string to bytes for sha256 input and hexdigest turns 
        # bytes into hex string

    # def _get_cached_result(self, query: str, category: str = None) -> str:
    #     pass

    # def _store_cached_result(self, query: str, category: str, results: str) -> None:
    #     pass


    def search(self, query, top_n = 3, category = None) -> list[dict]:
        '''Searches the vector database with a certain query'''
        if not self.verify_connection():
            print("No database connection")
            return []
        
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
        
        return formatted_results
        

def main():
    connection = Connect()
    results = connection.search("Behavior of second grader")
    for v in results:
        print(v["text"])
        print('\n')
main()

    

