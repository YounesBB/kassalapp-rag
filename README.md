# 🛒 Kassalapp Assistant (Groq & Llama 3.3 Edition)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rag-kassal-v2.streamlit.app/) <!-- Replace with actual URL after deploy -->

**An intelligent, Norwegian grocery shopping assistant built with Groq (Llama 3.3) and the [Kassalapp API](https://kassal.app/api/).**

This project demonstrates a **Hybrid AI Architecture** combining **Local RAG (ChromaDB)** for expert domain knowledge with **Real-Time Tool Execution** for live grocery market data.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/streamlit-1.31%2B-red) ![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange)

---

## 🚀 Deployment Guide

This app is designed to be deployed for free on **Streamlit Community Cloud**.

### 1. Push to GitHub
Upload all project files (except `.env` and `__pycache__`) to a public GitHub repository.

### 2. Connect to Streamlit
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Connect your GitHub account.
3. Click "New App" and select this repository.

### 3. Configure Secrets (Critical)
Streamlit Cloud doesn't use `.env` files. Instead, follow these steps:
1. In the Streamlit deployment dashboard, go to **Settings > Secrets**.
2. Paste the following (with your actual keys):
```toml
GROQ_API_KEY = "your_key_here"
KASSALAPP_API_KEY = "your_key_here"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

---

## 🧠 Architecture: How it Works

This project implements a **Hybrid Agent Architecture** to provide both static expert advice and live market data.

### 1. Local RAG (Retrieval Augmented Generation)
Instead of relying on LLM training data, we use a local knowledge base (`knowledge/expert_guide.md`):
*   **Vector Database**: [ChromaDB](https://www.trychroma.com/) runs locally or in the cloud container.
*   **Embeddings**: We use `sentence-transformers` to turn text into math vectors for semantic search.
*   **Process**: When you ask "What is Trumf?", the app searches the guide for relevant paragraphs and feeds them to Llama 3.3 to ensure 100% accurate Norwegian context.

### 2. Real-Time Tool Calling
LLMs cannot see the current price of milk at Meny. 
*   **Function Calling**: When the model detects you want live data, it calls the `search_products` or `search_physical_stores` functions.
*   **Data Engineering**: We strip out ~70% of unnecessary API metadata (images, technical codes) before feeding it to the LLM to keep responses fast and cheap.

---

## 🛠️ Tech Stack

*   **Frontend**: [Streamlit](https://streamlit.io/)
*   **LLM Inference**: [Groq](https://groq.com/) (Llama 3.3 70B)
*   **RAG Engine**: Local ChromaDB + Sentence Transformers
*   **Data Source**: [Kassalapp API](https://kassal.app/)
*   **Env Manager**: `python-dotenv`

---

## 📂 Local Setup

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Configure Keys**: Create a `.env` file with `GROQ_API_KEY` and `KASSALAPP_API_KEY`.
3. **Run App**: `streamlit run app.py`

---

Built with ❤️ using **Groq** and **Llama**.
