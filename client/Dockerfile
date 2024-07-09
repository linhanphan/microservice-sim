# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Requests
RUN pip install requests

# Run client.py when the container launches
CMD ["python", "client.py"]
