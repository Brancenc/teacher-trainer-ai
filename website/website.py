import streamlit as st
import time
import sys
import os
import traceback
import warnings
import logging

# More aggressive warning and error suppression
warnings.filterwarnings('ignore')
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('torch').setLevel(logging.ERROR)
logging.getLogger('faiss').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)

# Set environment variables to suppress PyTorch warnings and errors
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'
os.environ['PYTORCH_DISABLE_CUSTOM_CLASS_REGISTRATION'] = '1'
os.environ['TORCH_USE_RTLD_GLOBAL'] = 'YES'  # Help with some PyTorch dynamic loading issues
os.environ['STREAMLIT_WATCH_MODULE_SKIP'] = 'torch,transformers,langchain,sentence_transformers,faiss'

# Configure Streamlit page before any other Streamlit commands
try:
	st.set_page_config(
		page_title="Teacher Trainer Simulator",
		page_icon="icon.png",
		layout="wide"
	)
except Exception as e:
	st.error(f"Error setting page config: {str(e)}")

# Add the models directory to the Python path so we can import from it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import with error handling
try:
	from models.llm_test import (
		generate_scenario,
		get_student_response,
		get_knowledge_explorer_response,
		get_teaching_evaluation
	)
except Exception as e:
	st.error(f"Error importing LLM modules: {e}")
	# Stop the app if imports fail
	st.stop()

# Function to safely execute code with error handling
def safe_execute(func, *args, fallback_result=None, **kwargs):
	"""Execute a function safely with comprehensive error handling."""
	try:
		return func(*args, **kwargs)
	except Exception as e:
		st.error(f"Error in {func.__name__}: {str(e)}")
		return fallback_result

# Initialize default page
if 'page' not in st.session_state:
	st.session_state['page'] = 'home'

def StartPage():
	st.title("AI Classroom Simulator")
	st.divider()

	selectedGrade = st.selectbox("Grade Level",
	options=["Kindergarten","Grade 1","Grade 2","Grade 3","Grade 4","Grade 5"],
	index=2)

	selectedSubject = st.selectbox("Subject",
	options=["English","Math","Science"],
	index=0,
	placeholder="Select situation...")

	selectedChallengeType = st.selectbox("Challenge",
	options=["disruptive","fidgeting", "distracted", "frustrated", "confused", "engaged"],
	placeholder="Select challenge")

	st.session_state["subject"] = selectedSubject
	st.session_state["gradeLevel"] = selectedGrade
	st.session_state["challenge"] = selectedChallengeType

	if st.button("Start"):
		#go to chat page
		st.session_state['page'] = 'chat'
		#wipe messages in current session
		st.session_state.messages = []  # Start with empty messages
		st.rerun()

