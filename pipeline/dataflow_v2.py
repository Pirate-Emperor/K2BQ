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
from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions
import confluent_kafka
import json

class TokenProvider(object):

  def __init__(self, **config):
    self.credentials, _project = google.auth.default()
    self.http_client = urllib3.PoolManager()
    self.HEADER = json.dumps(dict(typ='JWT', alg='GOOG_OAUTH2_TOKEN'))

  def valid_credentials(self):
    if not self.credentials.valid:
      self.credentials.refresh(google.auth.transport.urllib3.Request(self.http_client))
    return self.credentials

  def get_jwt(self, creds):
    return json.dumps(
        dict(
            exp=creds.expiry.timestamp(),
            iss='Google',
            iat=datetime.datetime.now(datetime.timezone.utc).timestamp(),
            scope='kafka',
            sub=creds.service_account_email,
        )
    )

  def b64_encode(self, source):
    return (
        base64.urlsafe_b64encode(source.encode('utf-8'))
        .decode('utf-8')
        .rstrip('=')
    )

  def get_kafka_access_token(self, creds):
    return '.'.join([
      self.b64_encode(self.HEADER),
      self.b64_encode(self.get_jwt(creds)),
      self.b64_encode(creds.token)
    ])

  def token(self):
    creds = self.valid_credentials()
    return self.get_kafka_access_token(creds)

  def confluent_token(self):
    creds = self.valid_credentials()

    utc_expiry = creds.expiry.replace(tzinfo=datetime.timezone.utc)
    expiry_seconds = (utc_expiry - datetime.datetime.now(datetime.timezone.utc)).total_seconds()

    return self.get_kafka_access_token(creds), time.time() + expiry_seconds

# Confluent does not use a TokenProvider object
# It calls a method
def make_token(args):
    t = TokenProvider()
    token = t.confluent_token()
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

class CustomKafkaConsumer(beam.DoFn):
    def __init__(self, kafka_config, topic):
        self.kafka_config = kafka_config
        self.topic = topic

    def setup(self):
        # Initialize Kafka consumer
        self.consumer = confluent_kafka.Consumer(self.kafka_config)
        self.consumer.subscribe([self.topic])

    def process(self, element):
        try:
            # Poll Kafka for messages
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                return
            if msg.error():
                if msg.error().code() == confluent_kafka.KafkaError._PARTITION_EOF:
                    print(f"Reached end of partition: {msg.error()}")
                else:
                    raise confluent_kafka.KafkaException(msg.error())
                return
            
            # Decode and parse the Kafka message
            value = msg.value().decode('utf-8')
            parsed_message = json.loads(value)

            # Ensure required fields are present
            if all(k in parsed_message for k in ['symbol', 'date', 'open', 'high', 'low', 'close', 'vwap']):
                yield {
                    'symbol': parsed_message['symbol'],
                    'date': parsed_message['date'],
                    'open': float(parsed_message['open']),
                    'high': float(parsed_message['high']),
                    'low': float(parsed_message['low']),
                    'close': float(parsed_message['close']),
                    'vwap': float(parsed_message['vwap']),
                }
        except Exception as e:
            print(f"Error processing Kafka message: {e}")

    def teardown(self):
        # Close Kafka consumer
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

pipeline_options = PipelineOptions(
    runner='DataflowRunner',   #for Dataflow job change to runner='DataflowRunner'
    project='valid-verbena-437709-h5',
    region='us-central1',   #for Dataflow job change to 'us-west1'
    temp_location='gs://dataops-dataflow-2024/temp',
    staging_location='gs://dataops-dataflow-2024/staging',
    streaming=True,  #Enable streaming mode
    #Dataflow parameters that are optional
    job_name='streaming-kafka-bq-nifty50-v4',  #Set the Dataflow job name here
    num_workers=3,  #Specify the number of workers
    max_num_workers=10,  #Specify the maximum number of workers
    disk_size_gb=100,  #Specify the disk size in GB per worker
    autoscaling_algorithm='THROUGHPUT_BASED',  #Specify the autoscaling algorithm
    machine_type='n1-standard-4',  #Specify the machine type for the workers
    service_account_email='dataops-guru-sa@valid-verbena-437709-h5.iam.gserviceaccount.com'
)


# Define the pipeline
with beam.Pipeline(options=pipeline_options) as pipeline:
    (
        pipeline
        | 'Create Stream' >> beam.Create([None])  # Dummy PCollection to trigger Kafka consumer
        | 'Consume Kafka' >> beam.ParDo(CustomKafkaConsumer(config, kafka_topic_name ))
        | 'Write to BigQuery' >> WriteToBigQuery(
            table=f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}",
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
        )
    )