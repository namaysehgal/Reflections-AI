# import streamlit as st
# from snowflake.core import Root
# from snowflake.cortex import Complete
# from snowflake.snowpark.context import get_active_session
import streamlit as st
from snowflake.core import Root
from snowflake.cortex import Complete
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
import configparser
# Initialize session and root
# session = get_active_session()
# root = Root(session)

MODELS = ["mistral-large2"]
def create_session():
    """Create a Snowflake session using configuration details."""
    config = configparser.ConfigParser()
    config.read('properties.ini')
    snowflake_config = config['Snowflake']

    connection_params = {key: snowflake_config.get(key) for key in
                         ['account', 'user', 'password', 'role', 'warehouse', 'database', 'schema']}
    session = Session.builder.configs(connection_params).create()
    return session

session = create_session()
root = Root(session)
# Enhanced page config
st.set_page_config(
    page_title="ReflectionsAI",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Updated purple theme CSS
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f0ff 0%, #e0d0ff 100%);
    }
    .main {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(128, 0, 255, 0.1);
    }
    .stButton>button {
        background: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(128, 0, 255, 0.2);
    }
    .stTextArea>div>div>textarea {
        border-radius: 0.5rem;
        border: 2px solid #e0d0ff;
    }
    .stTextArea>div>div>textarea:focus {
        border-color: #9c27b0;
        box-shadow: 0 0 0 2px rgba(156, 39, 176, 0.2);
    }
    .css-1d391kg {
        background: linear-gradient(135deg, #9c27b0 0%, #673ab7 100%);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f5f0ff;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        color: #673ab7;
    }
    .stTabs [aria-selected="true"] {
        background-color: #9c27b0;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def init_messages():
    if st.session_state.clear_conversation or "messages" not in st.session_state:
        st.session_state.messages = []

def init_service_metadata():
    """
    Initialize the session state for cortex search service metadata. 
    Query the available cortex search services from the Snowflake session 
    and store their names and search columns in the session state.
    """
    # Check if service metadata is already initialized in session state
    if "service_metadata" not in st.session_state:
        # Run the SQL query to fetch available Cortex search services
        services = session.sql("SHOW CORTEX SEARCH SERVICES;").collect()

        # Initialize an empty list to store service metadata
        service_metadata = []

        # Check if services were found
        if services:
            # Loop through each service and fetch its search column
            for s in services:
                svc_name = s["name"]
                try:
                    # Query the search column for the current service
                    svc_search_col = session.sql(f"DESC CORTEX SEARCH SERVICE {svc_name};").collect()
                    if svc_search_col:
                        svc_search_col = svc_search_col[0]["search_column"]
                    else:
                        st.warning(f"No search column found for service {svc_name}")
                        continue
                    # Append service metadata to the list
                    service_metadata.append({"name": svc_name, "search_column": svc_search_col})

                except Exception as e:
                    st.error(f"Error while fetching metadata for service {svc_name}: {e}")

        # Store the metadata in session state for later use
        st.session_state.service_metadata = service_metadata

        # If no services found, show an appropriate message
        if not service_metadata:
            st.error("No Cortex search services found in Snowflake.")


def init_config_options():
    st.sidebar.selectbox(
        "Select cortex search service:",
        [s["name"] for s in st.session_state.service_metadata],
        key="selected_cortex_search_service",
    )

    st.sidebar.button("Clear conversation", key="clear_conversation")
    st.sidebar.toggle("Debug", key="debug", value=False)
    st.sidebar.toggle("Use chat history", key="use_chat_history", value=True)

    with st.sidebar.expander("Advanced options"):
        st.selectbox("Select model:", MODELS, key="model_name")
        st.number_input(
            "Select number of context chunks",
            value=500,
            key="num_retrieved_chunks",
            min_value=1,
            max_value=500,
        )
        st.number_input(
            "Select number of messages to use in chat history",
            value=50,
            key="num_chat_messages",
            min_value=1,
            max_value=50,
        )

    st.sidebar.expander("Session State").write(st.session_state)

def query_journal_cortex_service(query, columns=[], filter={}):
    """
    Query the journal cortex search service with the given query and retrieve context documents.
    Display the retrieved context documents in the sidebar if debug mode is enabled. Return the
    context documents as a string.

    Args:
        query (str): The query to search the journal cortex search service with.
        columns (list): The columns to query in the search service (default is an empty list).
        filter (dict): The filter conditions for the search (default is an empty dictionary).

    Returns:
        tuple: A concatenated string of context documents and the results as a list.
    """
    # Get the active database and schema
    db, schema = session.get_current_database(), session.get_current_schema()

    # Retrieve the journal Cortex search service
    cortex_search_service = (
        root.databases[db]
        .schemas[schema]
        .cortex_search_services["journal_service"]  # Use the name of your journal service
    )

    # Perform the search in the journal cortex search service
    context_documents = cortex_search_service.search(
        query, columns=columns, filter=filter, limit=st.session_state.num_retrieved_chunks
    )
    results = context_documents.results

    # Concatenate the context documents into a single string
    context_str = ""
    for i, r in enumerate(results):
        context_str += f"Context document {i+1}: {r['chunk']} \n" + "\n"

    # If debug mode is enabled, show the context documents in the sidebar
    if st.session_state.debug:
        st.sidebar.text_area("Context documents", context_str, height=500)

    return context_str, results


def get_chat_history():
    """
    Retrieve the chat history from the session state, limited to the number of messages specified
    by the user in the sidebar options (using the num_chat_messages setting).

    Returns:
        list: The list of chat messages from the session state.
    """
    # Determine the start index based on the number of messages specified in the sidebar options
    start_index = max(
        0, len(st.session_state.messages) - st.session_state.num_chat_messages
    )
    # Return the limited list of chat messages
    return st.session_state.messages[start_index:]

def complete(session, model, prompt):
    """
    Generate a completion for the given prompt using the specified model.

    Args:
        model (str): The name of the model to use for completion.
        prompt (str): The prompt to generate a completion for.

    Returns:
        str: The generated completion for the journal app's context.
    """
    # Generate completion using the provided model and prompt, handling special characters like "$"
    response = Complete(model, prompt, session = session).replace("$", "\$")
    
    # If you need further customization or formatting (like adding references or other elements), 
    # you can modify the returned response here.
    return response


def make_chat_history_summary(chat_history, question):
    """
    Generate a summary of the chat history combined with the current question to extend the query
    context. Use the language model to generate this summary.

    Args:
        chat_history (str): The chat history to include in the summary.
        question (str): The current user question to extend with the chat history.

    Returns:
        str: The generated summary of the chat history and question for the journal app's context.
    """
    prompt = f"""
        [INST]
        Based on the chat history below and the question, generate a query that extends the question
        with the chat history provided. The query should be in natural language.
        Answer with only the query. Do not add any explanation.

        <chat_history>
        {chat_history}
        </chat_history>
        <question>
        {question}
        </question>
        [/INST]
    """

    # Generate the summary using the selected model
    summary = complete(session, st.session_state.model_name, prompt)

    # If debug mode is enabled, display the summary in the sidebar for review
    if st.session_state.debug:
        st.sidebar.text_area(
            "Chat history summary", summary.replace("$", "\$"), height=150
        )

    return summary
def write_journal_entry():
    """
    Function to allow users to write their own journal entries
    and store them in a Snowflake table for future use.
    """
    st.subheader("Write Your Journal Entry")

    # Input for the journal entry
    journal_entry = st.text_area("Write your thoughts here...", height=300)

    # Optional title for the entry
    journal_title = st.text_input("page number for your entry:")

    # Button to save the entry
    if st.button("Save Journal Entry"):
        if journal_entry.strip() == "":
            st.warning("Journal entry cannot be empty!")
        else:
            # Insert the entry into a Snowflake table
            try:
                # Get the current date and time
                timestamp = session.sql("SELECT CURRENT_TIMESTAMP;").collect()[0][0]
                chunk_size = 1000  # You can define your chunk size
                chunks = [journal_entry[i:i+chunk_size] for i in range(0, len(journal_entry), chunk_size)]

                for chunk in chunks:
                    session.sql(
                        f"""
                        INSERT INTO JOURNAL_DB.PUBLIC.JOURNAL_CHUNKS_TABLE(id, chunk, created_at)
                        VALUES (?, ?, ?)
                        """,
                        [journal_title, chunk, timestamp]
                    ).collect()


                # Insert the data into the Snowflake table
                session.sql(
                    f"""
                    INSERT INTO journal_entries (title, entry, created_at)
                    VALUES (?, ?, ?)
                    """,
                    [journal_title, journal_entry, timestamp],
                ).collect()

                st.success("Your journal entry has been saved successfully!, Memories will be updated within 1 minute!")
            except Exception as e:
                st.error(f"An error occurred while saving your journal entry: {e}")



def create_prompt(user_question):
    """
    Create a prompt for the language model by combining the user question with context retrieved
    from the journal cortex search service and chat history (if enabled). Format the prompt according to
    the expected input format of the model for the journaling app.

    Args:
        user_question (str): The user's question to generate a prompt for.

    Returns:
        tuple: The generated prompt for the language model and the search results.
    """
    if st.session_state.use_chat_history:
        chat_history = get_chat_history()
        if chat_history != []:
            # If there is chat history, summarize it with the current question
            question_summary = make_chat_history_summary(chat_history, user_question)
            prompt_context, results = query_journal_cortex_service(
                question_summary,
                columns=["chunk"]
            )
        else:
            # If no chat history, query directly based on the user question
            prompt_context, results = query_journal_cortex_service(
                user_question,
                columns=["chunk"]
            )
    else:
        # If chat history is not used, query directly based on the user question
        prompt_context, results = query_journal_cortex_service(
            user_question,
            columns=["chunk"]
            
        )
        chat_history = ""  # Empty chat history if not using it

    # Format the context to include timestamps
    formatted_context = ""
    for i, result in enumerate(results):
        created_at = result.get("created_at", "Unknown timestamp")
        chunk = result.get("chunk", "")
        formatted_context += f"Document {i+1} (Created At: {created_at}):\n{chunk}\n\n"

    # Format the final prompt for the language model
    prompt = f"""
    [INST]
    You are a helpful AI assistant for a journaling application. When a user asks a question,
    you will also be given context provided between <context> and </context> tags. Use that context
    with the user's chat history provided between <chat_history> and </chat_history> tags
    to provide a meaningful response that answers the user's question. Ensure your response is relevant,
    empathetic, and concise. If the answer cannot be derived from the provided information, politely inform
    the user that the information is not available.

    If the user's question is too generic or cannot be answered with the given context or chat_history,
    respond with "Sorry, I don't know the answer to that."

    <chat_history>
    {chat_history}
    </chat_history>
    <context>
    {prompt_context}
    </context>
    <question>
    {user_question}
    </question>
    [/INST]
    Answer:
    """
    return prompt, results 


def home_page():
    """
    New function to display the home page
    """
    st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='color: #9c27b0; margin-bottom: 2rem;'>✨Welcome to ReflectionsAI✨</h1>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='background: rgba(156, 39, 176, 0.1); padding: 1.5rem; border-radius: 1rem; height: 200px; text-align: center;'>
                <h3 style='color: #9c27b0;'>✍ Write</h3>
                <p>Express your thoughts, feelings, and experiences in your personal digital space.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='background: rgba(156, 39, 176, 0.1); padding: 1.5rem; border-radius: 1rem; height: 200px; text-align: center;'>
                <h3 style='color: #9c27b0;'>💭 Reflect</h3>
                <p>Review past entries and track your personal growth journey.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='background: rgba(156, 39, 176, 0.1); padding: 1.5rem; border-radius: 1rem; height: 200px; text-align: center;'>
                <h3 style='color: #9c27b0;'>🤖 Chat</h3>
                <p>Interact with your journal using our AI assistant for deeper insights.</p>
            </div>
        """, unsafe_allow_html=True)

def main():
    """
    Enhanced main function with better UI and navigation
    """
    # Initialize everything as before
    init_service_metadata()
    init_config_options()
    init_messages()
    
    # Enhanced navigation with Home page
    tabs = st.tabs(["🏠 Home", "✍ Write Entry", "💬 Chat"])
    
    with tabs[0]:
        home_page()
    
    with tabs[1]:
        write_journal_entry()
    
    with tabs[2]:
        # Your original chat interface with updated styling
        icons = {"assistant": "💜", "user": "👤"}
        
        # Display existing chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=icons[message["role"]]):
                st.markdown(message["content"])

        # Chat input logic remains the same
        disable_chat = (
            "service_metadata" not in st.session_state
            or len(st.session_state.service_metadata) == 0
        )

        if question := st.chat_input("Ask about your journal...", disabled=disable_chat):
            st.session_state.messages.append({"role": "user", "content": question})
            
            with st.chat_message("user", avatar=icons["user"]):
                st.markdown(question.replace("$", "\$"))

            with st.chat_message("assistant", avatar=icons["assistant"]):
                message_placeholder = st.empty()
                question = question.replace("'", "")
                prompt, results = create_prompt(question)

                with st.spinner("Thinking..."):
                    generated_response = complete(session,
                        st.session_state.model_name, prompt
                    )
                    message_placeholder.markdown(generated_response + "\n\n")

            st.session_state.messages.append(
                {"role": "assistant", "content": generated_response}
            )

if __name__ == "__main__":
    # session = get_active_session()
    # root = Root(session)
    main()
