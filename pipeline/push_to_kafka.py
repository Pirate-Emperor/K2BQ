from nsepython import equity_history
from kafka import KafkaProducer
import datetime
import json
import time

# Initialize Kafka producer
KAFKA_TOPIC = 'dataops-kafka-topic'
KAFKA_SERVER = 'bootstrap.dataops-kafka.us-central1.managedkafka.valid-verbena-437709-h5.cloud.goog:9092'  # Replace with your Kafka broker address
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

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
            producer.send(KAFKA_TOPIC, value=message)
            print(f"Sent to Kafka: {message}")
        
        # Wait for 5 minutes before processing the next symbol
        time.sleep(300)
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")

# Close the producer connection
producer.close()
