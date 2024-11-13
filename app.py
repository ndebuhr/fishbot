import os

import markdown
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

DATASTORE_STATIC_HOST = os.getenv("DATASTORE_STATIC_HOST")

st.set_page_config(
    page_title="Fishbot",
    page_icon="🎣",
    layout="wide"
)
st.title('Fishbot')

def html_response_with_sources(response):
    """Mark up the response text as HTML, including simple numbered citations."""
    text = response.text
    metadata = response.candidates[0].grounding_metadata

    # Track sources in order of first appearance
    sources = []
    source_numbers = {}

    # First pass: collect sources in order of appearance
    for support in metadata.grounding_supports:
        chunk_idx = support.grounding_chunk_indices[0]
        source = metadata.grounding_chunks[chunk_idx].retrieved_context

        if source.title not in source_numbers:
            source_numbers[source.title] = len(sources) + 1
            sources.append(source)

    # Sort supports by start index in reverse order to avoid position shifts
    supports = sorted(
        metadata.grounding_supports,
        key=lambda x: x.segment.start_index if hasattr(x.segment, 'start_index') else 0,
        reverse=True
    )

    # Second pass: insert citations
    for support in supports:
        chunk_idx = support.grounding_chunk_indices[0]
        source = metadata.grounding_chunks[chunk_idx].retrieved_context
        citation_number = source_numbers[source.title]

        start = support.segment.start_index if hasattr(support.segment, 'start_index') else 0
        end = support.segment.end_index
        supported_text = support.segment.text

        citation = f"{supported_text}<sup>[{citation_number}]</sup>"
        text = text[:start] + citation + text[end:]

    # Convert markdown to HTML
    # Not sure if the markdown will ever use advanced "extra" features, but it's enabled just in case
    md = markdown.Markdown(extensions=['extra'])
    html_content = md.convert(text)

    # Add source list at the bottom
    source_text = "<p>"
    if sources:
        for i, source in enumerate(sources, 1):
            filename = source.uri.split('/')[-1]
            source_text += f'<a href="{DATASTORE_STATIC_HOST}/{filename}" target="_blank">[{i}] {source.title}</a><br>'
    source_text += "</p>"

    return f"{html_content}{source_text}"

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.html(message["content"])

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
    html_response = html_response_with_sources(response)
    st.html(html_response)
    st.session_state.messages.append({"role": "assistant", "content": html_response})

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