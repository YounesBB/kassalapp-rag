import streamlit as st
import os

# Configuration (MUST be the first Streamlit command)
st.set_page_config(page_title="Kassalapp Assistant", page_icon="🛒", layout="wide", initial_sidebar_state="expanded")

import json
from dotenv import load_dotenv
from groq import Groq
from tools import (
    search_products,
    get_product_by_id,
    get_product_by_ean,
    search_physical_stores,
    find_physical_store_by_id,
    compare_product_prices_by_url,
    format_product_list
)
from rag_engine import KassalappRAG

# Load environment variables
load_dotenv(override=True)

# --- CUSTOM CSS (Glassmorphism & Premium UI) ---
st.markdown("""
<style>
    /* Main background - Deep Space Gradient */
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1c23 100%);
        color: #fafafa;
    }

    /* Force Sidebar Collapse Button Visibility */
    [data-testid="sidebar-user-features"] + div button,
    button[kind="headerNoPadding"] {
        opacity: 1 !important;
        visibility: visible !important;
        color: white !important;
    }

    /* Glassmorphism Chat Containers */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        margin-bottom: 1rem !important;
    }

    /* Status Badge Styling */
    .status-badge {
        display: inline-block;
        white-space: nowrap;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        background: rgba(0, 255, 127, 0.1);
        color: #00ff7f;
        border: 1px solid rgba(0, 255, 127, 0.2);
        margin-top: 5px;
    }

    .stTextInput > div > div > input {
        background-color: #262730;
        color: #ffffff;
        border-radius: 10px;
        border: 1px solid #4a4a4a;
    }
    
    .stButton > button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        background-color: #ff6b6b;
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hi! 👋 I am your **Kassalapp Assistant**. I can help you find grocery prices at stores like Kiwi, Meny, Rema 1000, and more. \n\n**⚡ Tip:** Specific questions (like *'Price of Pepsi Max at Kiwi'*) yield the fastest and most accurate results!"
        }
    ]

# Constants
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Initialize RAG Engine
if "rag" not in st.session_state:
    with st.spinner("Connecting to Knowledge Base..."):
        st.session_state.rag = KassalappRAG()

# Initialize Groq Client
if "client" not in st.session_state:
    # Universal Secrets: Try Streamlit Secrets (Cloud), then Environment Variables (Local)
    try:
        api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    except Exception:
        api_key = os.getenv("GROQ_API_KEY")
        
    if not api_key:
        st.error("GROQ_API_KEY not found. Please set it as a Secret or Environment Variable.")
        st.stop()
    st.session_state.client = Groq(api_key=api_key)

rag = st.session_state.rag
client = st.session_state.client

# Define Tools for Groq (Aligned with OpenAPI Spec)
tools = [
     {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search for groceries and products to find the price and store. Use the 'store' parameter to filter by a specific store (KIWI, REMA_1000, MENY_NO, SPAR_NO, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "The product name (min 3 chars)."},
                    "store": {"type": "string", "description": "Store filter: KIWI, REMA_1000, MENY_NO, SPAR_NO, etc."}
                },
                "required": ["search"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_physical_stores",
            "description": "Find grocery stores by location, name, or chain (group).",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "City or location name."},
                    "group": {"type": "string", "description": "Chain name (e.g. KIWI, REMA_1000, COOP_NO, MENY_NO)."}
                }
            }
        }
    }
]

# Helper to execute tools
def execute_tool(name, args):
    if name == "search_products":
        # Type coercion: Convert string numbers to integers
        if "size" in args and isinstance(args["size"], str):
            try:
                args["size"] = int(args["size"])
            except (ValueError, TypeError):
                args["size"] = 10  # Default fallback
        
        # Ensure Store code is correct for API
        if "store" in args and args["store"]:
            s = args["store"].upper()
            if s == "MENY": s = "MENY_NO"
            if s == "SPAR": s = "SPAR_NO"
            if s == "REMA": s = "REMA_1000"
            args["store"] = s
        return search_products(**args)
    elif name == "search_physical_stores":
        # Type coercion for size parameter
        if "size" in args and isinstance(args["size"], str):
            try:
                args["size"] = int(args["size"])
            except (ValueError, TypeError):
                args["size"] = 20  # Default fallback
        return search_physical_stores(**args)
    return {"error": "Tool not found"}

# Main UI
st.title("🛒 Kassalapp Assistant")
st.markdown("""
**Expert AI for Norwegian Groceries** using the [Kassalapp API](https://kassal.app/api/).
The AI will help you find information such as prices and products across several Norwegian grocery chains.

💡 **Try asking:**
* *"What is the price of Coca Cola at Meny?"*
* *"What is Trumf and how does it work?"*
* *"Find a Kiwi store in Oslo."*

> ⚡ **Tip:** Specific questions (mentioning a store or product brand) yield better and much faster results!
""")

# Sidebar
with st.sidebar:
    st.title("🛒 Kassalapp AI")
    st.markdown("---")
    
    # Cloud Status Badge
    st.markdown('**System Status**<br><span class="status-badge">Pinecone Connected</span>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.info("""
    **Kassalapp AI Engine**
    - **RAG**: Pinecone Cloud
    - **Intelligence**: Groq Llama 3.3
    - **Real-time Data**: Kassalapp API
    """)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Model Selection UI
    selected_model = st.selectbox(
        "Select Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        index=0 if DEFAULT_MODEL == "llama-3.3-70b-versatile" else 1,
        help="llama-3.3 is higher quality, llama-3.1 is faster with higher daily limits."
    )
    MODEL_NAME = selected_model
    
    st.info(f"**Active Model**: `{MODEL_NAME}`")
    st.markdown("---")
    st.markdown("### 💡 Model Switching")
    st.markdown("""
    **Hit limits?** Change model in `.env`:
    - `llama-3.1-8b-instant`: **500K Tokens / Day** 🚀
    - `llama-3.2-90b-text-preview`: **500K Tokens / Day**
    
    ⚠️ *Must support tool calling!*
    
    Then restart the app.
    """)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about grocery prices, stores, or loyalty programs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # 1. Check for greetings or very short messages to avoid over-eager tool/rag
        greetings = ["hi", "hello", "hei", "hallo", "hey"]
        is_greeting = any(g in prompt.lower().split() for g in greetings)
        
        if is_greeting and len(prompt.split()) < 3:
            final_text = "Hello! I am your Kassalapp Assistant. How can I help you find groceries or store info today?"
            message_placeholder.markdown(final_text)
            st.session_state.messages.append({"role": "assistant", "content": final_text})
        else:
            # 2. RAG Retrieval
            relevant_docs = rag.query(prompt, n_results=2)
            context = "\n".join(relevant_docs)
            
            system_prompt = f"""You are Kassalapp Assistant, a precise guide to Norwegian groceries.
            
            CONTEXT FROM GUIDE:
            {context}
            
            TOOLS:
            - search_products: Use for specific price or availability questions.
            - search_physical_stores: Use to find store locations or chains.
            
            INSTRUCTIONS:
            - If the question can be answered by the Context above, answer directly.
            - If you need real-time data, use the tool calling feature.
            - If a product query is ambiguous (e.g., "Coca Cola" could mean regular, sugar-free, different sizes), ask the user to clarify BEFORE using tools.
            - After receiving tool results, always present them to the user in a clear, friendly format.
            - If tool results show no price data or empty results, inform the user politely.
            - DO NOT output tool names in tags like <function> or within the text.
            - Be concise but helpful.
            """
            
            messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages:
                messages.append({"role": m["role"], "content": m["content"]})
                
            try:
                # LLM Loop
                max_turns = 3
                current_turn = 0
                final_text = None
                
                while current_turn < max_turns:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        temperature=0.1 # Lower temperature for stability
                    )
                    
                    response_message = response.choices[0].message
                    
                    # Check if there are tool calls to execute
                    if not response_message.tool_calls:
                        # No tool calls - this is the final response
                        messages.append(response_message)
                        final_text = response_message.content
                        if final_text:
                            message_placeholder.markdown(final_text)
                            st.session_state.messages.append({"role": "assistant", "content": final_text})
                        break
                    
                    # There are tool calls - add message and execute them
                    # DO NOT display content here, even if present - wait for final synthesis
                    messages.append(response_message)
                    
                    # Execute tool calls
                    for tool_call in response_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        
                        with st.status(f"🛠️ Connecting to Kassalapp: `{func_name}`", expanded=True):
                            st.write(f"Parameters: `{func_args}`")
                            try:
                                result = execute_tool(func_name, func_args)
                                st.write(f"Result: `{result}`")  # DEBUG: Show what we got back
                            except Exception as e:
                                result = {"error": str(e)}
                                st.error(f"Tool execution error: {str(e)}")
                        
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": json.dumps(result)
                        })
                    
                    current_turn += 1
                
                # If we exit the loop without a final response, show an error
                if final_text is None and current_turn >= max_turns:
                    error_msg = "I apologize, but I encountered an issue processing the results. Please try your question again."
                    message_placeholder.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
            except Exception as e:
                st.error(f"API Error: {str(e)}")

