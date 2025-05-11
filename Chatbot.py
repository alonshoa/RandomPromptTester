import streamlit as st
st.set_page_config(initial_sidebar_state="expanded")

import datetime
import re
from typing import List, Dict, Union
from openai import OpenAI
import anthropic
from utils import cases, image



# Initialize session state with default messages and system configuration
def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state["system_messages"] = cases["case 1"]
        st.session_state["current_assistant_avatar"] = image["assistant_case 1"]
        st.session_state["messages"] = []
        st.session_state["client"] = None

# Handle model changes and API key validation
def change_model():
    if not st.session_state.get("chatbot_api_key"):
        st.sidebar.info("Please provide an API key.")
        st.session_state.client = None
        return

    # Initialize appropriate client based on selected model
    selected_value = st.session_state.model_selector
    try:
        if selected_value == "OpenAI":
            st.session_state.client = OpenAI(api_key=st.session_state.chatbot_api_key)
        elif selected_value == "Claude.ai":
            st.session_state.client = anthropic.Anthropic(api_key=st.session_state.chatbot_api_key)
        else:
            st.session_state.client = None
    except Exception as e:
        st.error(f"Error initializing model: {str(e)}")
        st.session_state.client = None

# Update system messages when case selection changes
def case_changed():
    case = st.session_state.case_selector
    if case == "select the case before start":
        return
    
    st.session_state["system_messages"] = [prompt for prompt in cases[case]]
    st.session_state["current_assistant_avatar"] = image.get(f"assistant_{case}", image["default"])
    st.session_state["current_header_image"] = image.get(f"header_{case}", "images/thumbsup.jpg")
    st.session_state["messages"] = []

# Generate response based on selected model (OpenAI or Claude)
def get_response(client: Union[OpenAI, anthropic.Anthropic], 
                messages: List[Dict[str, str]], 
                sys_messages: List[str]) -> str:
    try:
        # Handle OpenAI response generation
        if isinstance(client, OpenAI):
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": sys_msg} for sys_msg in sys_messages] + messages
            )
            return response.choices[0].message.content
        # Handle Claude response generation
        elif isinstance(client, anthropic.Anthropic):
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",
                messages=[msg for msg in messages if msg["role"] in ["user", "assistant"]],
                system="".join(sys_messages),
                max_tokens=4096,
            )
            return response.content[0].text
    except Exception as e:
        st.error(f"Error getting response: {e}")
        return "Error"

def collect_data_for_download() -> str:
    msg_list = [f"system: {c}" for c in cases[st.session_state.case_selector]]
    msg_list.extend([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
    return "\n".join(msg_list)

def get_file_name() -> str:
    return f"chat_{st.session_state['user_id']}_{st.session_state.case_selector}_{datetime.datetime.now()}.txt"

def parse_questions(text: str) -> List[str]:
    questions = []
    start = text.find("רשימת השאלות:")
    if start == -1:
        return questions  # Return empty list if the section is not found
    
    lines = text[start:].split('\n')[1:]  # Get lines after "רשימת השאלות:"
    
    for line in lines:
        match = re.match(r'\d+\.\s*(.*)', line)  # Match lines that start with a number
        if match:
            questions.append(match.group(1).strip())
        elif questions:  # Stop if a non-question line appears after starting
            break
    
    return questions


    

def update_sys_messages(file_content: str):
    if file_content:
        if "current_question" not in st.session_state:
            st.session_state["questions"] = parse_questions(file_content)
            st.session_state["current_question"] = -1
        st.session_state['system_messages'] = file_content.split("\n")
        st.session_state['system_messages'] = [msg for msg in st.session_state['system_messages'] if msg.strip()]
        st.session_state['system_messages'] += [f"עוד לא התחלת לשאול שאלות"]
        return st.session_state['system_messages'], st.session_state['questions']


# Initialize session state
initialize_session_state()

# Sidebar UI
with st.sidebar:
    st.text_input("User Id", key="user_id", type="default")
    st.text_input("API Key", key="chatbot_api_key", type="password")
    st.selectbox("Select model vendor", options=["OpenAI", "Claude.ai"], on_change=change_model, key="model_selector")
    st.selectbox("Select case", options=list(cases.keys()), on_change=case_changed, key="case_selector")
    
    uploaded_file = st.file_uploader("Upload a file", type=["txt"])
    if uploaded_file is not None:
        st.session_state["uploaded_file"] = uploaded_file
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        if uploaded_file.name.endswith(".txt"):
            file_content = uploaded_file.read().decode("utf-8")
            if not "questions" in st.session_state:
                system_messages,questions = update_sys_messages(file_content)
                st.session_state['system_messages'] = system_messages
                st.session_state['questions'] = questions



# Main chat interface
col1, col2 = st.columns([3, 1])
with col1:
    st.title("The 💗 Chatbot")
if "current_header_image" in st.session_state:
    with col2:
        st.image(st.session_state.get("current_header_image", "images/download_1.jpg"), width=100,)
# st.caption(r"🚀 A Streamlit 💗 chatbot ")

# Display chat messages
for msg in st.session_state.messages:
    # avatar = image["user"] if msg["role"] == "user" else st.session_state.get("current_assistant_avatar", image["default"])
    st.chat_message(msg["role"]).write(msg["content"])

# Handle user input
if prompt := st.chat_input():
    if not st.session_state.get("user_id"):
        st.info("Please add your user identifier.")
        st.stop()

    if not st.session_state.client:
        st.error("Please select a model and provide a valid API key.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    msg = get_response(st.session_state.client, st.session_state.messages, st.session_state.system_messages)
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    st.session_state["current_question"] += 1
    if st.session_state["current_question"] < len(st.session_state['questions']):
        st.session_state['system_messages'][-1]= f"{st.session_state['questions'][st.session_state['current_question']]}"
    else:
        st.session_state['system_messages'][-1]="נגמרו השאלות, תודה על השיחה!"

# Download chat history
if st.session_state.messages:
    with st.sidebar:
        st.download_button(
            label="Download chat as text",
            data=collect_data_for_download(),
            file_name=get_file_name(),
            mime="text/txt"
        )
