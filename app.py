from generate import generic_generate, multiturn_generate, singleturn_generate
import streamlit as st

st.title('Tiered LLM Chat Interface')

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("How can I help you?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Try different generation strategies in sequence
            # Since the multiturn is always called, the session integrity is maintained
            generation_strategies = [
                multiturn_generate,
                singleturn_generate,
                generic_generate
            ]

            for strategy in generation_strategies:
                response = strategy(prompt)
                if "provide the sources" not in response.text:
                    break

    # Add assistant response to chat history
    st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})

# Add a button to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Display current chat state in sidebar for debugging (optional)
with st.sidebar:
    st.subheader("Debug Info")
    st.write("Current chat state:")
    st.json(st.session_state.messages)