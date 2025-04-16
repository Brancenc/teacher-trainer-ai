import sqlite3
import json
import os

root_dir = root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
db_path = os.path.join(root_dir, 'databases', 'chat_memory', 'chat_memory.sqlite')

# db_path = "chat_memory.sqlite"
# Adjust the path to the correct location
# db_path = os.path.join(os.path.dirname(__file__), '../../databases/chat_memory/chat_memory.sqlite3')


mock_chat1 = [
    {"role": "user", "content": "Can you tell me the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris."},
    {"role": "user", "content": "That's right. Do you know any interesting facts about Paris?"},
    {"role": "assistant", "content": "Yes, Paris is known as the 'City of Light' because it was one of the first cities to have street lighting. It's also famous for landmarks like the Eiffel Tower and the Louvre Museum."},
    {"role": "user", "content": "Yes, the Eiffel Tower is iconic. Do you know how tall it is?"}, 
    {"role": "assistant", "content": "The Eiffel Tower stands about 330 meters tall, including its antennas at the top. It was the tallest man-made structure in the world until the completion of the Chrysler Building in New York in 1930."}
]

mock_chat2 = [
    {"role": "user", "content": "What is the Pythagorean theorem?"},
    {"role": "assistant", "content": "The Pythagorean theorem states that in a right triangle, the square of the length of the hypotenuse is equal to the sum of the squares of the lengths of the other two sides."},
    {"role": "user", "content": "That's correct. How do we apply it in real life?"},
    {"role": "assistant", "content": "It's used in many fields such as construction, navigation, and physics. For example, in construction, it helps to ensure that corners of buildings are square by measuring the diagonal lengths."},
    {"role": "user", "content": "What about its use in navigation?"}, 
    {"role": "assistant", "content": "In navigation, the Pythagorean theorem helps calculate the shortest distance between two points on a map, especially when traveling in a straight line rather than following the edges of roads."}
]

new_chat = [
    {"role": "user", "content": "What is the Pythagorean theorem?"},
    {"role": "assistant", "content": "The Pythagorean theorem states that in a right triangle, the square of the length of the hypotenuse is equal to the sum of the squares of the lengths of the other two sides."},
    {"role": "user", "content": "That's correct. How do we apply it in real life?"},
    {"role": "assistant", "content": "It's used in many fields such as construction, navigation, and physics. For example, in construction, it helps to ensure that corners of buildings are square by measuring the diagonal lengths."},
    {"role": "user", "content": "What about its use in navigation?"}, 
    {"role": "assistant", "content": "In navigation, the Pythagorean theorem helps calculate the shortest distance between two points on a map, especially when traveling in a straight line rather than following the edges of roads."}
]

def create_table():
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS chat_sessions')
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, 
                conversations TEXT,
                grade_level TEXT,
                subject TEXT,
                challenge TEXT,
                knowledge_messages TEXT
            )    
        ''')
        conn.commit()

def retrieve_chats(username, idd = None):
    query = '''
        SELECT id, conversations, grade_level, subject, challenge, knowledge_messages
        FROM chat_sessions
        WHERE username = ?
    '''
    params = (username,)
    if idd:
        query += ' AND id != ?'
        params = (username, idd)

    try:
        with sqlite3.connect(db_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                return None
            else:
                return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
        
def retrieve_conversations(username, id):
    query = '''
        SELECT conversations
        FROM chat_sessions
        WHERE username = ? AND id != ?
    '''
    params = (username, id)
    try:
        with sqlite3.connect(db_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                return None
            else:
                return rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
        
def store_chat(username, chat, g_level="2nd", subj="math", chal="disruptive", knowledge_messages=None):
    try:
        chat_json = json.dumps(chat)
        knowledge_messages_json = json.dumps(knowledge_messages)
        print(f"chat_json: {chat_json}")
        print(f"knowledge_messages_json: {knowledge_messages}")
        with sqlite3.connect(db_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_sessions (username, conversations, grade_level, subject, challenge, knowledge_messages)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, chat_json, g_level, subj, chal, knowledge_messages_json))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def replace_chat(id, username, new_chat, gl, subj, chal, km):
    try:
        chat_json = json.dumps(new_chat)
        knowledge_json = json.dumps(km)
        with sqlite3.connect(db_path, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                REPLACE INTO chat_sessions (id, username, conversations, grade_level, subject, challenge, knowledge_messages)   
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (id, username, chat_json, gl, subj, chal, knowledge_json))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
# Helper Function, not used in main application
def view_table():
    with sqlite3.connect(db_path, timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT *
            FROM chat_sessions
            ORDER BY username
        ''')
        rows = cursor.fetchall()
        if not rows:
            print("No rows")
        else:
            for id, username, content, gl, s, c in rows:
                print(f"ID: {id}")
                print(f"Username: {username}")
                print(f"Content: {content}\n")  # Content is a string
                # print(type(content))

def main():
    create_table()
    # username = "brancenc"


    # mock_id_1 = store_chat(username, mock_chat1)
    # mock_id_2 = store_chat(username, mock_chat2)
    # print(mock_id_1, mock_id_2)
    # new_chat.append(mock_chat1[0])
    # new_chat.append(mock_chat1[1])
    # replace_chat(rid, username, new_chat, "2nd", "math", "disruptive")
    # view_table()

    
if __name__ == "__main__":
    main()