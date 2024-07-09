import os
import requests
import concurrent.futures
import random
import string
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(message)s"
)


def generate_request_id(length=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def send_request(user_id):
    request_id = generate_request_id()
    start_time = time.time()
    try:
        response = requests.get(f"http://frontend:5000/request/{user_id}/{request_id}")
        end_time = time.time()
        total_duration = (end_time - start_time) * 1000  # in milliseconds

        if response.status_code == 200:
            json_response = response.json()
            hops_info = json_response.get("hops", [])
            hops_str = ", ".join(
                [
                    # f'{list(hop.keys())[0]} ({list(hop.values())[0]["duration"] * 1000:.2f} ms)'
                    f'{list(hop.values())[0]["service_name"]} ({list(hop.values())[0]["duration"] * 1000:.2f} ms)'
                    for hop in hops_info
                ]
            )
            logging.info(
                f"User {user_id}, Request {request_id}, {hops_str}, total duration {total_duration:.2f} ms"
            )
        else:
            logging.error(
                f"User {user_id}, Request {request_id}, failed with status code {response.status_code}"
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"User {user_id}, Request {request_id}, error: {e}")


def wait_for_server():
    retries = 10
    while retries > 0:
        try:
            response = requests.get("http://frontend:5000/ping")
            if response.status_code == 200 and response.text == "pong":
                logging.info("Server is up and running.")
                return True
        except requests.exceptions.RequestException as e:
            logging.warning(f"Ping failed, retrying... {retries} retries left.")
        retries -= 1
        time.sleep(10)
    logging.error("Server did not become available in time.")
    return False


if __name__ == "__main__":
    MAX_USER = int(os.environ.get("MAX_USER", 5))
    logging.info("Starting client...")
    if wait_for_server():
        logging.info("Server is ready. Starting requests...")
        while True:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_USER) as executor:
                futures = [executor.submit(send_request, i) for i in range(MAX_USER)]
                concurrent.futures.wait(futures)
            time.sleep(
                10
            )  # wait for 10 seconds before sending the next batch of requests
    else:
        logging.error("Exiting client due to server unavailability.")
