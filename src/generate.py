import base64
import os
import vertexai

from google.auth import default
from vertexai.preview.generative_models import GenerativeModel, Tool
from vertexai.preview.generative_models import grounding

DATASTORE_LOCATION = os.getenv("DATASTORE_LOCATION")
DATASTORE_ID = os.getenv("DATASTORE_ID")

credentials, project_id = default()

CUSTOM_TOOLS = [
    Tool.from_retrieval(
        retrieval=grounding.Retrieval(
            source=grounding.VertexAISearch(datastore=f"projects/{project_id}/locations/{DATASTORE_LOCATION}/collections/default_collection/dataStores/{DATASTORE_ID}"),
        )
    ),
]

GOOGLE_TOOLS = [
    Tool.from_google_search_retrieval(
        google_search_retrieval=grounding.GoogleSearchRetrieval()
    ),
]

GENERATION_CONFIG = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

vertexai.init()
custom_model = GenerativeModel(
    "gemini-1.5-flash-002",
    tools=CUSTOM_TOOLS,
)
google_search_model = GenerativeModel(
    "gemini-1.5-flash-002",
    tools=GOOGLE_TOOLS,
)
generic_model = GenerativeModel(
    "gemini-1.5-flash-002",
)
chat = custom_model.start_chat()

def multiturn_generate(prompt):
    return chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )

def singleturn_generate(prompt):
    singleturn_chat = custom_model.start_chat()
    return singleturn_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )

def google_search_generate(prompt):
    google_search_chat = google_search_model.start_chat()
    return google_search_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )

def generic_generate(prompt):
    generic_chat = generic_model.start_chat()
    return generic_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )