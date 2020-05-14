import motor.motor_asyncio
import requests
import json
import re
import time
from threading import Lock, Thread
import random
import time
from models import Node
import aiohttp
import asyncio
from datetime import datetime
import motor.motor_asyncio

lock = Lock()

url = "https://query.wikidata.org/sparql"
headers = {
    'User-Agent': 'bot (testing this)',
}

threads = {}
nodes = {}
edges = {}
explored = {}


async def get(query, children, label_field=False):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params={'format': 'json', 'query': query}, headers=headers) as response:
            try:
                data = await response.json(content_type=None)
                data = data['results']['bindings']
            except Exception as e:
                print('there was an exception requesting', e)
                return False

            if not label_field:
                for x in data:
                    wid = re.search(r'Q\d*$', x['entity_']['value'])
                    children['wd:'+wid.group()] = x['propertyLabel']['value']
            elif len(data) > 0:
                children.append(data[0]['label']['value'])
            else:
                return False

            return True


def request_entity(obj_id):
    print('REQUESTING', obj_id)
    label_query = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
    PREFIX wd: <http://www.wikidata.org/entity/> 
    select  *
    where {
            """+obj_id+""" rdfs:label ?label .
    FILTER (langMatches( lang(?label), "EN" ) )
        } 
    LIMIT 1"""
    primary_query = """SELECT ?propertyLabel ?entity_ {
      VALUES (?company) {("""+obj_id+""")}

      ?company ?p ?statement .
      ?statement ?entity ?entity_ .

      ?property wikibase:claim ?p.
      ?property wikibase:statementProperty ?entity.

      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
      FILTER(REGEX(STR(?entity_), "Q[0-9]*$"))
    }"""
    secondary_query = """SELECT ?propertyLabel ?entity_ {
      VALUES (?company) {("""+obj_id+""")}

      ?company ?p ?statement .
      ?statement ?ps ?ps_ .

      ?wd wikibase:claim ?p.
      ?wd wikibase:statementProperty ?ps.

      ?statement ?entity ?entity_ .
      ?property wikibase:qualifier ?entity .

      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
      FILTER(REGEX(STR(?entity_), "Q[0-9]*$"))
    }"""

    children = {}
    node_name = []  # did this to get a mutable data type

    # makes the 3 requests asyncronously to get the label and the primary and secondary connections
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    coroutines = [get(label_query, node_name, True), get(
        primary_query, children), get(secondary_query, children)]
    results = loop.run_until_complete(asyncio.gather(*coroutines))

    # makes sure everything went well
    for x in results:
        if not x:
            raise "Node doesn't effectively exist"
            # print('there was an error parsing node', obj_id)
            # return {}

    # saves the node to the database
    n = Node(wid=obj_id, label=node_name[0], children=children)
    n.save()

    return children


def get_children(id):
    node = Node.objects(wid=id)
    if node:
        return node[0].children.keys()
    else:
        return request_entity(id).keys()


'''
format:
node: { "id": "n0", "label": "A node", }
edge: { "id": "e2", "source": "n2",  "target": "n0", label:"" }

the data must come in as only objects so no time included or other shitty data
'''


async def get_doc(id, parent, collection):
    document = await collection.find_one({'wid': id})
    parent[id] = document


def get_graph_data(request_paths):
    ans_nodes = {}
    ans_links = {}

    # this is for the polling
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = motor.motor_asyncio.AsyncIOMotorClient(
        'mongodb+srv://stuff:jStigter1@cluster0-mgq8y.mongodb.net/data?retryWrites=true&w=majority', io_loop=loop)
    db = client.data
    collection = db['node']

    required = set()
    for a in request_paths:
        for x in a:
            required.add(x)

    documents = {}
    routines = [get_doc(x, documents, collection) for x in required]
    start = time.time()
    loop.run_until_complete(asyncio.gather(*routines))
    print('request end', (time.time()-start)*1000,
          (time.time()-start)/len(required)*1000)

    for request_nodes in request_paths:
        last_node = None
        for index in range(0, len(request_nodes)):
            x = request_nodes[index]

            #node = Node.objects.get(wid=x)
            node = documents[x]

            n = {}
            n['label'] = node['label']
            n['id'] = node['wid']
            n['distance'] = index

            ans_nodes[x] = n

            # this is all to get the edge from this node to the next
            if index == 0:
                last_node = node
                continue

            e = {}
            next = last_node['wid']
            key = next+x if next > x else x+next

            # if not in this node then must be in the next node
            if next in node['children'].keys():
                e['label'] = node['children'][next]
                e['source'] = x
                e['target'] = next
            else:
                e['label'] = last_node['children'][x]
                e['source'] = next
                e['target'] = x

            e['id'] = key

            ans_links[key] = e

            last_node = node

    client.close()

    return {'nodes': ans_nodes, 'links': ans_links}


if __name__ == '__main__':
    obj_id = 'wd:Q76'
    data = request_entity(obj_id)
    print(data)
    a = get_children(obj_id)
    print(a)
    print('done')
