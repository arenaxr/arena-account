
import logging

from pymongo import MongoClient
from pymongo.database import Database

'''
persist_db.py: This Mongo connection manager is triggered at startup and checked
before each database call, this allows a lazy connection to Mongo. There is no
explicit disconnect from Mongo. PyMongo manages its own connection pooling and the OS
handles socket cleanup on process exit. Plus, Django shutdown is hard to detect.
'''

client: MongoClient = None
db: Database = None

logging.getLogger("pymongo").setLevel(logging.WARNING)

def get_persist_db():
    global client, db
    if db:
        return db

    # connect to mongodb, read-only
    print("arena_persist: connecting...")
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
    return db
