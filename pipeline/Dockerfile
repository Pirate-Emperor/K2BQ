FROM apache/beam_python3.12_sdk:latest
# Install confluent-kafka and other dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

