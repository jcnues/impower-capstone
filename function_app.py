"""
Made by John Nuestro
"""

import logging
import json
from datetime import timedelta, datetime
import os

import requests
import azure.functions as func
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 0 12 * * *", arg_name="myTimer", run_on_startup=False, use_monitor=True
)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    """
    Timer trigger to grab NASA APOD on a daily basis at 10am and
    move it to a Azure storage container

    Args:
        myTimer (func.TimerRequest): timer for running the function
    """
    logging.info("Getting NASA APOD")

    # Get payload from NASA API
    # initialize params
    params = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "api_key": os.getenv("NASA_APOD_API_KEY"),
    }
    # Initialize the URL to call via api
    url = os.getenv("NASA_APOD_API_URL")
    # Run a get request and conver the repsonse to json
    apod_payload = requests.get(url=url, params=params, timeout=30).json()

    logging.info("Dumping payload to temp file.")

    # Initialize the output filename
    output_file = "/tmp/data.json"

    # Write the JSON to a file
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(apod_payload, file, indent=4)

    current_datetime = datetime.now()
    previous_datetime = current_datetime - timedelta(days=1)

    # Initialize variables
    your_name = "JohnNuestro"
    connection_string = os.getenv("AZURE_STORAGE_ACCOUNT_CONN_STR")
    blob_name = f"{previous_datetime.strftime('%m%d%Y')}{your_name}Data.json"
    container_name = os.getenv("CONTAINER_NAME")

    logging.info(
        f"Moving data from temp file into azure storage container: {container_name}"
    )

    # Upload the file to the blob storage
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    with open(output_file, "rb") as data:
        container_client.upload_blob(blob_name, data)
        
    logging.info(f"NASA APOD successfully stored into azure storage container: {container_name}")

    if myTimer.past_due:
        logging.info("The timer is past due!")

    logging.info("Python timer trigger function executed.")
