import time
import io
import datetime
import random
from typing import List, Dict, Union

import streamlit as st
# from openai import OpenAI
import anthropic
from anthropic import Anthropic

# from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials       # ✅ correct
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


# ---------------------------
# Streamlit basic page config
# ---------------------------
st.set_page_config(
    page_title="Experiment Chat",
    layout="centered"
)

@st.cache_resource
def get_claude_client():
    api_key = st.secrets["ANTHROPIC_API_KEY"]
    return Anthropic(api_key=api_key)

# ---------------------------
# Session state initialization
# ---------------------------
def initialize_session_state():
    defaults = {
        "messages": [],
        "selected_prompt_content": None,
        "user_id": None,
        "user_name": None,
        "user_gender": None,
        "case_id": None,
        "log_file_name": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


initialize_session_state()


# ---------------------------
# URL parameters
# ---------------------------
def get_query_params():
    # Newer Streamlit: st.query_params, older: experimental_get_query_params
    if hasattr(st, "query_params"):
        params = st.query_params
    else:
        params = st.experimental_get_query_params()

    def get_single(name, default=None):
        if name not in params:
            return default
        val = params[name]
        if isinstance(val, list):
            return val[0]
        return val

    user_id = get_single("user_id")
    user_name = get_single("name", "")
    user_gender = get_single("gender", "")

    return user_id, user_name, user_gender


# ---------------------------
# Google Drive helpers
# ---------------------------
@st.cache_resource
def get_drive_service():
    """
    Expects a service account in st.secrets["gdrive_service_account"],
    and grants access to Drive.
    """
    info = st.secrets["gdrive_service_account"]  # dict-like
    creds = Credentials.from_authorized_user_info(
        info,
        scopes=info["scopes"]
    )
    return build("drive", "v3", credentials=creds)


def get_or_create_subfolder(service, parent_id: str, folder_name: str) -> str:
    """
    Returns the ID of a subfolder named `folder_name` under `parent_id`.
    If it does not exist, creates it.
    """
    query = (
        f"'{parent_id}' in parents and "
        f"mimeType = 'application/vnd.google-apps.folder' and "
        f"name = '{folder_name}' and "
        f"trashed = false"
    )
    resp = service.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)"
    ).execute()
    files = resp.get("files", [])

    if files:
        return files[0]["id"]

    # Create the folder
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    new_folder = service.files().create(
        body=metadata,
        fields="id"
    ).execute()
    return new_folder["id"]


def read_text_file_from_drive(service, file_id: str) -> List[str]:
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    content = fh.read().decode("utf-8")
    return content.splitlines()


def get_prompt_file_id_for_case(service, folder_id: str, case_id: int) -> str:
    """
    Finds a text file in folder whose name contains 'case<case_id>'.
    E.g. case1.txt, case1_prompt.txt, etc.
    """
    query = (
        f"'{folder_id}' in parents and "
        f"mimeType='text/plain' and "
        f"name contains 'case{case_id}' and "
        f"trashed = false"
    )
    resp = service.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)"
    ).execute()
    files = resp.get("files", [])
    if not files:
        raise RuntimeError(f"No prompt file found in Drive for case {case_id}")
    return files[0]["id"]


def write_transcript_to_drive(
    service,
    folder_id: str,
    filename: str,
    content: str
):
    """
    Create or overwrite a text file in the given folder.
    """
    # Search for existing file with same name in that folder
    query = (
        f"'{folder_id}' in parents and "
        f"name = '{filename}' and "
        f"mimeType='text/plain' and "
        f"trashed = false"
    )
    resp = service.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)"
    ).execute()
    files = resp.get("files", [])

    media = MediaIoBaseUpload(
        io.BytesIO(content.encode("utf-8")),
        mimetype="text/plain",
        resumable=False
    )

    if files:
        file_id = files[0]["id"]
        service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
    else:
        file_metadata = {
            "name": filename,
            "parents": [folder_id],
            "mimeType": "text/plain"
        }
        service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()


# # ---------------------------
# # OpenAI client helper
# # ---------------------------
# @st.cache_resource
# def get_openai_client():
#     api_key = st.secrets["OPENAI_API_KEY"]
#     return OpenAI(api_key=api_key)


# ---------------------------
# Prompt personalization
# ---------------------------
def replace_tags(lines: List[str], name: str, gender: str) -> List[str]:
    return [
        line.replace("[NAME]", name or "[NAME]").replace("[GENDER]", gender or "[GENDER]")
        for line in lines
    ]


# ---------------------------
# Transcript building
# ---------------------------
def build_full_transcript(
    prompt_lines: List[str],
    messages: List[Dict[str, str]]
) -> str:
    header = "\n".join(prompt_lines or [])
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    return f"System Prompt:\n{header}\n\nConversation:\n{convo}"


