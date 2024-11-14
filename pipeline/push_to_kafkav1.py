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
from nsepython import equity_history

# Token Provider class
# This class handles the OAuth token retrieval and formatting
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
  """Method to get the Token"""
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

producer = confluent_kafka.Producer(config)

# Produce and submit 10 messages
# List of Nifty 50 stock symbols
nifty_50_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HINDUNILVR", "KOTAKBANK", "SBIN", "HDFC", "BHARTIARTL", 
                    "BAJFINANCE", "ITC", "AXISBANK", "LT", "ASIANPAINT", "DMART", "HCLTECH", "MARUTI", "WIPRO", "HDFCLIFE", 
                    "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "POWERGRID", "ONGC", "JSWSTEEL", "BAJAJFINSV", "COALINDIA", "NTPC"]

end_date = datetime.datetime.now().strftime("%d-%m-%Y")
start_date = (datetime.datetime.now() - datetime.timedelta(days=65)).strftime("%d-%m-%Y")

for symbol in nifty_50_symbols:
    try:
        df = equity_history(symbol, "EQ", start_date, end_date)
        # Convert the DataFrame to JSON format and publish each row to Kafka
        for index, row in df.iterrows():
            message = {
                'symbol': symbol,
                'date': row['CH_TIMESTAMP'],
                'open': row['CH_OPENING_PRICE'],
                'high': row['CH_TRADE_HIGH_PRICE'],
                'low': row['CH_TRADE_LOW_PRICE'],
                'close': row['CH_CLOSING_PRICE'],
                'vwap': row['VWAP']
            }
            # Serialize data to bytes
            serialized_data = json.dumps(message).encode('utf-8')

            # Produce the message
            producer.produce(kafka_topic_name, serialized_data)

            print(f"Produced {message} messages")
        # Wait for 5 minutes before processing the next symbol
        time.sleep(300)
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")

producer.flush()