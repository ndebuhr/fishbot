# Fishbot 🎣

## Feature Highlights

* Dynamic search and rendering for answer-supporting images
* A tiered LLM approach, based on grounding supports relevancy (all Gemini-based):
    1. Multi-turn custom grounded responses (most preferred)
    2. Single-turn custom grounded responses
    3. Single-turn Google Search grounded responses
    4. Ungrounded responses (least preferred)
* Custom grounding citations rendering
* EDW reporting on sessions, prompts, and responses

## Usage

| Environment Variable | Description |
|----------------------|-------------|
| DATASTORE_LOCATION | Location of the Vertex AI Agent Builder data store for custom grounding (e.g., "global") |
| DATASTORE_ID | ID of the Vertex AI Agent Builder data store for custom grounding (e.g., "fishbot-123") |
| DATASTORE_STATIC_HOST | Protocol and host for the file server containing the custom grounding sources (e.g., "https://example.com") |
| PEXELS_API_KEY | API key from pexels.com, for use in dynamic image rendering |
| REPORTING_DATASET | BigQuery dataset for storing usage reporting data (e.g., "fishbot_reporting") |
| REPORTING_TABLE | BigQuery table for storing usage reporting data, which will be created if it does not already exist (e.g., "responses") |

## Infrastructure

The infrastructure for [fishbot.com](https://fishbot.com) includes:
1. A Cloud Run service with "internal + load balancer" ingress
1. An External Global Application Load Balancer spanning both the chatbot and static files (custom grounding source)
    1. Serverless Network Endpoint backend for the Cloud Run service
    1. Public backend bucket for the static files
1. Vertex AI Agent Builder search app and data store, built over the static files bucket, for grounding
1. Cloud Armor backend policy, including:
    1. Select US sanctioned country blocking: Russia, Iran, Cuba, North Korea, Syria, and Belarus
    1. OWASP ModSecurity CRS 3.3 scanner protection
    1. Rate-based 30-minute ban for exceeding 60 requests/minute
        * Enforcement key is the concatenation of IP address and HTTP path
1. BigQuery dataset for prompt-response usage reporting