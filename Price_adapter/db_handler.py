from pymongo import MongoClient
from redis import Redis
from datetime import datetime
import json
def imt_mongo(data, db_name="PaperQuant", collection_name="candles"):
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client[db_name]
        collection = db[collection_name]

        # Insert multiple ticker data
        if data:
            result = collection.insert_many(data)
            #print(f"Inserted {len(result.inserted_ids)} ticker records into MongoDB.")
            return result
        else:
            print("No data to insert.")
            return None

    except Exception as e:
        print(f"An error occurred while inserting ticker data: {e}")
        raise

    finally:
        # Close the MongoDB connection
        client.close()

# Initialize Redis client as a global variable
redis_client = Redis(host='localhost', port=6379, db=0)  # Use db=0 for db_handler

def _json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def update_redis_candles(ticker: str, candle_data: dict):
    try:
        redis_key = f"candles:{ticker}"

        redis_client.rpush(
            redis_key,
            json.dumps(candle_data, default=_json_serializer)
        )

        redis_client.ltrim(redis_key, -5, -1)

    except Exception as e:
        print(f"An error occurred while updating Redis cache: {e}")
        raise