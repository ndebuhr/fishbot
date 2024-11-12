import base64
import os
import vertexai

from google.auth import default
from vertexai.preview.generative_models import GenerativeModel, SafetySetting, Tool
from vertexai.preview.generative_models import grounding

DATASTORE_LOCATION = os.getenv("DATASTORE_LOCATION")
DATASTORE_ID = os.getenv("DATASTORE_ID")

credentials, project_id = default()

TOOLS = [
    Tool.from_retrieval(
        retrieval=grounding.Retrieval(
            source=grounding.VertexAISearch(datastore=f"projects/{project_id}/locations/{DATASTORE_LOCATION}/collections/default_collection/dataStores/{DATASTORE_ID}"),
        )
    ),
]

GENERATION_CONFIG = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
}

SAFETY_SETTINGS = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]

vertexai.init()
model = GenerativeModel(
    "gemini-1.5-flash-002",
    tools=TOOLS,
)
generic_model = GenerativeModel(
    "gemini-1.5-flash-002",
)
chat = model.start_chat()

def multiturn_generate(prompt):
    return chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )

def singleturn_generate(prompt):
    singleturn_chat = model.start_chat()
    return singleturn_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )

def generic_generate(prompt):
    generic_chat = generic_model.start_chat()
    return generic_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )