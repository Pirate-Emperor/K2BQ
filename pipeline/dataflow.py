import apache_beam as beam
from apache_beam.io.kafka import ReadFromKafka
from apache_beam.io.gcp.bigquery import WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions
import json

# Kafka and BigQuery configuration
PROJECT_ID = 'valid-verbena-437709-h5'
DATASET_ID = 'nifty50'
TABLE_ID = 'nifty50_historical_data_65'
KAFKA_TOPIC = 'dataops-kafka-topic'
KAFKA_SERVER = 'bootstrap.dataops-kafka.us-central1.managedkafka.valid-verbena-437709-h5.cloud.goog:9092'  # Replace with your Kafka broker address

# Define the BigQuery table schema
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

pipeline_options = PipelineOptions(
    runner='DataflowRunner',   #for Dataflow job change to runner='DataflowRunner'
    project='valid-verbena-437709-h5',
    region='us-central1',   #for Dataflow job change to 'us-west1'
    temp_location='gs://dataops-dataflow-2024/temp',
    staging_location='gs://dataops-dataflow-2024/staging',
    streaming=True,  #Enable streaming mode
    #Dataflow parameters that are optional
    job_name='streaming-kafka-bq-nifty50',  #Set the Dataflow job name here
    num_workers=3,  #Specify the number of workers
    max_num_workers=10,  #Specify the maximum number of workers
    disk_size_gb=100,  #Specify the disk size in GB per worker
    autoscaling_algorithm='THROUGHPUT_BASED',  #Specify the autoscaling algorithm
    machine_type='n1-standard-4',  #Specify the machine type for the workers
    service_account_email='dataops-guru-sa@valid-verbena-437709-h5.iam.gserviceaccount.com' 
)


def parse_kafka_message(element):
    """Parse Kafka message from bytes to JSON."""
    message = element.value.decode('utf-8')
    return json.loads(message)

# Define the Apache Beam pipeline
with beam.Pipeline(options=pipeline_options) as p:
    (
        p
        # Read from Kafka topic
        | 'Read from Kafka' >> ReadFromKafka(
            consumer_config={'bootstrap.servers': KAFKA_SERVER},
            topics=[KAFKA_TOPIC]
        )
        # Parse JSON messages
        | 'Parse JSON' >> beam.Map(parse_kafka_message)
        # Write to BigQuery
        | 'Write to BigQuery' >> WriteToBigQuery(
            table=f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}",
            schema=table_schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
        )
    )