# ---------------------------
# Response generation
# ---------------------------
def get_response(
    client: Anthropic,
    messages: List[Dict[str, str]],
    sys_lines: List[str],
) -> tuple[str, float]:
    """
    client   - Anthropic client
    messages - st.session_state.messages (user/assistant history)
    sys_lines - list of system prompt lines from the prompt file
    """
    try:
        # system_text = "\n".join(sys_lines or [])
        system_text = "\n".join([line["content"] for line in sys_lines])

        start_time = time.time()
        resp = client.messages.create(
            # use whichever Claude model you want to lock in
            model="claude-sonnet-4-5-20250929",   # example, stable snapshot ID :contentReference[oaicite:1]{index=1}
            max_tokens=4096,
            system=system_text,
            messages=[
                m for m in messages
                if m["role"] in ("user", "assistant")
            ],
        )
        elapsed = time.time() - start_time

        # Claude returns a list of content blocks; we just join all text blocks
        reply_text = "".join(
            block.text
            for block in resp.content
            if block.type == "text"
        )

        return reply_text, elapsed

    except Exception as e:
        st.error(f"Error getting response from Claude: {e}")
        return "Error", 0.0


# def get_response_openai(
#     client: OpenAI,
#     messages: List[Dict[str, str]],
#     sys_messages: List[Dict[str, str]]
# ) -> tuple[str, float]:
#     try:
#         start_time = time.time()
#         resp = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=sys_messages + messages
#         )
#         elapsed = time.time() - start_time
#         return resp.choices[0].message.content, elapsed
#     except Exception as e:
#         st.error(f"Error getting response: {e}")
#         return "Error", 0.0


# ---------------------------
# Initial setup from URL
# ---------------------------
# Read URL parameters only once per session
if st.session_state.user_id is None:
    user_id_param, name_param, gender_param = get_query_params()
    st.session_state.user_id = user_id_param
    st.session_state.user_name = name_param or ""
    st.session_state.user_gender = gender_param or ""

# Validate user_id
if not st.session_state.user_id:
    st.error("Missing 'user_id' in URL. Please access the app with ?user_id=<id>.")
    st.stop()

try:
    uid_int = int(st.session_state.user_id)
except ValueError:
    st.error("user_id must be an integer.")
    st.stop()

# Case selection
if st.session_state.case_id is None:
    case_idx = uid_int % 4
    st.session_state.case_id = case_idx + 1  # 1..4

case_id = st.session_state.case_id

# Delay decision
use_delay = case_id in (2, 4)

# Google Drive service & prompt loading
PROMPT_FOLDER_ID = st.secrets["GDRIVE_PROMPT_FOLDER_ID"]  # set this in secrets

drive_service = get_drive_service()

LOG_FOLDER_ID = get_or_create_subfolder(
    drive_service,
    PROMPT_FOLDER_ID,
    "conversation_log"
)

if st.session_state.selected_prompt_content is None:
    # 1) Find prompt file for this case
    prompt_file_id = get_prompt_file_id_for_case(drive_service, PROMPT_FOLDER_ID, case_id)
    # 2) Read raw lines
    raw_prompt_lines = read_text_file_from_drive(drive_service, prompt_file_id)
    # 3) Personalize with name/gender
    personalized_lines = replace_tags(
        raw_prompt_lines,
        st.session_state.user_name,
        st.session_state.user_gender
    )
    st.session_state.selected_prompt_content = personalized_lines

# Prepare log file name once
if st.session_state.log_file_name is None:
    date_str = datetime.datetime.now().strftime("%d_%m_%Y")
    st.session_state.log_file_name = (
        f"{st.session_state.user_id}_{date_str}_case{case_id}.txt"
    )


# ---------------------------
# Main UI
# ---------------------------
st.title("אלכס המנהל")

st.markdown(
    f"**User ID:** {st.session_state.user_id} &nbsp;&nbsp; "
    f"**Case:** {case_id}"
)

# Optionally show name/gender for debugging (can be removed in production)
st.caption(
    f"Participant: {st.session_state.user_name or '[no name]'} "
    f"({st.session_state.user_gender or 'no gender'})"
)

# Display existing messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Ensure model client and prompt exist
    # client = get_openai_client()
    client = get_claude_client()

    if not st.session_state.selected_prompt_content:
        st.error("Prompt not loaded. Please contact the experimenter.")
        st.stop()

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Build system messages
    sys_messages = [
        {"role": "system", "content": line}
        for line in st.session_state.selected_prompt_content
    ]

    # Get model response
    reply, elapsed = get_response(client, st.session_state.messages, sys_messages)

    # Apply artificial delay for cases 2 and 4
    if use_delay:
        total_delay = random.randint(10, 15)
        remaining = total_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    # Show assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").write(reply)

    # Build transcript and write to Google Drive
    transcript = build_full_transcript(
        st.session_state.selected_prompt_content,
        st.session_state.messages
    )
    write_transcript_to_drive(
        drive_service,
        PROMPT_FOLDER_ID,
        st.session_state.log_file_name,
        transcript
    )


# ---------------------------
# Local download button (optional)
# ---------------------------
if st.session_state.messages:
    transcript = build_full_transcript(
        st.session_state.selected_prompt_content,
        st.session_state.messages
    )
    st.download_button(
        label="Download Chat Transcript",
        data=transcript,
        file_name=st.session_state.log_file_name,
        mime="text/plain"
    )
