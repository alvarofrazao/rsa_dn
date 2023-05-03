from flask import Flask, jsonify, render_template
import json

app = Flask(__name__)


# Define route to return object data as JSON
@app.route('/objects.json')
def get_objects():
    with open('objects.json', 'r') as f:
        objects = json.load(f)
    return jsonify(objects)

# Define route to serve index.html template
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
