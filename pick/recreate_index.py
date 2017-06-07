#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from elasticsearch import Elasticsearch
es = Elasticsearch()

index_name = 'tsec'
if es.indices.exists(index_name):
    print("deleting '%s' index..." % (index_name))
    res = es.indices.delete(index = index_name)
    print(" response: '%s'" % (res))

request_body = {
    "settings" : {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}
print("creating '%s' index..." % (index_name))
res = es.indices.create(index = index_name, body = request_body)
print(" response: '%s'" % (res))
