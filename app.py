"""
Streamlit Chatbot using Semantic Kernel with GPT-4
A simple chatbot that uses Semantic Kernel with custom plugins/tools
"""

import os
import asyncio
from dotenv import load_dotenv
import streamlit as st
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import KernelArguments

from plugins import KnowledgePlugin

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Databricks Genie Chatbot",
    layout="centered"
)

# Title and description
st.title("Databricks Genie Chatbot")


def initialize_kernel():
    """Initialize Semantic Kernel with GPT-4 and plugins"""
    # Create kernel
    kernel = Kernel()
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OPENAI_API_KEY not found. Please set it in your .env file.")
        st.stop()
    
    # Add OpenAI chat completion service with GPT-4
    service_id = "chat-gpt"
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id="gpt-4",
            api_key=api_key
        )
    )
    
    # Add the knowledge plugin
    kernel.add_plugin(
        KnowledgePlugin(),
        plugin_name="KnowledgePlugin"
    )
    
    return kernel, service_id


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat_history = ChatHistory()
    st.session_state.kernel, st.session_state.service_id = initialize_kernel()
    
    # Add system message to guide GPT-4
    system_message = """You are a helpful assistant for Databricks and Unity Catalog queries.

When users ask questions about Databricks, Unity Catalog, tables, schemas, data, clusters, or jobs:
- Use the get_databricks_info tool
- Pass the user's question EXACTLY as they asked it (natural language)
- DO NOT convert questions to SQL - Genie handles that internally
- DO NOT modify or rewrite the user's question before passing it to the tool

For example:
- User asks: "What tables are in my catalog?"
- You should call: get_databricks_info(query="What tables are in my catalog?")
- NOT: get_databricks_info(query="SELECT * FROM information_schema.tables")

Let Genie do the SQL generation and data retrieval."""
    
    st.session_state.chat_history.add_system_message(system_message)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about your Databricks environment..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to chat history
    st.session_state.chat_history.add_user_message(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Create execution settings with auto function calling
                execution_settings = st.session_state.kernel.get_prompt_execution_settings_from_service_id(
                    service_id=st.session_state.service_id
                )
                execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
                
                # Get response from kernel
                response = asyncio.run(
                    st.session_state.kernel.get_service(
                        service_id=st.session_state.service_id
                    ).get_chat_message_contents(
                        chat_history=st.session_state.chat_history,
                        settings=execution_settings,
                        kernel=st.session_state.kernel,
                        arguments=KernelArguments()
                    )
                )
                
                # Extract the assistant's message
                assistant_message = str(response[0])
                
                # Display the response
                st.markdown(assistant_message)
                
                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
                st.session_state.chat_history.add_assistant_message(assistant_message)
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# Sidebar with information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This chatbot uses:
    - **Semantic Kernel** for orchestration
    - **GPT-4** for reasoning
    - **Databricks Genie** for data insights
    
    The bot has access to your Databricks environment through Genie APIs.
    """)
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.chat_history = ChatHistory()
        st.rerun()
    
    st.header("Configuration")
    st.markdown(f"""
    - **Model**: GPT-4
    - **Plugins**: {len(st.session_state.kernel.plugins)} loaded
    - **Messages**: {len(st.session_state.messages)}
    """)

