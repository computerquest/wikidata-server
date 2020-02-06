import requests
import json
import re
import time

url = "https://query.wikidata.org/sparql"
headers = {
    'User-Agent': 'bot (testing this)',
}


def request_entity(obj_id):
    print('requesting', obj_id)
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
        except:
            print('an error occured')
            # this sleeps for a minute to try and avoid rate call issues
            time.sleep(60)
            # return []

    # this is used to get rid irrelevant garbage values that we don't want
    data = data['results']['bindings']

    data = [x for x in data if re.search(
        r'wikidata.*Q\d*$', x['ps_']['value']) is not None and ('pq_' not in x or re.search(
            r'wikidata.*Q\d*$', x['pq_']['value']) is not None)]

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

# this is super inefficient and needs to be optimized


def extract_objects(data):
    ans = set()

    for x in data:
        ans.add('wd:'+x['ps_']['value'].rsplit('/', 1)[1])

        if 'pq_' in x:
            st = re.search(r'Q\d*$', x['pq_']['value'])

            if st is not None:
                ans.add('wd:'+st.group())
                x['pq_']['value'] = 'wd:'+st.group()

        if 'ps_' in x:
            st = re.search(r'Q\d*$', x['ps_']['value'])

            if st is not None:
                ans.add('wd:'+st.group())
                x['ps_']['value'] = 'wd:'+st.group()

    return ans


'''
format:
node: { "id": "n0", "label": "A node", }
edge: { "id": "e2", "source": "n2",  "target": "n0", label:"" }

the data must come in as only objects so no time included or other shitty data
'''


def create_graph(origin, data):
    nodes = []
    edges = []
    for i in data:

        # this is to add all of the requierd nodes ps
        node_label = i['ps_']['value']
        if node_label not in nodes:
            nodes.append({'id': node_label, 'label': i["ps_Label"]['value']})

        # this is adds all edges ps
        proposed_edge = {'id': i['wdLabel']['value']+i['ps_Label']['value'],
                         'source': origin, 'target': i['ps_']['value'], 'label': i['wdLabel']['value']}
        if proposed_edge not in edges:
            edges.append(proposed_edge)

        if 'pq_' not in i.keys():
            continue

        # required to add all nodes pq
        node_label = i['pq_']['value']
        if node_label not in nodes:
            nodes.append({'id': node_label, 'label': i['pq_Label']['value']})

        # this is adds all edges ps
        proposed_edge = {'id': i['wdpqLabel']['value']+i['pq_Label']['value'],
                         'source': 'origin', 'target': i['pq_']['value'], 'label': i['wdpqLabel']['value']}
        if proposed_edge not in edges:
            edges.append(proposed_edge)

    return {'nodes': nodes, 'edges': edges}


if __name__ == '__main__':
    data = request_entity('wd:Q76')
    a = extract_labels(data)
    b = extract_objects(data)
    c = create_graph('wd:Q76', data)
    print('done')
