import sqlite3
import faiss
import numpy as np
import os
import warnings
import json

# Suppress warnings
warnings.filterwarnings('ignore')

# Set environment variables to suppress PyTorch warnings
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'
os.environ['PYTORCH_DISABLE_CUSTOM_CLASS_REGISTRATION'] = '1'

# Import sentence transformers with error handling
try:
    from sentence_transformers import SentenceTransformer
    # Load the sentence transformer model for vectorization
    model = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    print("Error importing sentence_transformers. Please install with: pip install sentence-transformers")
    model = None

# Database Path
DB_PATH = './databases/vector/vector_db.sqlite'

# Initialize a simple text generation function instead of using LangChain
def simple_generate(prompt):
    """A simple function to generate text without using LangChain."""
    try:
        # Import here to avoid PyTorch issues during module loading
        from langchain_ollama import OllamaLLM
        try:
            llm = OllamaLLM(model="llama3")
            return str(llm.invoke(prompt))
        except ConnectionRefusedError:
            print("Connection to Ollama refused. Is the Ollama server running?")
            return "Unable to connect to LLM server. Please check if Ollama is running."
    except Exception as e:
        print(f"Error generating text: {e}")
        return f"Error generating response: {str(e)}"

def connect_db():
    """Connect to the SQLite database."""
    try:
        if not os.path.exists(DB_PATH):
            print(f"Database file not found at: {DB_PATH}")
            return None
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def retrieve_knowledge(query, top_k=3):
    """Retrieve relevant knowledge from the database using vector similarity search."""
    try:
        if model is None:
            return ["Error: Sentence transformer model not loaded."]
            
        conn = connect_db()
        if conn is None:
            return ["Database connection failed."]
            
        cursor = conn.cursor()

        # Load text and embeddings
        cursor.execute("SELECT c.id, c.text, e.vector FROM chunks c JOIN embeddings e ON c.id = e.chunk_id where id<17981")
        data = cursor.fetchall()
        
        if not data:
            print("No data found in the database.")
            conn.close()
            return []

        ids = [row[0] for row in data]
        texts = [row[1] for row in data]
        embeddings = np.array([np.frombuffer(row[2], dtype=np.float32) for row in data])

        # Build FAISS index
        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)

        # Encode query
        query_vector = model.encode([query]).astype(np.float32)

        # Search FAISS index
        distances, indices = index.search(query_vector, top_k)

        # Retrieve corresponding knowledge texts
        knowledge = [texts[idx] for idx in indices[0] if idx < len(texts)]
        
        conn.close()
        return knowledge
    except Exception as e:
        print(f"Error retrieving knowledge: {e}")
        return [f"Error retrieving knowledge: {str(e)}"]

def generate_scenario(grade_level, subject, challenge_type, previous_scenario=None, keep_student=False, teacher_name=None):
    """Generate a classroom management scenario based on grade, subject, and challenge."""
    try:
        # Add teacher prefix based on name
        if teacher_name:
            name_parts = teacher_name.split()
            # Use last name if multiple names are provided, otherwise use the only name
            used_name = name_parts[-1] if len(name_parts) > 1 else name_parts[0]
            teacher_prefix = "Mr." if "Mr." in teacher_name or "Mr" in teacher_name else "Ms."
            teacher_full = f"{teacher_prefix} {used_name}"
        else:
            teacher_full = "the teacher"

        # If we want to keep the same student and have a previous scenario
        if keep_student and previous_scenario:
            # Create a prompt that keeps the same student but changes the situation
            prompt = f"""
            Using the following previous scenario as context:
            {previous_scenario}
            
            Generate a NEW classroom scenario for the SAME student in {teacher_full}'s {grade_level} {subject} class where they now have a {challenge_type} challenge.
            Keep the student's name and personality traits consistent, but create an entirely new situation.
            Describe the situation from a third-person perspective.
            DO NOT include any teacher responses or evaluations.
            Just describe the classroom situation that {teacher_full} needs to respond to.
            Keep it brief (2-3 sentences).
            Use {teacher_full} when referring to the teacher.
            """
        else:
            # Create a prompt for a completely new scenario
            prompt = f"""
            Generate a classroom scenario for {teacher_full}'s {grade_level} {subject} class where a student has a {challenge_type} challenge.
            Describe the situation from a third-person perspective.
            DO NOT include any teacher responses or evaluations.
            Just describe the classroom situation that {teacher_full} needs to respond to.
            Keep it brief (2-3 sentences).
            Use {teacher_full} when referring to the teacher.
            """

        # Generate the scenario
        return simple_generate(prompt)
    except Exception as e:
        print(f"Error generating scenario: {e}")
        return "Unable to generate scenario. Please try again."

