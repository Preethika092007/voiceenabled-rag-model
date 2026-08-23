# EchoRAG

A modern, voice-enabled Retrieval-Augmented Generation (RAG) system built with React, FastAPI, Groq (Llama 3), ElevenLabs, and FAISS.

## Architecture

EchoRAG utilizes a split-stack architecture to maintain a lightweight frontend while supporting heavy Machine Learning dependencies on the backend.

### Frontend
- **Framework**: React + Vite
- **Styling**: Tailwind CSS v4
- **Components**: Lucide React icons
- **Deployment**: Vercel (Recommended)

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database/Retrieval**: FAISS (Dense) + BM25 (Sparse)
- **Reranking**: Cross-Encoder (MS-MARCO MiniLM)
- **LLM**: Groq (Llama 3 8B)
- **Speech-to-Text**: ElevenLabs (Scribe v2)
- **Deployment**: Render, Railway, or any Docker-compatible PaaS.

## Setup Instructions

### Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment and install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill in your `LLM_API_KEY` and `ELEVENLABS_API_KEY`.
5. Run the server: `uvicorn main:app --reload`

### Frontend Setup
1. Navigate to the root directory.
2. Install dependencies: `npm install`
3. Copy `.env.example` to `.env.local` and set `VITE_API_URL=http://localhost:8000`.
4. Run the development server: `npm run dev`

## Deployment

### Deploying the Frontend (Vercel)
1. Install the Vercel CLI: `npm i -g vercel`
2. Login to Vercel: `vercel login`
3. Deploy the app: `vercel --prod`
4. Make sure to set `VITE_API_URL` to your live backend URL in the Vercel project settings.

### Deploying the Backend (Docker / Render)
The backend includes a `Dockerfile` and `render.yaml` for easy deployment to container platforms. Note that the machine learning models (FAISS, SentenceTransformers, Cross-Encoders) require at least 1GB of RAM to run effectively. Vercel Serverless Functions are not recommended for the backend due to size and timeout limits.
