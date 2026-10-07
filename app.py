from flask import Flask, jsonify, request, render_template
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)  # Enables Prometheus /metrics endpoint

# In-memory database simulation
parking_slots = [
    {"id": 1, "status": "Available"},
    {"id": 2, "status": "Occupied"}
]

# Serve the HTML Frontend Dashboard
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# GET: Fetch all parking slots
@app.route('/items', methods=['GET'])
def get_slots():
    return jsonify(parking_slots), 200

# POST: Add a new parking slot (with duplicate prevention)
@app.route('/items', methods=['POST'])
def add_slot():
    new_slot = request.get_json()
    
    # Check if the slot ID already exists
    for slot in parking_slots:
        if slot['id'] == new_slot['id']:
            return jsonify({"message": f"Error: Slot {new_slot['id']} already exists!"}), 400
            
    parking_slots.append(new_slot)
    return jsonify({"message": "Slot added", "slot": new_slot}), 201

# DELETE: Remove a parking slot by its ID
@app.route('/items/<int:slot_id>', methods=['DELETE'])
def delete_slot(slot_id):
    global parking_slots
    # Keep only the slots that DO NOT match the ID we want to delete
    parking_slots = [slot for slot in parking_slots if slot['id'] != slot_id]
    return jsonify({"message": f"Slot {slot_id} removed successfully"}), 200

# GET: Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)