def evaluate_response(user_response, knowledge):
    """Evaluate the teacher's response based on retrieved knowledge."""
    try:
        # Format knowledge as a string
        knowledge_str = "\n".join(knowledge) if isinstance(knowledge, list) else str(knowledge)
        
        eval_prompt = f"""
        Evaluate the following teacher response based on best practices:

        Teacher's Response: {user_response}

        Relevant Research:
        {knowledge_str}

        Provide a score (1-10) with an explanation of how well the response aligns with best practices.
        """
        
        # Generate the evaluation
        return simple_generate(eval_prompt)
    except Exception as e:
        print(f"Error evaluating response: {e}")
        return "Unable to evaluate response. Please try again."

def get_student_response(grade_level, subject, challenge_type, teacher_message, conversation_history=None, other_conversations=None):
    """
    Generate a student's response to a teacher's message with conversation history.
    
    Args:
        grade_level: The grade level of the student
        subject: The subject being taught
        challenge_type: The type of challenge the student is facing
        teacher_message: The most recent message from the teacher
        conversation_history: A list of previous exchanges in the format 
                             [{"role": "student/teacher", "content": "message"}]
    
    Returns:
        A response from the student character
    """
    try:
        # Format conversation history if provided
        history_text = ""
        scenario = ""
        other_history = ""
        
        if conversation_history and len(conversation_history) > 0:
            # Extract the scenario from the first message if it exists
            first_msg = conversation_history[0]
            if first_msg.get("role") == "assistant" and "Classroom Scenario" in first_msg.get("content", ""):
                scenario_text = first_msg.get("content", "")
                # Extract just the scenario part
                if "*You are now" in scenario_text:
                    scenario = scenario_text.split("*You are now")[0].strip()
                else:
                    scenario = scenario_text
            
            # Format the rest of the conversation history
            for msg in conversation_history[1:]:  # Skip the scenario message
                if msg.get("role") == "user":
                    history_text += f"Teacher: {msg.get('content', '')}\n"
                elif msg.get("role") == "assistant":
                    history_text += f"Student: {msg.get('content', '')}\n"

        # Include other conversations for memory across sessions
        if other_conversations:
            i = 1
            for tup in other_conversations:
                loaded_data = json.loads(tup[0])
                other_history += f"Conversation {i}\n"
                if loaded_data and len(loaded_data) > 0:
                    # Get the first message
                    first_msg = loaded_data[0]
                    if first_msg.get("role") == "assistant" and "Classroom Scenario" in first_msg.get("content", ""):
                        text = first_msg.get("content", "")
                        if "*You are now" in text:
                            other_history += text.split("*You are now")[0].strip()
                        else:
                            other_history += text

                    # Format the rest of the conversation history
                    for msg in loaded_data[1:]:  # Skip the scenario message
                        if msg.get("role") == "user":
                            other_history += f"Teacher: {msg.get('content', '')}\n"
                        elif msg.get("role") == "assistant":
                            other_history += f"Student: {msg.get('content', '')}\n"

                other_history += "\n"
                i += 1

        # Create a prompt for student response with history
        context = f"""
        You are a {grade_level} student in a {subject} class with a {challenge_type} challenge.
        
        {scenario if scenario else ""}
        
        {"Previous conversation:" if history_text else ""}
        {history_text}
        
        The teacher just said: "{teacher_message}"
        
        Respond AS THE STUDENT would in this scenario, keeping in mind your age and the challenge.
        Make your responses appropriate for a {grade_level} student's vocabulary and emotional maturity.
        Show consistency with your previous responses if any.
        DO NOT evaluate the teacher's response. DO NOT give feedback on teaching methods.
        Just respond naturally as a {grade_level} student would.
        """
        # TODO Cross Chat Memory Here
        # {"Here are some other conversations that occured with different students. RESPOND AS THE STUDENT to the Previous Conversation, but use the conversations below if they are referenced." 
        #  if other_history else ""}
        # {other_history}
        # """"""

        # Generate the student response
        return simple_generate(context)
    except Exception as e:
        print(f"Error generating student response: {e}")
        return "Unable to generate student response. Please try again."

