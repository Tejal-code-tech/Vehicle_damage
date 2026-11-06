from flask import Flask, request

app = Flask(__name__)

data = "Hello"

# GET
@app.route('/get', methods=['GET'])
def get_data():
    return data

# POST
@app.route('/post', methods=['POST'])
def post_data():
    global data
    data = request.form['msg']
    return "Data Added"

# PUT
@app.route('/put', methods=['PUT'])
def put_data():
    global data
    data = request.form['msg']
    return "Data Updated"

app.run()