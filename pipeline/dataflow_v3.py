import base64
import datetime
import http.server
import json
import random
import google.auth
import google.auth.transport.urllib3
import urllib3
import functools
import time
import apache_beam as beam
from confluent_kafka import Consumer
from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions

import json

# Pipeline options
pipeline_options = PipelineOptions(
    runner='DataflowRunner',   #for Dataflow job change to runner='DataflowRunner'
    project='valid-verbena-437709-h5',
    region='us-central1',   #for Dataflow job change to 'us-west1'
    temp_location='gs://dataops-dataflow-2024/temp',
    staging_location='gs://dataops-dataflow-2024/staging',
    streaming=True,  #Enable streaming mode
    #Dataflow parameters that are optional
    job_name='streaming-kafka-bq-nifty50-v5',  #Set the Dataflow job name here
    num_workers=3,  #Specify the number of workers
    max_num_workers=10,  #Specify the maximum number of workers
    disk_size_gb=100,  #Specify the disk size in GB per worker
    autoscaling_algorithm='THROUGHPUT_BASED',  #Specify the autoscaling algorithm
    machine_type='n1-standard-4',  #Specify the machine type for the workers
    service_account_email='dataops-guru-sa@valid-verbena-437709-h5.iam.gserviceaccount.com'
)



# Define the pipeline
with beam.Pipeline(options=pipeline_options) as pipeline:

    class TokenProvider:
        def __init__(self):
            self.credentials, _ = google.auth.default()
            self.http_client = urllib3.PoolManager()

        def valid_credentials(self):
            if not self.credentials.valid:
                self.credentials.refresh(google.auth.transport.urllib3.Request(self.http_client))
            return self.credentials

        def confluent_token(self):
            creds = self.valid_credentials()
            utc_expiry = creds.expiry.replace(tzinfo=datetime.timezone.utc)
            expiry_seconds = (utc_expiry - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            return creds.token, time.time() + expiry_seconds

    def make_token(args):
        token_provider = TokenProvider()
        token, expiry_time = token_provider.confluent_token()
        return token

    kafka_cluster_name = 'dataopsguru-kafka'
    region = 'us-central1'
    project_id = 'valid-verbena-437709-h5'
    port = '9092'
    kafka_topic_name = 'dataops-kafka-topic'

    # Kafka Producer configuration with OAUTHBEARER authentication
    config = {
    'bootstrap.servers': f'bootstrap.{kafka_cluster_name}.{region}.managedkafka.{project_id}.cloud.goog:{port}',
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'OAUTHBEARER',
    'oauth_cb': make_token,
    }

    class KafkaConsumer(beam.DoFn):
        def __init__(self, kafka_config, topic):
            self.kafka_config = kafka_config
            self.topic = topic

        def setup(self):
            # Initialize Kafka consumer
            self.consumer = Consumer(self.kafka_config)
            self.consumer.subscribe([self.topic])

        def process(self, element):
            # Poll Kafka for messages
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                return
            if msg.error():
                raise Exception(f"Kafka error: {msg.error()}")

            # Decode and parse the Kafka message
            value = msg.value().decode('utf-8')
            parsed_message = json.loads(value)
            yield parsed_message

        def teardown(self):
            if self.consumer:
                self.consumer.close()

    PROJECT_ID = 'valid-verbena-437709-h5'
    DATASET_ID = 'nifty50'
    TABLE_ID = 'nifty50_historical_data_65'

    table_schema = {
    'fields': [
        {'name': 'symbol', 'type': 'STRING'},
        {'name': 'date', 'type': 'DATE'},
        {'name': 'open', 'type': 'FLOAT'},
        {'name': 'high', 'type': 'FLOAT'},
        {'name': 'low', 'type': 'FLOAT'},
        {'name': 'close', 'type': 'FLOAT'},
        {'name': 'vwap', 'type': 'FLOAT'},
        ] 
      }

    # Pipeline
    (
        pipeline
        | 'Create Stream' >> beam.Create([None])  # Dummy PCollection to trigger Kafka consumer
        | 'Consume Kafka' >> beam.ParDo(KafkaConsumer(config, kafka_topic_name ))
        | 'Write to BigQuery' >> WriteToBigQuery(
            table=f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}",
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
        )
    )
