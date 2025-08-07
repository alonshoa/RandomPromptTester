# from time import time
import time
import streamlit as st
import datetime
import random
from typing import List, Dict, Union
from openai import OpenAI
import anthropic

# --- Initialize session state with all needed keys ---
def initialize_session_state():
    defaults = {
        "messages": [],
        "client": None,
        "uploaded_file_names": None,
        "selected_prompt_content": None,
        "selected_file_name": None,
        "user_guess": None,
        "revealed": False
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

initialize_session_state()

def replace_tags(lines: List[str], name: str, gender: str) -> List[str]:
    return [
        line.replace("[NAME]", name).replace("[GENDER]", gender)
        for line in lines
    ]


# --- Sidebar UI for credentials & prompt upload & guess ---
with st.sidebar:
    st.text_input("User ID", key="user_id")
    st.text_input("Name", key="user_name")
    st.selectbox("Gender", ["Male","Female","Other"],key="user_gender")
    st.checkbox("Use Delay", key="enable_delay")
    st.text_input("API Key", key="chatbot_api_key", type="password")

    def change_model():
        if not st.session_state.chatbot_api_key:
            st.sidebar.info("Please provide an API key.")
            st.session_state.client = None
            return
        try:
            if st.session_state.model_selector == "OpenAI":
                st.session_state.client = OpenAI(api_key=st.session_state.chatbot_api_key)
            else:
                st.session_state.client = anthropic.Anthropic(api_key=st.session_state.chatbot_api_key)
        except Exception as e:
            st.error(f"Error initializing model: {e}")
            st.session_state.client = None

    st.selectbox("Select Model", ["OpenAI", "Claude.ai"], key="model_selector", on_change=change_model)

    # Multiple-file uploader
    uploaded_files = st.file_uploader(
        "Upload prompt files (.txt)", 
        type=["txt"], 
        accept_multiple_files=True
    )

    # On first upload: pick randomly, store names, reset guess & reveal
    if uploaded_files and st.session_state.selected_prompt_content is None:
        # store list of filenames so user can guess
        st.session_state.uploaded_file_names = [f.name for f in uploaded_files]
        # randomly choose one file
        chosen = random.choice(uploaded_files)
        raw_content = chosen.read().decode("utf-8").splitlines()
        personalized_content = replace_tags(
            raw_content,
            name=st.session_state.user_name or "[NAME]",
            gender=st.session_state.user_gender or "[GENDER]"
        )
        st.session_state.selected_prompt_content = personalized_content
        st.session_state.selected_file_name = chosen.name

        # reset guess & reveal
        st.session_state.user_guess = None
        st.session_state.revealed = False
        st.success(f"{len(uploaded_files)} files uploaded; make your guess below.")

    # If we have files, show guess widget
    # if st.session_state.uploaded_file_names:
    #     st.radio(
    #         "Guess which prompt file was selected:",
    #         options=st.session_state.uploaded_file_names,
    #         key="user_guess"
    #     )

# --- Main page header ---
st.title("אלכס  ")
# st.subheader("ראש צוות ")

# --- Reveal selection button & feedback ---
# if st.session_state.selected_file_name and not st.session_state.revealed:
#     if st.button("Reveal selection"):
#         st.session_state.revealed = True
#         st.success(f"🎉 Actual Prompt File: {st.session_state.selected_file_name}")
#         # compare guess
#         if st.session_state.user_guess == st.session_state.selected_file_name:
#             st.balloons()
#             st.success("✅ Your guess was correct!")
#         else:
#             st.error(f"❌ Wrong guess. You picked “{st.session_state.user_guess}.”")

# --- Display existing chat messages ---
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- Handle new user input ---
if prompt := st.chat_input():
    # 1) Check user ID
    if not st.session_state.user_id:
        st.info("Please add your user identifier.")
        st.stop()

    # 2) Check model client
    if not st.session_state.client:
        st.error("Please select a model and provide a valid API key.")
        st.stop()

    # 3) Check that prompt was selected
    if not st.session_state.selected_prompt_content:
        st.warning("Please upload prompt files first.")
        st.stop()

    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Build system messages from the chosen prompt file
    sys_messages = [
        {"role": "system", "content": line}
        for line in st.session_state.selected_prompt_content
    ]

    # Generate assistant response
    def get_response(
        client: Union[OpenAI, anthropic.Anthropic],
        messages: List[Dict[str, str]],
        sys_messages: List[Dict[str, str]]
    ) -> tuple[str, float]:
        try:
            start_time = time.time()
            if isinstance(client, OpenAI):
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=sys_messages + messages
                )
                elapsed = time.time() - start_time
                return resp.choices[0].message.content,elapsed
            else:  # Claude.ai
                resp = client.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    messages=[m for m in messages if m["role"] in ["user", "assistant"]],
                    system="\n".join([m["content"] for m in sys_messages]),
                    max_tokens=4096,
                )
                elapsed = time.time() - start_time
                return resp.content[0].text,elapsed
        except Exception as e:
            st.error(f"Error getting response: {e}")
            return "Error",0

    reply,tim_took = get_response(st.session_state.client, st.session_state.messages, sys_messages)
    if st.session_state.enable_delay:
        total_delay = random.randint(10, 15)
        remaining = total_delay - tim_took
        if remaining > 0:
            time.sleep(remaining)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)

# --- Download chat transcript (only after reveal) ---
def collect_data_for_download() -> str:
    header = "\n".join(st.session_state.selected_prompt_content or [])
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.messages)
    return f"System Prompt:\n{header}\n\nConversation:\n{convo}"

def get_file_name() -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"chat_{st.session_state.user_id}_{ts}.txt"

# if st.session_state.revealed:
st.download_button(
    label="Download Chat Transcript",
    data=collect_data_for_download(),
    file_name=get_file_name(),
    mime="text/plain"
)
