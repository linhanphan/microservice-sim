from flask import Flask, request, jsonify
import requests
import os
import random
import time
import socket

app = Flask(__name__)

# List of all backend service names
BACKEND_SERVICE_NAMES = [
    "backend1",
    "backend2",
    "backend3",
    "backend4",
    "backend5",
    "backend6",
    "backend7",
    "backend8",
    "backend9",
    "backend10",
]

service_ip = socket.gethostbyname(socket.gethostname())
MAX_HOPS = int(os.environ.get("MAX_HOPS", 5))
SERVICE_NAME = os.environ.get("SERVICE_NAME", service_ip)

@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


@app.route("/request/<userID>/<requestID>", methods=["GET"])
def handle_get(userID, requestID):
    json_data = {"userID": userID, "requestID": requestID, "hops": []}
    receive_timestamp = time.time()
    time.sleep(random.uniform(0, 0.005))  # Random wait between 0-5 ms
    # Add receive timestamp and service IP
    json_data["hops"].append(
        {
            service_ip: {
                "service_name": SERVICE_NAME,
                "receive_timestamp": receive_timestamp,
            }
        }
    )
    backend_service = f"http://{random.choice(BACKEND_SERVICE_NAMES)}:5000/request"
    try:
        response = requests.post(backend_service, json=json_data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_json = response.json()  # Attempt to parse the response as JSON
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error contacting backend service {backend_service}: {e}")
        return jsonify({"error": "Backend service error"}), 500
    except ValueError:
        app.logger.error(
            f"Invalid JSON response from backend service {backend_service}: {response.text}"
        )
        return jsonify({"error": "Invalid JSON response"}), 500
    # print(response_json)
    response_timestamp = time.time()
    duration = response_timestamp - receive_timestamp

    # Update the first hop with response timestamp and duration if no more forwarding
    response_json["hops"][0][service_ip].update(
        {"response_timestamp": response_timestamp, "duration": duration}
    )
    return jsonify(response_json)


@app.route("/request", methods=["POST"])
def handle_post():
    json_data = request.get_json()
    receive_timestamp = time.time()
    time.sleep(random.uniform(0, 0.005))  # Random wait between 0-5 ms

    # Add receive timestamp and service IP
    json_data["hops"].append(
        {
            service_ip: {
                "service_name": SERVICE_NAME,
                "receive_timestamp": receive_timestamp,
            }
        }
    )

    if len(json_data["hops"]) < MAX_HOPS:
        used_services = [list(hop.values())[0]["service_name"] for hop in json_data['hops']]
        remaining_services = [
            svc for svc in BACKEND_SERVICE_NAMES if svc not in used_services
        ]

        # print(used_services)
        # print(remaining_services)

        if remaining_services:
            backend_service = f"http://{random.choice(remaining_services)}:5000/request"
            try:
                response = requests.post(backend_service, json=json_data)
                response.raise_for_status()  # Raise an exception for HTTP errors
                response_json = response.json()  # Attempt to parse the response as JSON
            except requests.exceptions.RequestException as e:
                app.logger.error(
                    f"Error contacting backend service {backend_service}: {e}"
                )
                return jsonify({"error": "Backend service error"}), 500
            except ValueError:
                app.logger.error(
                    f"Invalid JSON response from backend service {backend_service}: {response.text}"
                )
                return jsonify({"error": "Invalid JSON response"}), 500

            response_timestamp = time.time()
            duration = response_timestamp - receive_timestamp

            # Find and update the current hop with response timestamp and duration
            for idx, hop in enumerate(response_json["hops"]):
                if service_ip in hop:
                    response_json["hops"][idx][service_ip].update(
                        {"response_timestamp": response_timestamp, "duration": duration}
                    )
                    break
            return jsonify(response_json)

    response_timestamp = time.time()
    duration = response_timestamp - receive_timestamp

    # Update the last hop with response timestamp and duration if no more forwarding
    json_data["hops"][-1][service_ip].update(
        {"response_timestamp": response_timestamp, "duration": duration}
    )

    return jsonify(json_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
