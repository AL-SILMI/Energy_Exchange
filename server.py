from flask import Flask, jsonify, request
from flask_cors import CORS

# Initialize the Flask application
app = Flask(__name__)

# A more robust CORS setup for local development.
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS", "DELETE"],
    "allow_headers": ["Content-Type"]
}})

# --- MOCK DATABASE ---
users = {}
energy_listings = [
    { "id": 1, "producer": 'Solar Farm A', "type": 'Solar', "amount": 150, "price": 0.12, "location": 'North District', "source": "Renewable", "duration": 24 },
    { "id": 2, "producer": 'Wind Turbine #3', "type": 'Wind', "amount": 300, "price": 0.10, "location": 'West Hills', "source": "Renewable", "duration": 48 },
    { "id": 3, "producer": 'Rooftop Solar B', "type": 'Solar', "amount": 25, "price": 0.15, "location": 'City Center', "source": "Renewable", "duration": 12 }
]
transactions = []
next_listing_id = 4
next_transaction_id = 1

# --- API ENDPOINTS ---

@app.route('/')
def home():
    return "Energy Exchange Backend is running!"

# In server.py, replace the existing login function

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    name = data.get('name') # New: Get the name from the request

    print(f"Login attempt for: {email}")
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # If user is new, store their full info
    if email not in users:
        users[email] = {'email': email, 'role': role, 'name': name}
    
    # If user exists, ensure their name is stored (for logins after signup)
    if 'name' not in users[email] or not users[email]['name']:
        users[email]['name'] = name

    return jsonify({"message": "Login successful!", "user": users[email]})

@app.route('/api/listings', methods=['GET'])
def get_listings():
    # New: Add filtering logic
    query_params = request.args
    filtered_listings = energy_listings

    # Filter by energy type (Solar, Wind, etc.)
    energy_type = query_params.get('type')
    if energy_type and energy_type != 'all':
        filtered_listings = [l for l in filtered_listings if l['type'].lower() == energy_type.lower()]

    # Filter by source (Renewable/Non-Renewable)
    source = query_params.get('source')
    if source and source != 'all':
        filtered_listings = [l for l in filtered_listings if l['source'].lower() == source.lower()]
    
    print(f"GET /api/listings request received. Returning {len(filtered_listings)} listings.")
    return jsonify(filtered_listings)

@app.route('/api/post-energy', methods=['POST'])
def post_energy():
    global next_listing_id
    data = request.get_json()
    print(f"POST /api/post-energy request received with data: {data}")
    
    # Updated: Check for new fields
    if not all(k in data for k in ['type', 'amount', 'price', 'user_email', 'source', 'duration']):
        return jsonify({"error": "Missing data"}), 400
    
    producer_name = data['user_email'].split('@')[0]
    new_listing = {
        "id": next_listing_id,
        "producer": producer_name,
        "type": data['type'],
        "amount": float(data['amount']),
        "price": float(data['price']),
        "source": data['source'],
        "duration": int(data['duration']),
        "location": "User Location"
    }
    energy_listings.append(new_listing)
    next_listing_id += 1
    return jsonify({"message": "Listing created successfully!", "listing": new_listing}), 201

@app.route('/api/buy-energy', methods=['POST'])
def buy_energy():
    global next_transaction_id
    data = request.get_json()
    listing_id = data.get('listing_id')
    user_email = data.get('user_email')
    if not listing_id or not user_email:
        return jsonify({"error": "Listing ID and User Email are required"}), 400
    
    listing = next((item for item in energy_listings if item["id"] == listing_id), None)
    if not listing:
        return jsonify({"error": "Listing not found"}), 404
    
    amount_to_buy = 10
    if listing['amount'] >= amount_to_buy:
        listing['amount'] -= amount_to_buy
        new_transaction = {
            "id": next_transaction_id, "buyer_email": user_email, "producer": listing['producer'],
            "amount": amount_to_buy, "cost": round(amount_to_buy * listing['price'], 2), "type": listing['type']
        }
        transactions.append(new_transaction)
        next_transaction_id += 1
        return jsonify({"message": f"Successfully purchased {amount_to_buy} kWh!", "listing": listing})
    else:
        return jsonify({"error": "Not enough energy available in this listing"}), 400

@app.route('/api/delete-energy/<int:listing_id>', methods=['DELETE'])
def delete_energy(listing_id):
    global energy_listings
    listing_to_delete = next((item for item in energy_listings if item["id"] == listing_id), None)
    if not listing_to_delete:
        return jsonify({"error": "Listing not found"}), 404
    
    data = request.get_json()
    user_email = data.get('user_email')
    producer_name = user_email.split('@')[0] if user_email else None

    if listing_to_delete['producer'] != producer_name:
        return jsonify({"error": "You are not authorized to delete this listing"}), 403

    energy_listings = [item for item in energy_listings if item["id"] != listing_id]
    return jsonify({"message": "Listing deleted successfully"})

@app.route('/api/my-energy', methods=['POST'])
def get_my_energy():
    data = request.get_json()
    user_email = data.get('user_email')
    if not user_email:
        return jsonify({"error": "User email is required"}), 400
    user_transactions = [t for t in transactions if t['buyer_email'] == user_email]
    return jsonify(user_transactions)

# --- RUN THE SERVER ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
