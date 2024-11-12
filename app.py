import streamlit as st

from generate import generic_generate, multiturn_generate, singleturn_generate
from pexels import top_pexels_result

IMAGE_CHECK_PROMPT = """
Would an image be very helpful in answering this question? Answer only "yes" or "no".

Question:
{}

Answer:
{}
"""

IMAGE_QUERY_PROMPT = """
What search term should be used to find an image related to this question/answer? Return only the single search term.

Question:
{}

Answer:
{}
"""

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
                # If the response is grounded, we can break out of the loop
                if len(response.candidates[0].grounding_metadata.grounding_supports) > 0:
                    break

    # Add assistant response to chat history
    st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})

    # Check if the response could use an image
    if "yes" in generic_generate(IMAGE_CHECK_PROMPT.format(prompt, response.text)).text.lower():
        # Search for an image related to the user's question
        query = generic_generate(IMAGE_QUERY_PROMPT.format(prompt, response.text)).text
        top_result = top_pexels_result(query)
        st.image(top_result["src"]["original"], caption=top_result["alt"])

# Add a button to clear chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# Display current chat state in sidebar for debugging (optional)
with st.sidebar:
    st.subheader("Debug Info")
    st.write("Current chat state:")
    st.json(st.session_state.messages)