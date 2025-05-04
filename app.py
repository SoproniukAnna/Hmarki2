from flask import Flask, request, jsonify

app = Flask(__name__)

data = []

@app.route('/', methods=['GET'])
def index():
    return "Hello!"

@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(data)

@app.route('/items', methods=['POST'])
def create_item():
    item = request.json
    data.append(item)
    return jsonify({"message": "Item created"}), 201

@app.route('/items/<int:index>', methods=['PUT'])
def update_item(index):
    if index >= len(data):
        return jsonify({"error": "Item not found"}), 404
    data[index] = request.json
    return jsonify({"message": "Item updated"})

@app.route('/items/<int:index>', methods=['DELETE'])
def delete_item(index):
    if index >= len(data):
        return jsonify({"error": "Item not found"}), 404
    data.pop(index)
    return jsonify({"message": "Item deleted"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
