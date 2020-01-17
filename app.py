from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["DEBUG"] = True


@app.route('/')
def hello():

    return "Hello World!"


@app.route('/entry', methods=['GET'])
def login():
    wiki_obj = request.args.get('object')
    print(wiki_obj)


if __name__ == '__main__':
    app.run()
