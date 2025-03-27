import streamlit as st
import streamlit_authenticator as stauth
import time
import sys
import os
import traceback
import warnings
import logging
import yaml
from yaml.loader import SafeLoader

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
					# Pass the entire conversation history to get_student_response
					assistant_response = safe_execute(
						get_student_response,
						st.session_state["gradeLevel"],
						st.session_state["subject"],
						st.session_state["challenge"],
						prompt,
						st.session_state["messages"],  # Pass the full conversation history
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
	
	# Check if we have any conversation to evaluate
	if "messages" not in st.session_state or len(st.session_state["messages"]) < 2:
		st.warning("You need to have a conversation first before getting an evaluation.")
		if st.button("Go Back to Conversation"):
			st.session_state['page'] = 'chat'
			st.rerun()
		return
	
	with st.spinner("Generating evaluation..."):
		try:
			# Pass the conversation messages directly to the evaluation function
			evaluationScore, evaluationText = safe_execute(
				get_teaching_evaluation,
				None,  # No pre-formatted conversation text
				st.session_state["gradeLevel"],
				st.session_state["subject"], 
				st.session_state["challenge"],
				st.session_state["messages"],  # Pass the raw messages
				fallback_result=(0, "Unable to generate evaluation.")
			)
		except Exception as e:
			st.error(f"Error generating evaluation: {str(e)}")
			evaluationScore = 0
			evaluationText = f"Unable to generate evaluation: {str(e)}"
	
	# Display evaluation
	st.metric("Score", evaluationScore)
	st.header("AI's evaluation")
	st.write(evaluationText)
	
	# Show a snippet of the conversation that was evaluated
	with st.expander("Conversation Evaluated"):
		for i, message in enumerate(st.session_state["messages"]):
			if i == 0:
				# Show the scenario differently
				st.markdown("**Scenario:**")
				scenario_text = message["content"].split("*You are now")[0] if "*You are now" in message["content"] else message["content"]
				st.markdown(scenario_text)
				st.markdown("---")
			else:
				# Show the actual conversation
				role = "👨‍🏫 Teacher" if message["role"] == "user" else "👨‍🎓 Student"
				st.markdown(f"**{role}**: {message['content']}")

	col1, col2 = st.columns(2)
	
	with col1:
		if st.button("Go Back to Situation Select"):
			# Go back to home page
			st.session_state['page'] = 'home'
			st.rerun()
	
	with col2:
		if st.button("Continue Conversation"):
			# Go back to chat page
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
