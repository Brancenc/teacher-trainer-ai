import streamlit as st
import random
import time

defaultPage = 'home'#current pages are 'home','chat',and 'eval'

def GetSecondGraderResponse( session, userResponse):
	"""session is the steamlit session, userResponse is string of user's prompt, returns a string"""
	messages = session.messages
	situation = session.situation

	#this should be replaced with actual output
	return random.choice(
				[
					"Hello there! I am second grader",
					"Hi, human! Is there anything I can help you with?",
					"Do you need help?",
				]
			)

def GetEvaluation( session):
	"""session is the streamlit session, returns a tuple (score, evalText)"""
	messages = session.messages

	#these should be replaced with actual evaluation
	score = 50
	evalTex = "This is some text that talks about your interation"
	return (score,evalTex)


if 'page' not in st.session_state:
    st.session_state['page'] = 'home'#this is the default page

def StartPage():
	st.title("AI 2nd Grader")
	st.divider()

	selectedSituation = st.selectbox("Select Situation",
	options=["Situation 1","Situation 2","Situation 3","Situation 4"],
	index=0,
	placeholder="Select situation...")

	st.session_state["situation"]=selectedSituation

	if st.button("Start"):
		#go to chat page
		st.session_state['page'] = 'chat'
		#wipe messages in current session
		st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

		st.rerun()


def ChatPage():
	navContainer = st.container(border=True)
	col1, col2, col3 = navContainer.columns(3)
	if col1.button("Go Back to Situation Select"):
		#go back to home page
		st.session_state['page'] = 'home'
		st.rerun()
	if col3.button("Go to Evaluation Page"):
		#go to eval page
		st.session_state['page'] = 'eval'
		st.rerun()


	# Initialize chat history
	if "messages" not in st.session_state:
		st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

	# Display chat messages from history on app rerun
	for message in st.session_state.messages:
		with st.chat_message(message["role"]):
			st.markdown(message["content"])

	# Accept user input
	if prompt := st.chat_input("What is up?"):
		# Add user message to chat history
		st.session_state.messages.append({"role": "user", "content": prompt})
		# Display user message in chat message container
		with st.chat_message("user"):
			st.markdown(prompt)

		# Display assistant response in chat message container
		with st.chat_message("assistant"):
			message_placeholder = st.empty()
			full_response = ""
			assistant_response = GetSecondGraderResponse(st.session_state,prompt)
			# Simulate stream of response with milliseconds delay
			for chunk in assistant_response.split():
				full_response += chunk + " "
				time.sleep(0.05)
				# Add a blinking cursor to simulate typing
				message_placeholder.markdown(full_response + "▌")
			message_placeholder.markdown(full_response)
		# Add assistant response to chat history
		st.session_state.messages.append({"role": "assistant", "content": full_response})

def EvalPage():
	st.title("Evaluation")
	
	evaluationScore,evaluationText = GetEvaluation(st.session_state)
	#display evaluation
	st.metric("Score",evaluationScore)
	st.header("AI's evaluation")
	st.text(evaluationText)

	#button to restart
	if st.button("Go Back to Situation Select"):
		#go back to home page
		st.session_state['page'] = 'home'
		st.rerun()
	



#page selector
if st.session_state['page'] == 'chat':
	ChatPage()
elif st.session_state['page'] == 'eval':
	EvalPage()
elif st.session_state['page'] == 'home':
	StartPage()
else:
	st.title("Something went wrong.")
