import streamlit as st
from __init__ import vtuber


st.subheader("Component with variable args")

# Create a second instance of our component whose `name` arg will vary
# based on a text_input widget.
#
# We use the special "key" argument to assign a fixed identity to this
# component instance. By default, when a component's arguments change,
# it is considered a new instance and will be re-mounted on the frontend
# and lose its current state. In this case, we want to vary the component's
# "name" argument without having it get recreated.
selected_option = st.selectbox("Select an option", ["Idling", "Angry", "Sad"])
txtBox = st.text_input("Animation",value="F Angry")
vtuber(anim=txtBox,key="foo")
