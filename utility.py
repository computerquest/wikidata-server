import requests
import json
import re
import time
from threading import Lock, Thread
import random

lock = Lock()

url = "https://query.wikidata.org/sparql"
headers = {
    'User-Agent': 'bot (testing this)',
}

threads = {}
nodes = {}
edges = {}
explored = {}


def request_entity(obj_id):
    #print('requesting', obj_id)
    query = """SELECT ?wdLabel ?ps_ ?ps_Label ?wdpqLabel ?pq_ ?pq_Label {
      VALUES (?company) {("""+obj_id+""")}

      ?company ?p ?statement .
      ?statement ?ps ?ps_ .

      ?wd wikibase:claim ?p.
      ?wd wikibase:statementProperty ?ps.

      OPTIONAL {
      ?statement ?pq ?pq_ .
      ?wdpq wikibase:qualifier ?pq .
      }

      SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }"""
    data = None

    broken = True
    while broken:
        try:
            r = requests.get(
                url, params={'format': 'json', 'query': query}, headers=headers)
            data = r.json()
            broken = False
        except Exception as e:
            print('an error occured', e)
            # this sleeps for a minute to try and avoid rate call issues
            time.sleep(1)
            # return []

    # this is used to get rid irrelevant garbage values that we don't want
    data = data['results']['bindings']

    # data = [x for x in data if re.search(
    #     r'wikidata.*Q\d*$', x['ps_']['value']) is not None and ('pq_' not in x or re.search(
    #         r'wikidata.*Q\d*$', x['pq_']['value']) is not None)]

    new_data = []
    for x in data:
        if 'pq_' in x:
            st = re.search(r'Q\d*$', x['pq_']['value'])

            if st is not None:
                x['pq_']['value'] = 'wd:'+st.group()
            else:
                continue

        if 'ps_' in x:
            st = re.search(r'Q\d*$', x['ps_']['value'])

            if st is not None:
                x['ps_']['value'] = 'wd:'+st.group()
            else:
                continue

        new_data.append(x)

    data = new_data

    threads[obj_id] = Thread(
        target=create_graph_segment, args=(obj_id, data), daemon=True)
    threads[obj_id].start()

    return data


def extract_labels(data):
    ans = []  # ans will store as {'prep': , 'object':}

    for x in data:
        ans.append({'prep': x['wdLabel']['value'],
                    'object': x['ps_Label']['value']})

        if 'wdpqLabel' in x:
            ans.append({'prep': x['wdpqLabel']['value'],
                        'object': x['pq_Label']['value']})

    return ans


def extract_objects_raw(data):
    ans = set()

    for x in data:
        ans.add(x['ps_']['value'])

        if 'pq_' in x:
            ans.add(x['pq_']['value'])

        if 'ps_' in x:
            ans.add(x['ps_']['value'])

    return ans


def extract_objects_proccessed(id):
    return explored[id]


def get_children(id):
    if id not in explored.keys():
        return extract_objects_raw(request_entity(id))
    else:
        return extract_objects_proccessed(id)


'''
format:
node: { "id": "n0", "label": "A node", }
edge: { "id": "e2", "source": "n2",  "target": "n0", label:"" }

the data must come in as only objects so no time included or other shitty data
'''


def create_graph_segment(origin, data):
    # this is to check and make sure that we aren't making multiple requests
    lock.acquire()

    if origin in explored.keys():
        lock.release()
        return

    lock.release()

    children = []

    for i in data:

        # this is to add all of the requierd nodes ps
        node_label = i['ps_']['value']
        if node_label not in nodes:
            nodes[node_label] = {'id': node_label,
                                 'label': i["ps_Label"]['value']}
        children.append(node_label)

        # this is adds all edges ps
        proposed_edge = {'id':   origin+i['ps_']['value'] if origin > i['ps_']['value'] else i['ps_']['value']+origin,
                         'source': origin, 'target': i['ps_']['value'], 'label': i['wdLabel']['value']}
        edges[proposed_edge['id']] = proposed_edge

        if 'pq_' not in i.keys():
            continue

        # required to add all nodes pq
        node_label = i['pq_']['value']
        if node_label not in nodes:
            nodes[node_label] = {'id': node_label,
                                 'label': i['pq_Label']['value']}
        children.append(node_label)

        # this is adds all edges ps
        proposed_edge = {'id': origin+i['pq_']['value'] if origin > i['pq_']['value'] else i['pq_']['value']+origin,
                         'source': origin, 'target': i['pq_']['value'], 'label': i['wdpqLabel']['value']}
        edges[proposed_edge['id']] = proposed_edge

    if origin not in nodes.keys():
        query = """SELECT DISTINCT * WHERE { 
        """+origin+""" rdfs:label ?label . 
        FILTER (langMatches( lang(?label), "ES" ) )  
        }"""
        data = 'origin'

        try:
            print('making the request', query)
            r = requests.get(
                url, params={'format': 'json', 'query': query}, headers=headers)
            data = r.json()
            data = data['results']['bindings'][0]['label']['value']
        except:
            print('error fetching name')

        nodes[origin] = {'id': origin, 'label': data}

    explored[origin] = children

    # return {'nodes': nodes, 'edges': edges}


def create_graph(request_paths):
    ans = {'nodes': [], 'links': []}

    for request_nodes in request_paths:

        for index in range(0, len(request_nodes)):
            x = request_nodes[index]

            if x not in threads.keys():
                continue

            if threads[x].isAlive():
                threads[x].join()

            if x not in [x['id'] for x in ans['nodes']]:
                nodes[x]['distance'] = index
                ans['nodes'].append(nodes[x])

            if index+1 > len(request_nodes)-1:
                continue

            next = request_nodes[index+1]
            key = next+x if next > x else x+next
            if key in edges.keys() and key not in [x['id'] for x in ans['links']]:
                ans['links'].append(edges[key])

    return ans


def create_graph_data(request_paths):
    ans_nodes = {}
    ans_links = {}

    for request_nodes in request_paths:

        for index in range(0, len(request_nodes)):
            x = request_nodes[index]

            if x not in threads.keys():
                continue

            if threads[x].isAlive():
                threads[x].join()

            nodes[x]['distance'] = index
            ans_nodes[x] = nodes[x]

            if index+1 > len(request_nodes)-1:
                continue

            next = request_nodes[index+1]
            key = next+x if next > x else x+next
            ans_links[key] = edges[key]

    return {'nodes': ans_nodes, 'links': ans_links}


if __name__ == '__main__':
    data = request_entity('wd:Q76')
    a = extract_labels(data)
    print('done')
