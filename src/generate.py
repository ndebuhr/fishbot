import base64
import os
import vertexai
import redis
from datetime import datetime
from functools import wraps

from google.auth import default
from vertexai.preview.generative_models import GenerativeModel, Tool
from vertexai.preview.generative_models import grounding


DATASTORE_LOCATION = os.getenv("DATASTORE_LOCATION")
DATASTORE_ID = os.getenv("DATASTORE_ID")
REDIS_URL = os.getenv("REDIS_URL")
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

class RateLimiter:
    def __init__(self, redis_url):
        self.redis_client = redis.from_url(redis_url)

    def check_rate_limit(self, key, max_requests, time_window):
        """Check if the request should be rate limited (rejected)"""

        current_time = datetime.utcnow().timestamp()
        window_start = current_time - time_window

        pipeline = self.redis_client.pipeline()
        # Remove old requests
        pipeline.zremrangebyscore(key, 0, window_start)
        # Add current request
        pipeline.zadd(key, {str(current_time): current_time})
        # Count requests in window
        pipeline.zcount(key, window_start, current_time)
        # Set key expiration
        pipeline.expire(key, time_window)

        _, _, request_count, _ = pipeline.execute()

        return request_count <= max_requests

def rate_limit(max_requests, time_window):
    """Decorator for rate limiting"""
    def decorator(func):
        limiter = RateLimiter(REDIS_URL)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate rate limit key based on the function name
            key = f"rate_limit:{func.__name__}"

            if not limiter.check_rate_limit(key, max_requests, time_window):
                raise Exception(f"Rate limit exceeded. Maximum {max_requests} requests per {time_window} seconds.")

            return func(*args, **kwargs)
        return wrapper
    return decorator


vertexai.init()
custom_model = GenerativeModel("gemini-1.5-flash-002", tools=CUSTOM_TOOLS)
google_search_model = GenerativeModel("gemini-1.5-flash-002", tools=GOOGLE_TOOLS)
generic_model = GenerativeModel("gemini-1.5-flash-002")
chat = custom_model.start_chat()

@rate_limit(max_requests=10, time_window=60)
def multiturn_generate(prompt):
    return chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )

@rate_limit(max_requests=10, time_window=60)
def singleturn_generate(prompt):
    singleturn_chat = custom_model.start_chat()
    return singleturn_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )

@rate_limit(max_requests=10, time_window=60)
def google_search_generate(prompt):
    google_search_chat = google_search_model.start_chat()
    return google_search_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )

# Use a higher limit than other generate functions, because of image-check calls
@rate_limit(max_requests=30, time_window=60)
def generic_generate(prompt):
    generic_chat = generic_model.start_chat()
    return generic_chat.send_message(
        [prompt],
        generation_config=GENERATION_CONFIG
    )