def get_knowledge_explorer_response(query,convo):
    """Generate a response about teaching concepts based on the knowledge base."""
    try:
        print(f"{convo}************************************************************************************************")
        # Retrieve relevant knowledge from the database
        unpacked_convo = "\n".join([f"role: {item['role']}, content: {item['content']}" for item in convo])
        knowledge = retrieve_knowledge(unpacked_convo, top_k=5)
        print(f"Knowledge: {knowledge}++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        if not knowledge:
            return "I don't have specific information about that in my knowledge base. Could you try asking something related to classroom management or teaching approaches?"
        
        # Format the knowledge into a response
        prompt = f"""
        The user has asked: "{query}"
        
        Based on the following knowledge, provide a helpful response:
        Situation: {convo}
        Knowledge Base:
        {knowledge}
        
        Format your response in a clear, concise way that directly addresses the user's query.
        """
        
        response = simple_generate(prompt)
        return response
    except Exception as e:
        print(f"Error retrieving knowledge response: {e}")
        return "I'm having trouble accessing the knowledge base right now. Please try again."

def get_teaching_evaluation(conversation_text=None, grade_level=None, subject=None, challenge_type=None, conversation_messages=None):
    """
    Evaluate a teacher-student conversation.
    
    Args:
        conversation_text: Pre-formatted conversation text (legacy support)
        grade_level: The grade level of the classroom
        subject: The subject being taught
        challenge_type: The challenge type being addressed
        conversation_messages: List of conversation messages in the format
                              [{"role": "user/assistant", "content": "message"}]
    
    Returns:
        Tuple of (score, evaluation_text)
    """
    try:
        # Extract scenario and format conversation if messages are provided
        if conversation_messages and len(conversation_messages) > 0:
            scenario = ""
            conversation_text = ""
            
            # Extract scenario from first message if it exists
            first_msg = conversation_messages[0]
            if first_msg.get("role") == "assistant" and "Classroom Scenario" in first_msg.get("content", ""):
                scenario_text = first_msg.get("content", "")
                # Extract just the scenario part
                if "*You are now" in scenario_text:
                    scenario = scenario_text.split("*You are now")[0].strip()
                else:
                    scenario = scenario_text
                
                conversation_text = f"Scenario: {scenario}\n\n"
            
            # Format the rest of the conversation
            for i in range(1, len(conversation_messages)):
                msg = conversation_messages[i]
                if msg.get("role") == "user":
                    conversation_text += f"Teacher: {msg.get('content', '')}\n"
                elif msg.get("role") == "assistant":
                    conversation_text += f"Student: {msg.get('content', '')}\n"
        
        # Fall back to provided conversation text if no messages or formatting failed
        if not conversation_text:
            conversation_text = "No conversation to evaluate."
        
        # Get the challenge type for knowledge retrieval
        knowledge = retrieve_knowledge(challenge_type, top_k=5)
        
        # Create evaluation prompt
        prompt = f"""
        Evaluate the following teacher-student interaction based on best practices for handling a {challenge_type} situation:
        
        Grade Level: {grade_level}
        Subject: {subject}
        Challenge: {challenge_type}
        
        {conversation_text}
        
        Relevant Research:
        {knowledge}
        
        First, provide an overall rating (poor, fair, good, great, amazing) that accurately replects the teacher's performance.
        Then, provide a detailed analysis of how well the theacher handled the situateion, including the following categories:
        - Comprehension: How well did the teacher understand and address the student's needs?
        - Engagement: How effectively did the teacher engage with the student?
        - Accuracy: How accurate was the teacher's approach to the situation?
        - Believability of Role: How well did the teacher maintain their professional role?
        - Opportunities for growth: What opportunities for improvement were present?

        Make sure your overall rating is consistent with your detailed analysis.
        Pormat your response as: OVERALL: [rating]\n\nANALYSIS: [detailed evaluation]
        """
        
        evaluation = simple_generate(prompt)
        
        # Extract score and text
        try:
            if "OVERALL:" in evaluation:
                parts = evaluation.split("ANALYSIS:", 1)
                score_part = parts[0].strip()
                #Extract the rating
                score = score_part.replace("OVERALL:","").strip()
                eval_text = parts[1].strip() if len(parts) > 1 else evaluation
            else:
                # If format isn't followed, make an estimate
                score = "Fair"
                eval_text = evaluation
        except:
            score = "Fair"
            eval_text = evaluation
        
        return (score, eval_text)
    except Exception as e:
        print(f"Error generating evaluation: {e}")
        return ("Fair", f"Unable to generate evaluation: {str(e)}")

def handle_conversation():
    context = ""
    print("Welcome to the classroom management chatbot! Type 'exit' to quit.")

    while True:
        grade_level = input("Enter grade level: ")
        subject = input("Enter subject: ")
        challenge_type = input("Enter challenge type: ")

        # Generate the scenario based on grade level, subject, and challenge type
        scenario = generate_scenario(grade_level, subject, challenge_type)
        print("\nGenerated Classroom Scenario:")
        print(scenario)

        # Now the teacher must respond to the scenario
        user_response = input("\nHow would you respond? ").strip()

        # Retrieve relevant knowledge for evaluation (assuming it's related to the challenge)
        knowledge = retrieve_knowledge(challenge_type)
        if not knowledge:
            print("No relevant knowledge found. Try a different query.")
            continue

        # Evaluate the teacher's response based on the knowledge retrieved
        evaluation = evaluate_response(user_response, knowledge)
        print("\nEvaluation of Your Response:")
        print(evaluation)

if __name__ == "__main__":
    handle_conversation()
