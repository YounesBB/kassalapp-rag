---
title: Kassalapp Assistant V3
emoji: 🛒
colorFrom: green
colorTo: blue
sdk: streamlit
sdk_version: 1.52.2
app_file: app.py
pinned: false
---

# 🛒 Kassalapp Assistant (V3 Cloud Edition)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://huggingface.co/spaces/YounesBB/kassalapp-assistant)

**An intelligent, Norwegian grocery shopping assistant built with Groq (Llama 3.3) and the [Kassalapp API](https://kassal.app/api/).**

This project demonstrates a **Cloud-Hybrid RAG Architecture** combining **Pinecone Cloud** for expert domain knowledge with **Real-Time Tool Execution** for live grocery market data.

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Streamlit](https://img.shields.io/badge/streamlit-1.31%2B-red) ![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange) ![Pinecone](https://img.shields.io/badge/DB-Pinecone-blueviolet)

---

## 🧠 Architecture: How it Works

The V3 migration transitions the app to a "Cloud-Hybrid" model, optimized for production hosting.

### 1. Cloud RAG (Retrieval Augmented Generation)
Instead of relying on LLM training data, we use a cloud-native knowledge base:
*   **Vector Database**: [Pinecone](https://www.pinecone.io/) (Serverless) handles all semantic retrieval.
*   **Embeddings**: Local `sentence-transformers` generate vectors, which are then queried against the Pinecone cloud index.
*   **Synchronization**: The `sync_to_pinecone.py` utility handles data ingestion with memory-efficient streaming.

### 2. Real-Time Tool Calling
LLMs cannot see the current price of milk at Meny. 
*   **Function Calling**: When the model detects you want live data, it calls the `search_products` or `search_physical_stores` functions.
*   **Data Engineering**: We strip out ~70% of unnecessary API metadata to keep responses fast and token-efficient.

---

## 🛠️ Tech Stack

*   **Frontend**: [Streamlit](https://streamlit.io/)
*   **LLM Inference**: [Groq](https://groq.com/) (Llama 3.3 70B)
*   **Vector Store**: [Pinecone Cloud](https://pinecone.io/)
*   **Embeddings**: `all-MiniLM-L6-v2`
*   **Data Source**: [Kassalapp API](https://kassal.app/)

---

## 📂 Deployment Configuration (Hugging Face / Streamlit)

This app supports **Streamlit Secrets**. Configure the following keys in your dashboard:

```toml
GROQ_API_KEY = "your_key"
KASSALAPP_API_KEY = "your_key"
PINECONE_API_KEY = "your_key"
PINECONE_INDEX_NAME = "kassalapp-index"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

---

## 💻 Local Developer Setup

1. **Install**: `pip install -r requirements.txt`
2. **Configure**: Add keys to a `.env` file.
3. **Sync Data**: Run `python sync_to_pinecone.py` to populate your cloud index.
4. **Run**: `streamlit run app.py`

Built with ❤️ using **Groq**, **Pinecone**, and **Kassalapp**.
