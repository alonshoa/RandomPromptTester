FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

# Streamlit must listen on 0.0.0.0 and use PORT
CMD ["bash", "-lc", "streamlit run RandomPromptChoose.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true"]
