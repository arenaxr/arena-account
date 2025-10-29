import logging

from fastapi import FastAPI
from pymongo import MongoClient
from pymongo.database import Database

client: MongoClient
db: Database

app = FastAPI()

logging.getLogger("pymongo").setLevel(logging.WARNING)

# connect to mongodb, read-only
client = MongoClient("mongodb://mongodb/arena_persist?readPreference=primaryPreferred")

try:
    dba = client.admin
    server_status = dba.command('serverStatus')
    current_connections = server_status['connections']['current']
    print(f"arena_persist: current connections: {current_connections}")
    total_connections = server_status['connections']['totalCreated']
    print(f"arena_persist: total connections created: {total_connections}")

except Exception as e:
    print(f"arena_persist: error: {e}")

db = client.arena_persist

@app.on_event("shutdown")
def close_db_connection():
    global client
    # disconnect from mongodb
    if client:
        print("arena_persist: closing connection")
        client.close()
