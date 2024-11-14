import datetime
import os

from google.auth import default
from google.cloud import bigquery

client = bigquery.Client()
credentials, project_id = default()

DATASET = os.getenv("REPORTING_DATASET")
TABLE = os.getenv("REPORTING_TABLE")

SCHEMA = [
    bigquery.SchemaField("timestamp", "TIMESTAMP"),
    bigquery.SchemaField("session_id", "STRING"),
    bigquery.SchemaField("prompt", "STRING"),
    bigquery.SchemaField("response", "STRING"),
    bigquery.SchemaField("image", "STRUCT", fields=[
        bigquery.SchemaField("src", "STRING"),
        bigquery.SchemaField("alt", "STRING")
    ]),
]

def log_to_bigquery(session_id, prompt, response, image_result=None):
    """Log interaction data to BigQuery."""
    table_ref = f"{project_id}.{DATASET}.{TABLE}"

    # Create the table if it does not exist
    table = bigquery.Table(table_ref, schema=SCHEMA)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.MONTH,
        field="timestamp"
    )
    client.create_table(table, exists_ok=True)

    row = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "session_id": session_id,
        "prompt": prompt,
        "response": response,
        "image": {
            "src": image_result.get("src").get("original") if image_result else None,
            "alt": image_result.get("alt") if image_result else None
        }
    }

    errors = client.insert_rows_json(table_ref, [row])