from flask import Flask, jsonify, request, render_template
from prometheus_flask_exporter import PrometheusMetrics
import random
from datetime import datetime

app = Flask(__name__)
metrics = PrometheusMetrics(app)  # Enables Prometheus /metrics endpoint

# Admin Portal Password
ADMIN_PASSWORD = "admin123"

# Initialize 100 Parking Slots by default (Slots 1 to 100)
parking_slots = [
    {"id": i, "status": "Available", "booking": None} for i in range(1, 101)
]

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# POST: Verify Admin Password
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    password = data.get('password', '')
    if password == ADMIN_PASSWORD:
        return jsonify({"authenticated": True, "message": "Login successful"}), 200
    return jsonify({"authenticated": False, "message": "Access Denied: Incorrect Admin Password!"}), 401

# GET: Fetch all parking slots
@app.route('/items', methods=['GET'])
def get_slots():
    return jsonify(parking_slots), 200

# POST: Admin adds a new parking slot
@app.route('/items', methods=['POST'])
def add_slot():
    data = request.get_json()
    slot_id = int(data.get('id', 0))
    
    if slot_id <= 0:
        return jsonify({"message": "Invalid Slot ID!"}), 400

    for slot in parking_slots:
        if slot['id'] == slot_id:
            return jsonify({"message": f"Error: Slot {slot_id} already exists!"}), 400
            
    new_slot = {
        "id": slot_id,
        "status": data.get("status", "Available"),
        "booking": None
    }
    parking_slots.append(new_slot)
    return jsonify({"message": "Slot added successfully", "slot": new_slot}), 201

# DELETE: Admin removes a parking slot
@app.route('/items/<int:slot_id>', methods=['DELETE'])
def delete_slot(slot_id):
    global parking_slots
    parking_slots = [slot for slot in parking_slots if slot['id'] != slot_id]
    return jsonify({"message": f"Slot {slot_id} removed successfully"}), 200

# POST: User registers vehicle -> Allocate Random Available Slot & Token
@app.route('/book', methods=['POST'])
def book_slot():
    data = request.get_json()
    owner_name = data.get('owner_name', '').strip()
    vehicle_no = data.get('vehicle_no', '').strip().upper()
    vehicle_type = data.get('vehicle_type', '4-Wheeler')
    duration = int(data.get('duration', 1))

    if not owner_name or not vehicle_no or duration <= 0:
        return jsonify({"message": "Please fill all details with a valid duration!"}), 400

    # Prevent duplicate active booking for the same vehicle
    for slot in parking_slots:
        if slot['status'] == 'Occupied' and slot['booking'] and slot['booking']['vehicle_no'] == vehicle_no:
            return jsonify({"message": f"Vehicle {vehicle_no} is already parked in Slot {slot['id']}!"}), 400

    # Find all available slots
    available_slots = [slot for slot in parking_slots if slot['status'] == 'Available']
    if not available_slots:
        return jsonify({"message": "Sorry! Parking is Full. No slots available right now."}), 400

    # Pick a random available slot out of the 100 slots
    chosen_slot = random.choice(available_slots)

    # Generate a unique Token ID
    existing_tokens = {s['booking']['token'] for s in parking_slots if s.get('booking')}
    while True:
        token = f"TKN-{random.randint(1000, 9999)}"
        if token not in existing_tokens:
            break

    # Calculate Parking Fee (₹20/hr for 2-Wheeler, ₹40/hr for 4-Wheeler)
    rate_per_hour = 20 if vehicle_type == '2-Wheeler' else 40
    fee = duration * rate_per_hour

    booking_details = {
        "token": token,
        "owner_name": owner_name,
        "vehicle_no": vehicle_no,
        "vehicle_type": vehicle_type,
        "duration": duration,
        "fee": fee,
        "booked_at": datetime.now().strftime("%I:%M %p")
    }

    chosen_slot['status'] = 'Occupied'
    chosen_slot['booking'] = booking_details

    return jsonify({
        "message": f"Slot {chosen_slot['id']} allocated successfully!",
        "slot_id": chosen_slot['id'],
        "booking": booking_details
    }), 201

# POST: User clicks "Leave Slot" OR Admin forces release
@app.route('/leave', methods=['POST'])
def leave_slot():
    data = request.get_json()
    identifier = str(data.get('identifier', '')).strip().upper()
    slot_id = data.get('slot_id')

    for slot in parking_slots:
        if slot['status'] == 'Occupied':
            b = slot.get('booking') or {}
            if (slot_id and slot['id'] == int(slot_id)) or \
               (identifier and (b.get('token') == identifier or b.get('vehicle_no') == identifier)):
                released_id = slot['id']
                slot['status'] = 'Available'
                slot['booking'] = None
                return jsonify({
                    "message": f"Slot {released_id} is now Available for other users!",
                    "slot_id": released_id
                }), 200

    return jsonify({"message": "No active booking found with that Token or Vehicle Number!"}), 404

# GET: Health check endpoint (Required for CI/CD unit tests)
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)