def ChatPage():
	with st.sidebar:
		if st.button("Go Back to Situation Select"):
			st.session_state['page'] = 'home'
			st.rerun()
		if st.button("Go to Evaluation Page"):
			st.session_state['page'] = 'eval'
			st.rerun()
		
		st.divider()
		st.markdown("### Knowledge Explorer")
		st.markdown("Ask questions about teaching concepts in the box below.")
		st.divider()

		messageCont = st.container(height=300)

		if "knowledgeMessages" not in st.session_state:
			st.session_state.knowledgeMessages = [{"role": "assistant", "content": "Ask about teaching knowledge"}]

		#display previous chat messages
		for message in st.session_state["knowledgeMessages"]:
			with messageCont.chat_message(message["role"]):
				st.markdown(message["content"])

		if prompt := st.chat_input("Ask for knowledge", key="knowledge_input"):
			# Add user message to chat history
			st.session_state["knowledgeMessages"].append({"role": "user", "content": prompt})
			# Display user message in chat message container
			with messageCont.chat_message("user"):
				st.markdown(prompt)

			# Display assistant response in chat message container
			with messageCont.chat_message("assistant"):
				message_placeholder = st.empty()
				full_response = ""
				
				with st.spinner("Retrieving knowledge..."):
					try:
						assistant_response = safe_execute(
							get_knowledge_explorer_response,
							prompt,
							fallback_result="I'm having trouble retrieving knowledge right now."
						)
					except Exception as e:
						assistant_response = f"Error retrieving knowledge: {str(e)}"
				
				# Simulate stream of response with milliseconds delay
				for chunk in assistant_response.split():
					full_response += chunk + " "
					time.sleep(0.01)  # Reduced delay for better performance
					# Add a blinking cursor to simulate typing
					message_placeholder.markdown(full_response + "▌")
				message_placeholder.markdown(full_response)
			# Add assistant response to chat history
			st.session_state["knowledgeMessages"].append({"role": "assistant", "content": full_response})

	# Student chat interface
	# Initialize chat history
	if "messages" not in st.session_state:
		st.session_state.messages = []

	# Generate and display the initial scenario if it's not already in the messages
	if len(st.session_state.messages) == 0:
		# Generate the scenario
		with st.spinner("Generating scenario..."):
			scenario = safe_execute(
				generate_scenario,
				st.session_state["gradeLevel"],
				st.session_state["subject"],
				st.session_state["challenge"],
				fallback_result="A student in your class is having difficulty focusing on the task."
			)
		
		# Add the scenario as the first assistant message
		st.session_state.messages.append({"role": "assistant", "content": f"**Classroom Scenario:**\n\n{scenario}\n\n*You are now interacting with a student. How would you respond as the teacher?*"})

	# Display chat messages from history on app rerun
	for message in st.session_state["messages"]:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])

	# Accept user input
	if prompt := st.chat_input("What would you like to say to the student?", key="main_input"):
		# Add user message to chat history
		st.session_state["messages"].append({"role": "user", "content": prompt})
		# Display user message in chat message container
		with st.chat_message("user"):
			st.markdown(prompt)

		# Display assistant response in chat message container
		with st.chat_message("assistant"):
			message_placeholder = st.empty()
			full_response = ""
			
			with st.spinner("Generating response..."):
				try:
					assistant_response = safe_execute(
						get_student_response,
						st.session_state["gradeLevel"],
						st.session_state["subject"],
						st.session_state["challenge"],
						prompt,
						fallback_result="I'm having trouble responding right now."
					)
				except Exception as e:
					st.error(f"Error: {str(e)}")
					assistant_response = "I'm having trouble responding right now. Please try again."
			
			# Simulate stream of response with milliseconds delay
			for chunk in assistant_response.split():
				full_response += chunk + " "
				time.sleep(0.01)  # Reduced delay for better performance
				# Add a blinking cursor to simulate typing
				message_placeholder.markdown(full_response + "▌")
			message_placeholder.markdown(full_response)
		# Add assistant response to chat history
		st.session_state["messages"].append({"role": "assistant", "content": full_response})

def EvalPage():
	st.title("Evaluation")
	
	# Format the conversation for evaluation
	conversation = ""
	if "messages" in st.session_state and len(st.session_state["messages"]) > 1:
		messages = st.session_state["messages"]
		
		# Skip the initial scenario message
		first_msg = messages[0]["content"]
		conversation += f"Scenario: {first_msg.split('*You are now')[0].strip()}\n\n"
		
		# Format the rest of the conversation
		for i in range(1, len(messages)):
			if messages[i]["role"] == "user":
				conversation += f"Teacher: {messages[i]['content']}\n"
			else:
				conversation += f"Student: {messages[i]['content']}\n"
	
	with st.spinner("Generating evaluation..."):
		try:
			evaluationScore, evaluationText = safe_execute(
				get_teaching_evaluation,
				conversation,
				st.session_state["gradeLevel"],
				st.session_state["subject"], 
				st.session_state["challenge"],
				fallback_result=(0, "Unable to generate evaluation.")
			)
		except Exception as e:
			st.error(f"Error generating evaluation: {str(e)}")
			evaluationScore = 0
			evaluationText = f"Unable to generate evaluation: {str(e)}"
	
	#display evaluation
	st.metric("Score", evaluationScore)
	st.header("AI's evaluation")
	st.write(evaluationText)

	col1, col2 = st.columns(2)
	
	with col1:
		if st.button("Go Back to Situation Select"):
			#go back to home page
			st.session_state['page'] = 'home'
			st.rerun()
	
	with col2:
		if st.button("Continue Conversation"):
			#go back to chat page
			st.session_state['page'] = 'chat'
			st.rerun()

# Wrap the main app in a try-except block to catch any errors
try:
	# page selector
	if st.session_state['page'] == 'chat':
		ChatPage()
	elif st.session_state['page'] == 'eval':
		EvalPage()
	elif st.session_state['page'] == 'home':
		StartPage()
	else:
		st.title("Something went wrong.")
except Exception as e:
	st.error(f"Application error: {str(e)}")
	st.code(traceback.format_exc())
