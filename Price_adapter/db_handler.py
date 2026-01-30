from pymongo import MongoClient

def insert_multiple_tickers_to_mongodb(ticker_data_list, db_name="stock_data", collection_name="tickers"):
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client[db_name]
        collection = db[collection_name]

        # Insert multiple ticker data
        if ticker_data_list:
            result = collection.insert_many(ticker_data_list)
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