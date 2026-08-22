FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for FAISS and compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Download HuggingFace models during build time (optional but recommended to avoid cold starts)
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); SentenceTransformer('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY . .

# Expose port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
