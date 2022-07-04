import json
from safety_db import INSECURE, INSECURE_FULL

changeset_schema = {
    "title": "Changeset_Schema",
    "description": "Schema for RTQA Praxi changeset",
    "type": "object",
    "properties" : {
        "label" : { "type" : "string" },
        "open_time" : { "type" : "number" },
        "close_time" : { "type" : "number" },
        "changes" : {
            "type" : "array",
            "items" : {
                "type" : "string"
            }
        }
    },
    "required": ["label", "changes"]
}

tagset_schema = {
    "title": "Tagset_Schema",
    "description": "Schema for RTQA Praxi tagset",
    "type": "object",
    "properties" : {
        "label" : {
            "type" : "string"
        },
        "tags" : {
            "type" : "array",
            "items" : {
                "type" : "object",
                "properties" : {
                    "tag" : { "type" : "string" },
                    "frequency" : { "type" : "integer" }
                },
                "required": ["tag", "frequency"]
            }
        }
    },
    "required": ["label", "tags"]
}

f1 = open('changeset_schema', 'w')
f2 = open('tagset_schema', 'w')

json.dump(changeset_schema, f1)
json.dump(tagset_schema, f2)
