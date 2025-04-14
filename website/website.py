import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import *
import time
import sys
import os
import traceback
import warnings
import logging
import yaml
import random
from yaml.loader import SafeLoader

from VTuberComponent.vtuber.__init__ import vtuber

# Configure Streamlit page before any other Streamlit commands
try:
    st.set_page_config(
        page_title="Teacher Trainer Simulator",
        page_icon="icon.png",
        layout="wide"
    )
except Exception as e:
    st.error(f"Error setting page config: {str(e)}")

# More aggressive warning and error suppression
warnings.filterwarnings('ignore')
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('torch').setLevel(logging.ERROR)
logging.getLogger('faiss').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)

# Enable our debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables to suppress PyTorch warnings and errors
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'
os.environ['PYTORCH_DISABLE_CUSTOM_CLASS_REGISTRATION'] = '1'
os.environ['TORCH_USE_RTLD_GLOBAL'] = 'YES'  # Help with some PyTorch dynamic loading issues
os.environ['STREAMLIT_WATCH_MODULE_SKIP'] = 'torch,transformers,langchain,sentence_transformers,faiss'

# Try to load authentication configuration
try:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Config', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error(f"Authentication configuration file 'config.yaml' not found at {config_path}. Please create it.")
    st.stop()

# Create authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Fix path to ensure models can be imported
# Get the absolute path of the root directory (parent of website directory)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    print(f"Added {root_dir} to Python path")

# Import with error handling
try:
    from models.llm_handler import (
        generate_scenario,
        get_student_response,
        get_knowledge_explorer_response,
        get_teaching_evaluation
    )
except Exception as e:
    st.error(f"Error importing LLM modules: {e}")
    st.code(f"Python path: {sys.path}")
    st.code(f"Current directory: {os.getcwd()}")
    st.code(f"Looking for models in: {os.path.join(root_dir, 'models')}")
    # Stop the app if imports fail
    st.stop()

