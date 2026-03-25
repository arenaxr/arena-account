'''
Mongo DB PyMongo queries for Persist:
https://pymongo.readthedocs.io/en/stable/index.html
'''
import json
from datetime import datetime

from bson import ObjectId

# assign accessible model for persist collection
def get_arenaobjects_collection():
    from .persist_db import get_persist_db
    return get_persist_db()['arenaobjects']

# arenaobjects schema reference:
# https://github.com/arenaxr/arena-persist/blob/master/server.js#L30-L43
# object_id: {type: String, required: true, index: true},
# type: {type: String, required: true, index: true},
# attributes: {type: Object, required: true, default: {}},
# expireAt: {type: Date, expires: 0},
# realm: {type: String, required: true, index: true},
# namespace: {type: String, required: true, index: true, default: 'public'},
# sceneId: {type: String, required: true, index: true},
# private: {type: Boolean},
# program_id: {type: String},
# createdAt: {type: Date}, // via timestamps: true
# updatedAt: {type: Date}, // via timestamps: true


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
            },
            "last_updated": {"$max": "$updatedAt"}
        }
    }])
    return {doc['_id']['namespace']: doc.get('last_updated') for doc in arenaobjects}


def read_persist_scenes_all():
    arenaobjects = get_arenaobjects_collection().aggregate([
        {
            "$group": {
                "_id": {
                    "namespace": "$namespace",
                    "sceneId": "$sceneId",
                },
                "last_updated": {"$max": "$updatedAt"}
            }
        },
        {
            "$project": {
                "name": {
                    "$concat": ["$_id.namespace", "/", "$_id.sceneId"]
                },
                "last_updated": 1
            }
        }
    ])
    return {doc['name']: doc.get('last_updated') for doc in arenaobjects}


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
                },
                "last_updated": {"$max": "$updatedAt"}
            }
        },
        {
            "$project": {
                "name": {
                    "$concat": ["$_id.namespace", "/", "$_id.sceneId"]
                },
                "last_updated": 1
            }
        }
    ])
    return {doc['name']: doc.get('last_updated') for doc in arenaobjects}


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
