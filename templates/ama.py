from dotenv import load_dotenv
from moderator.chatbot.chatbot import run_chatbot
import os
import streamlit as st

load_dotenv()

def format_moderator_response(generated_response: dict[str, str]):
    # Get raw answer of chatbot
    moderator_answer = generated_response["answer"]

    # Get sources
    documents_retrieved = generated_response["source_documents"]

    # Get unique module names used in reference, as well as its corresponding NUSMods link
    module_names_to_links_referred = {
        document.metadata["module_name"]: document.metadata["module_link"] for document in documents_retrieved
    }

    # Format reference using HTML list elements
    formatted_references = [
        f'<li><a href="{module_link_referred}">{module_name_referred}</a></li>' for module_name_referred, module_link_referred in module_names_to_links_referred.items()
    ]

    # Combine list elements into ordered list and add final formatting
    formatted_response = f'{moderator_answer}\n\n**Sources:**\n<ol>{"".join(formatted_references)}</ol>'

    return formatted_response


# Display header and introduction
st.header("AMA")
st.markdown("Ask NUS-MODerator anything about the courses in NUS!")

# Initialise chat history in session state, if we have not done so
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = list()

# Initialise formatted moderator responses in session state, if we have not done so
if "formatted_responses" not in st.session_state:
    st.session_state["formatted_responses"] = list()

# Display chat messages from history, when app is rerun
message_display = st.container(height=250)
with message_display:
    for i, message in enumerate(st.session_state["conversation_history"]):
        role = message["role"]
        with st.chat_message(role):
            if role == "user":
                # Get user message directly from the content key
                display_message = message["content"]
            
            else:
                # For moderator message, we want the formatted response. Get from session state
                index_in_formatted_responses = i // 2       # User always messages first
                display_message = st.session_state["formatted_responses"][index_in_formatted_responses]
            
            st.markdown(display_message, unsafe_allow_html=True)
        
# Initialise chatbox
prompt = st.chat_input(placeholder="Chat with NUS-MODerator!")

# Process the prompt that is submitted
if prompt:
    with message_display:
        # Display user's prompt
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Generating response..."):
            # Get response from chatbot and format it
            generated_response = run_chatbot(query=prompt, chat_history=st.session_state["conversation_history"])
            formatted_response = format_moderator_response(generated_response=generated_response)

        # Display moderator's response
        with st.chat_message("assistant"):
            st.markdown(formatted_response, unsafe_allow_html=True)

        # Update chat history in session state
        st.session_state["conversation_history"].append({
            "role": "user",
            "content": prompt
        })
        st.session_state["conversation_history"].append({
            "role": "assistant",
            "content": generated_response["answer"]
        })

        # Update formatted moderator responses in session state
        st.session_state["formatted_responses"].append(formatted_response)