FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY environment.py .
COPY app.py .
COPY baseline.py .
COPY openenv.yaml .
COPY README.md .

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
