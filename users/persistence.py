import json
from datetime import datetime

from bson import ObjectId

from .models import get_arenaobjects_collection

# Mongo DB PyMongo queries for Persist:
# https://pymongo.readthedocs.io/en/stable/index.html


class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # Convert ObjectId to string
        if isinstance(o, datetime):
            return o.isoformat()  # Convert datetime to ISO format
        return super().default(o)  # Call the default method for other types


def read_persist_ns_all():
    arenaobjects = get_arenaobjects_collection().aggregate([{
        "$group": {
            "_id": {
                "namespace": "$namespace",
                }
            }
        }
    ])
    return [doc['_id']['namespace'] for doc in arenaobjects]


def read_persist_scenes_all():
    arenaobjects = get_arenaobjects_collection().aggregate([
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "sceneId": "$sceneId",
                }
            }
        },
        {
            "$project": {
                "name": {
                    "$concat": ["$_id.namespace", "/", "$_id.sceneId"]
                }
            }
        }
    ])
    return [doc['name'] for doc in arenaobjects]


def read_persist_scenes_by_namespace(namespaces):
    arenaobjects = get_arenaobjects_collection().aggregate([
        {
            "$match": {
                "namespace": {"$in": namespaces}
            }
        },
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "sceneId": "$sceneId",
                }
            }
        },
        {
            "$project": {
                "name": {
                    "$concat": ["$_id.namespace", "/", "$_id.sceneId"]
                }
            }
        }
    ])
    return [doc['name'] for doc in arenaobjects]


def read_persist_scene_objects(namespace, scene):
    query = {"namespace": namespace, "sceneId": scene}
    arenaobjects = get_arenaobjects_collection().find(query)
    json_str = MongoJSONEncoder().encode(list(arenaobjects))
    return json.loads(json_str)


def delete_persist_scene_objects(namespace, scene):
    query = {"namespace": namespace, "sceneId": scene}
    result = get_arenaobjects_collection().delete_many(query)
    return result


def delete_persist_namespace_objects(namespace):
    query = {"namespace": namespace}
    result = get_arenaobjects_collection().delete_many(query)
    return result
