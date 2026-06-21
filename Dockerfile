FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY RandomPromptChoose.py app_language.py case_file_loader.py ./
COPY case_files ./case_files

EXPOSE 8501

CMD ["streamlit", "run", "RandomPromptChoose.py", "--server.address=0.0.0.0", "--server.port=8501"]
