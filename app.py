from dotenv import load_dotenv
import os
import streamlit as st

from moderator.chatbot.chatbot import run_chatbot

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


# Header of app
st.header("NUS-MODerator")
st.markdown("Welcome to the chat zone! Feel free to ask me anything about courses in NUS!")

# Initialise chat history in session state, if we have not done so
if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = list()

# Display chat messages from history, when app is rerun
for message in st.session_state["conversation_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialise chatbox
prompt = st.chat_input(placeholder="Chat with NUS-MODerator!")

# Process the prompt that is submitted in chatbox
if prompt:
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