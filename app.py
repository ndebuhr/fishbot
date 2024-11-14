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

SUGGESTED_QUESTIONS = [
    "What does a Rainbow Trout look like?",
    "What is a fly reel and what is it made of?",
    "Is a fishing license required in Texas?"
]

DATASTORE_STATIC_HOST = os.getenv("DATASTORE_STATIC_HOST")

def format_html_response_with_sources(response):
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

def generate_response(prompt):
    """Generate a response and handle images for a given prompt."""
    # Generate AI response
    generation_strategies = [
        multiturn_generate,
        singleturn_generate,
        generic_generate
    ]

    for strategy in generation_strategies:
        response = strategy(prompt)
        if len(response.candidates[0].grounding_metadata.grounding_supports) > 0:
            break

    # Format response as HTML
    html_response = format_html_response_with_sources(response)

    # Check if the response could use an image
    if "yes" in generic_generate(IMAGE_CHECK_PROMPT.format(prompt, response.text)).text.lower():
        query = generic_generate(IMAGE_QUERY_PROMPT.format(prompt, response.text)).text
        top_result = top_pexels_result(query)
        return html_response, top_result

    return html_response, None

def submit_prompt(prompt):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "image": None
    })

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            html_response, image_result = generate_response(prompt)

    st.session_state.messages.append({
        "role": "assistant",
        "content": html_response,
        "image": {
            "src": image_result["src"]["original"],
            "alt": image_result["alt"]
        } if image_result else None
    })

    st.rerun()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Fishbot",
        page_icon="🎣",
        layout="wide"
    )
    st.title('Fishbot')

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suggested questions
    st.write("Get started with some suggested questions:")
    cols = st.columns(3)
    for i, question in enumerate(SUGGESTED_QUESTIONS):
        col_idx = i % 3
        # Disable suggested questions if a prompt has been submitted
        if cols[col_idx].button(
            question,
            key=f"suggested_{i}",
            disabled=len(st.session_state.messages) > 0,
        ):
            submit_prompt(question)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                st.html(message["content"])
            if message["image"]:
                st.image(message["image"]["src"], caption=message["image"]["alt"])

    # Handle user input
    if prompt := st.chat_input("How can I help you?"):
        submit_prompt(prompt)

    # Clear chat history button
    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    # Debug info
    with st.sidebar:
        st.subheader("Debug Info")
        st.write("Current chat state:")
        st.json(st.session_state.messages)