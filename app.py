from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)  # Enables Prometheus /metrics endpoint

# In-memory database simulation
parking_slots = [
    {"id": 1, "status": "Available"},
    {"id": 2, "status": "Occupied"}
]

@app.route('/items', methods=['GET'])
def get_slots():
    return jsonify(parking_slots), 200

@app.route('/items', methods=['POST'])
def add_slot():
    new_slot = request.get_json()
    parking_slots.append(new_slot)
    return jsonify({"message": "Slot added", "slot": new_slot}), 201

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)