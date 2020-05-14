from flask import Flask, request, jsonify
import re
from search import launch_search, get_search_progress, detach_search, threads
from utility import request_entity, get_graph_data
import flask
from flask_cors import CORS, cross_origin
import json
from threading import Lock, Thread
import time
from db import initialize_db
from mongoengine import connect

app = Flask(__name__)
cors = CORS(app)
app.config["DEBUG"] = True
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['MONGODB_SETTINGS'] = {
    'db': 'data',
    'host': 'mongodb+srv://stuff:jStigter1@cluster0-mgq8y.mongodb.net/data?retryWrites=true&w=majority'
}


initialize_db(app)

# *this is to make sure that searches are active
request_history = set()


def check_active():
    while True:
        print('checking the active', request_history)

        for x in threads.keys():
            print(x, threads[x]['active'])
            if threads[x]['active'] is True and x not in request_history:
                print('detaching', x)
                detach_search(together=x, kill=True)

        request_history.clear()

        time.sleep(30)


t = Thread(
    target=check_active, daemon=True)
t.start()


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/start', methods=['GET'])
@cross_origin()
def start():
    try:
        first = 'wd:'+request.args.get('obj1')
        second = 'wd:'+request.args.get('obj2')
    except:
        print('error in start')
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

    request_history.add((first+second if first > second else second+first))
    if re.search(r'wd:Q\d*$', first) is not None and re.search(r'Q\d*$', second) is not None:
        print('starting the search')
        launch_search(first, second)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}


@app.route('/detach', methods=['GET'])
@cross_origin()
def detach():
    first = 'wd:'+request.args.get('obj1')
    second = 'wd:'+request.args.get('obj2')
    detach_search(first, second)
    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}


@app.route('/poll', methods=['GET'])
@cross_origin()
def poll_raw():
    first = 'wd:'+request.args.get('obj1')
    second = 'wd:'+request.args.get('obj2')

    try:
        results, checked, frontier = get_search_progress(first, second)
    except:
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

    request_history.add((first+second if first > second else second+first))

    return jsonify({**get_graph_data(results), 'paths': results, 'checked': checked, 'frontier': frontier})


if __name__ == '__main__':
    app.run(debug=True)
