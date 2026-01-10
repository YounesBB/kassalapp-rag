# 🚀 Deployment Guide: Kassalapp Assistant

This guide provides instructions for both local development and cloud deployment on Hugging Face Spaces.

---

## ☁️ Cloud Deployment: Hugging Face Spaces

This application is designed to run seamlessly on **Hugging Face Spaces** using the Streamlit SDK.

### 1. Create a New Space
*   Go to [Hugging Face Spaces](https://huggingface.co/new-space).
*   Select **Streamlit** as the SDK.
*   Choose a name (e.g., `kassalapp-assistant`).

### 2. Configure Secrets
In your Space settings, go to the **Variables and secrets** section and add the following keys:

| Secret Key | Description |
| :--- | :--- |
| `GROQ_API_KEY` | Your [Groq Cloud](https://console.groq.com/) API Key. |
| `KASSALAPP_API_KEY` | Your [Kassalapp API](https://kassal.app/api/) Key. |
| `PINECONE_API_KEY` | Your [Pinecone Cloud](https://www.pinecone.io/) API Key. |
| `PINECONE_INDEX_NAME` | The name of your index (e.g., `kassalapp-index`). |
| `GROQ_MODEL` | Default: `llama-3.3-70b-versatile`. |

### 3. Deploy
*   Push your code to the Hugging Face Space repository.
*   The space will automatically build and start using the `app.py` entry point.

---

## 💻 Local Development Setup

Follow these steps to run the assistant on your local machine.

### 1. Prerequisites
*   Python 3.10 or higher.
*   Git.

### 2. Installation
```bash
git clone https://github.com/your-username/kassalapp-rag.git
cd kassalapp-rag
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and copy the contents from `.env.example`:
```bash
# Example .env
GROQ_API_KEY=your_key
KASSALAPP_API_KEY=your_key
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=kassalapp-index
```

### 4. Data Synchronization
Before running the app locally, you must sync your knowledge base to the cloud:
```bash
python sync_to_pinecone.py
```

### 5. Running the Application
```bash
streamlit run app.py
```

---

## 🛡️ Universal Secrets Management
The application is built with a **"Dual-Aware"** logic. It automatically detects if it is running in a cloud environment (Hugging Face/Streamlit Cloud) by checking `st.secrets`. If not found, it falls back to local environment variables (`.env`). This ensures a zero-config transition for developers moving from local to production.
