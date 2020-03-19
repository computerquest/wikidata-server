from flask import Flask, request, jsonify
import re
from search import launch_search, get_search_progress, detach_search
from utility import create_graph, request_entity, create_graph_data
import flask
from flask_cors import CORS, cross_origin
import json

app = Flask(__name__)
cors = CORS(app)
app.config["DEBUG"] = True
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def hello():
    return "Hello World!"


@app.route('/start', methods=['GET'])
@cross_origin()
def start():
    try:
        first = request.args.get('obj1')
        second = request.args.get('obj2')
    except:
        print('error in start')
        return json.dumps({'success': False}), 400, {'ContentType': 'application/json'}

    if re.search(r'Q\d*$', first) is not None and re.search(r'Q\d*$', second) is not None:
        print('starting the search')
        launch_search('wd:'+first, 'wd:'+second)
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


@app.route('/poll_graph', methods=['GET'])
@cross_origin()
def poll():
    first = 'wd:'+request.args.get('obj1')
    second = 'wd:'+request.args.get('obj2')

    try:
        results, checked, frontier = get_search_progress(first, second)
    except:
        return json.dumps({'success': False}), 201, {'ContentType': 'application/json'}

    return jsonify({**create_graph(results), 'paths': results, 'checked': checked, 'frontier': frontier})


@app.route('/poll', methods=['GET'])
@cross_origin()
def poll_raw():
    first = 'wd:'+request.args.get('obj1')
    second = 'wd:'+request.args.get('obj2')

    try:
        results, checked, frontier = get_search_progress(first, second)
    except:
        return json.dumps({'success': False}), 201, {'ContentType': 'application/json'}

    return jsonify({**create_graph_data(results), 'paths': results, 'checked': checked, 'frontier': frontier})


if __name__ == '__main__':
    app.run(debug=True)
