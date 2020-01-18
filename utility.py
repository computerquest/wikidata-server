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
        r'wikidata.*Q\d*$', x['ps_']['value']) is not None]

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


def extract_objects(data):
    ans = set()

    for x in data:
        ans.add('wd:'+x['ps_']['value'].rsplit('/', 1)[1])

        if 'pq_' in x:
            st = re.search(r'Q\d*$', x['pq_']['value'])

            if st is not None:
                ans.add('wd:'+st.group())

    return ans


if __name__ == '__main__':
    data = request_entity('wd:Q76')
    extract_labels(data)
    extract_objects(data)
    print('done')