# Function to safely execute code with error handling
def safe_execute(func, *args, fallback_result=None, **kwargs):
    """Execute a function safely with comprehensive error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(f"Error in {func.__name__}: {str(e)}")
        st.error(traceback.format_exc())
        return fallback_result

# Initialize default page
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

# Login Page
def LoginPage():
    st.title("Teacher Trainer Simulator Login")
    
    # Login form
    try:
        authenticator.login()
    except Exception as e:
        st.error(f"Login error: {e}")

    if st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    
    # Additional authentication options
    col1, col2 = st.columns(2)
    
    with col1:
        # Password reset
        try:
            if st.button("Reset Password"):
                username = st.text_input("Enter username to reset password")
                if authenticator.reset_password(username):
                    st.success('Password reset successfully')
        except Exception as e:
            st.error(f"Password reset error: {e}")
    
    with col2:
        # Forgot password
        try:
            if st.button("Forgot Password"):
                username = st.text_input("Enter username")
                email = st.text_input("Enter email")
                if authenticator.forgot_password(username):
                    st.success('Password reset instructions sent')
        except Exception as e:
            st.error(f"Forgot password error: {e}")
    
    # Registration
    #when RegisteringNewAccount is true the registration form will be visible
    if "RegisteringNewAccount" not in st.session_state:
        st.session_state["RegisteringNewAccount"] = False

    #when the user clicks the register new account button toggle the visiblity of the form
    if st.button("Register New Account"):
        st.session_state["RegisteringNewAccount"] = not st.session_state["RegisteringNewAccount"]

    if st.session_state["RegisteringNewAccount"]:
        logger.info("Starting registration process...")
        
        # Create form
        with st.form("registration_form"):
            st.write("Please fill in your details")
            new_username = st.text_input("Username", key="reg_username")
            new_name = st.text_input("Name", key="reg_name")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_password")
            new_password_repeat = st.text_input("Repeat Password", type="password", key="reg_password_repeat")
            submit_button = st.form_submit_button("Register")

        if submit_button:
            st.session_state["RegisteringNewAccount"] = False#Hide form

            logger.info("Form submitted")
            logger.info(f"Form data - Username: {new_username}, Name: {new_name}, Email: {new_email}")
            
            if not new_username or not new_name or not new_email or not new_password:
                st.error("Please fill in all fields!")
                logger.error("Missing required fields in registration form")
                return
            
            if new_password != new_password_repeat:
                st.error("Passwords do not match!")
                logger.error("Passwords do not match in registration form")
                return
            
            # Add the new user to the config
            if 'credentials' not in config:
                config['credentials'] = {}
            if 'usernames' not in config['credentials']:
                config['credentials']['usernames'] = {}
            
            # Check if username already exists
            if new_username in config['credentials']['usernames']:
                st.error("Username already exists!")
                logger.error(f"Username {new_username} already exists")
                return
            
            # Hash the password
            logger.info("Hashing password...")
            hashed_password = stauth.Hasher().hash(new_password)
 
            # Add the new user
            config['credentials']['usernames'][new_username] = {
                'name': new_name,
                'email': new_email,
                'password': hashed_password,
                'logged_in': False
            }
            
            logger.info("Updated config with new user")
            logger.info(f"Config path: {config_path}")
            
            # Save the updated config
            try:
                logger.info("Attempting to save config file...")
                with open(config_path, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                logger.info("Config saved successfully")
                st.success("Registration successful! Please try logging in.")
            except Exception as e:
                logger.error(f"Error saving config: {str(e)}")
                st.error(f"Error saving registration: {str(e)}")

def StartPage():
    # Add logout to sidebar
    with st.sidebar:
        authenticator.logout()
        st.write(f'Welcome, *{st.session_state["name"]}*')

    st.title("AI Classroom Simulator")
    st.divider()

    # If keeping same student, use stored grade and challenge
    if st.session_state.get('keep_student', False):
        selectedGrade = st.session_state.get("previous_grade")
        st.write(f"Grade Level: {selectedGrade}")  # Display as text since we're keeping the same student
    else:
        selectedGrade = st.selectbox("Grade Level",
        options=["Kindergarten","Grade 1","Grade 2","Grade 3","Grade 4","Grade 5"],
        index=2)

    selectedSubject = st.selectbox("Subject",
    options=["English","Math","Science"],
    index=0,
    placeholder="Select situation...")

    # If keeping same student, use stored challenge
    if st.session_state.get('keep_student', False):
        selectedChallengeType = st.session_state.get("previous_challenge")
        st.write(f"Challenge: {selectedChallengeType}")  # Display as text since we're keeping the same student
    else:
        selectedChallengeType = st.selectbox("Challenge",
        options=["disruptive","fidgeting", "distracted", "frustrated", "confused", "engaged"],
        placeholder="Select challenge")

    st.session_state["subject"] = selectedSubject
    st.session_state["gradeLevel"] = selectedGrade
    st.session_state["challenge"] = selectedChallengeType

    if st.button("Start"):
        #go to chat page
        st.session_state['page'] = 'chat'
        #wipe messages in current session if not keeping the same student
        if not st.session_state.get('keep_student', False):
            st.session_state.messages = []
        st.session_state["vTuberAnimation"] = "Idling"
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
        vtuber(anim=st.session_state["vTuberAnimation"],key="vTuber")
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
            # Check if we should keep the same student
            previous_scenario = st.session_state.get('previous_scenario', None) if st.session_state.get('keep_student', False) else None
            keep_student = st.session_state.get('keep_student', False)
            
            scenario = safe_execute(
                generate_scenario,
                st.session_state["gradeLevel"],
                st.session_state["subject"],
                st.session_state["challenge"],
                previous_scenario,
                keep_student,
                st.session_state.get("name", None),  # Pass the teacher's name
                fallback_result="A student in your class is having difficulty focusing on the task."
            )
            
            # Clear the keep_student flag after use
            st.session_state['keep_student'] = False
            st.session_state['previous_scenario'] = None
        
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
        #change animation of vTuber

        count = 0
        if "vTuberCounter" not in st.session_state:
            st.session_state["vTuberCounter"] = 0
        else:
            st.session_state["vTuberCounter"] += 1
            if st.session_state["vTuberCounter"] > 5:
                st.session_state["vTuberCounter"] = 0
            count = st.session_state["vTuberCounter"]
        st.session_state["vTuberAnimation"] = ["Happy","Sad","Angry","Idling","Disgust","Surprised"][count]

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

    # Create three columns for the buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Continue Conversation"):
            # Go back to chat page
            st.session_state['page'] = 'chat'
            st.rerun()
    
    with col2:
        if st.button("New Scenario"):
            # Store that we want a completely new scenario
            st.session_state['keep_student'] = False
            # Go back to home page
            st.session_state['page'] = 'home'
            # Clear messages for new scenario
            st.session_state.messages = []
            st.rerun()
    
    with col3:
        if st.button("New Scenario (Same Student)"):
            # Extract student info from first message if available
            if len(st.session_state["messages"]) > 0:
                first_msg = st.session_state["messages"][0]
                scenario_text = first_msg.get("content", "")
                # Store the scenario text to extract student info later
                st.session_state['previous_scenario'] = scenario_text
                # Store the current grade and challenge
                st.session_state['previous_grade'] = st.session_state["gradeLevel"]
                st.session_state['previous_challenge'] = st.session_state["challenge"]
                st.session_state['keep_student'] = True
            # Go back to home page
            st.session_state['page'] = 'home'
            # Clear messages for new scenario
            st.session_state.messages = []
            st.rerun()

# Wrap the main app in a try-except block to catch any errors
try:
    # Authentication check and page routing
    st.write(f"Authentication Status: {st.session_state.get('authentication_status')}")
    st.write(f"Current Page: {st.session_state.get('page', 'Not set')}")
    
    if st.session_state.get('authentication_status') is None:
        LoginPage()
    elif st.session_state.get('authentication_status') is False:
        LoginPage()
    elif st.session_state.get('authentication_status'):
        # Debugging: check the current page
        if st.session_state['page'] == 'login':
            st.session_state['page'] = 'home'

        # page selector
        if st.session_state['page'] == 'chat':
            ChatPage()
        elif st.session_state['page'] == 'eval':
            EvalPage()
        elif st.session_state['page'] == 'home':
            StartPage()
        else:
            st.title("Something went wrong.")
            st.write(f"Current page state: {st.session_state['page']}")
except Exception as e:
    st.error(f"Application error: {str(e)}")
    st.code(traceback.format_exc())
