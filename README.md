# 🎲 Random Prompt Chat

This Streamlit app lets you upload multiple prompt text files, randomly selects one, and then chat with either OpenAI or Claude using the chosen prompt as system instructions. It supports simple personalization tokens for the user's name and gender, optional response delays, and transcript downloads.

## Features
- Upload multiple `.txt` prompts and have one selected at random.
- Replace `[NAME]` and `[GENDER]` placeholders with sidebar inputs.
- Talk to either OpenAI (Chat Completions) or Anthropic Claude.
- Optional artificial response delay to simulate longer processing.
- Download the full conversation along with the selected prompt.

## Setup
```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the app
```sh
streamlit run RandomPromptChoose.py
```

Provide your API key and user details in the sidebar, upload one or more prompt files, and start chatting.
