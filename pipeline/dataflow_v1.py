import base64
import datetime
import http.server
import json
import random
import google.auth
import google.auth.transport.urllib3
import urllib3
import confluent_kafka
import functools
import time
import apache_beam as beam
from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions
import json


PROJECT_ID = 'valid-verbena-437709-h5'
DATASET_ID = 'nifty50'
TABLE_ID = 'nifty50_historical_data_65'
kafka_cluster_name = 'dataopsguru-kafka'
region = 'us-central1'
project_id = 'valid-verbena-437709-h5'
port = '9092'
kafka_topic_name = 'dataops-kafka-topic'

# Function to read password from the file
def read_password_from_file(password_file_path):
    with open(password_file_path, 'r') as file:
        return file.read().strip()  # Read password and remove any extra whitespace

# Read the password from 'password.txt'
password = read_password_from_file('./password.txt')

# Kafka Producer configuration with OAUTHBEARER authentication
config = {
    'bootstrap.servers': f'bootstrap.{kafka_cluster_name}.{region}.managedkafka.{project_id}.cloud.goog:{port}',
    'security.protocol': 'SASL_SSL',
    'sasl.jaas.config' : 'org.apache.kafka.common.security.plain.PlainLoginModule',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username' :"dataops-guru-sa@valid-verbena-437709-h5.iam.gserviceaccount.com" ,
    'sasl.password' : password 
    }

table_schema = {
    'fields': [
        {'name': 'symbol', 'type': 'STRING'},
        {'name': 'date', 'type': 'DATE'},
        {'name': 'open', 'type': 'FLOAT'},
        {'name': 'high', 'type': 'FLOAT'},
        {'name': 'low', 'type': 'FLOAT'},
        {'name': 'close', 'type': 'FLOAT'},
        {'name': 'vwap', 'type': 'FLOAT'}
    ]
}
class ParseKafkaMessage(beam.DoFn):
    def process(self, element):
        # Decode the Kafka message (Key, Value) and parse JSON
        _, value = element
        message = json.loads(value.decode('utf-8'))
        
        # Ensure required fields are present
        if all(k in message for k in ['symbol', 'date', 'open', 'high', 'low', 'close', 'vwap']):
            yield {
                'symbol': message['symbol'],
                'date': message['date'],
                'open': float(message['open']),
                'high': float(message['high']),
                'low': float(message['low']),
                'close': float(message['close']),
                'vwap': float(message['vwap'])
            }

pipeline_options = PipelineOptions(
    runner='DataflowRunner',   #for Dataflow job change to runner='DataflowRunner'
    project='valid-verbena-437709-h5',
    region='us-central1',   #for Dataflow job change to 'us-west1'
    temp_location='gs://dataops-dataflow-2024/temp',
    staging_location='gs://dataops-dataflow-2024/staging',
    streaming=True,  #Enable streaming mode
    #Dataflow parameters that are optional
    job_name='streaming-kafka-bq-nifty50-v1',  #Set the Dataflow job name here
    num_workers=3,  #Specify the number of workers
    max_num_workers=10,  #Specify the maximum number of workers
    disk_size_gb=100,  #Specify the disk size in GB per worker
    autoscaling_algorithm='THROUGHPUT_BASED',  #Specify the autoscaling algorithm
    machine_type='n1-standard-4',  #Specify the machine type for the workers
    service_account_email='dataops-guru-sa@valid-verbena-437709-h5.iam.gserviceaccount.com' 
)

# Define the Apache Beam pipeline
with beam.Pipeline(options=pipeline_options) as p:
    (
        p
        # Read from Kafka topic
        | 'Read from Kafka' >> ReadFromKafka(
            consumer_config=config,
            topics=['dataops-kafka-topic'],
            with_metadata=False,
        )
        # Parse JSON messages
        | 'Parse JSON' >> beam.ParDo(ParseKafkaMessage())
        # Write to BigQuery
        | 'Write to BigQuery' >> WriteToBigQuery(
            table=f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}",
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
        )
    )
