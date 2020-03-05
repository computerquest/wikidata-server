from flask import Flask, request, jsonify
import re
from search import launch_search, get_search_progress
from utility import create_graph, request_entity
import flask
from flask_cors import CORS, cross_origin

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
        return 400

    if re.search(r'Q\d*$', first) is not None and re.search(r'Q\d*$', second) is not None:
        print('starting the search')
        launch_search('wd:'+first, 'wd:'+second)
        return 200
    else:
        return 400


@app.route('/poll', methods=['GET'])
@cross_origin()
def poll():
    first = 'wd:'+request.args.get('obj1')
    second = 'wd:'+request.args.get('obj2')

    try:
        results = get_search_progress(first, second)
    except:
        return 201

    return jsonify(create_graph(results))


if __name__ == '__main__':
    app.run(debug=True)
