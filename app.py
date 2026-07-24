from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# 1. Mock Data: Our temporary database of delivery trucks
fleet_data = [
    {"truck_id": "T01", "driver": "Rahul", "status": "In Transit", "fuel_efficiency": "85%", "destination": "Mumbai"},
    {"truck_id": "T02", "driver": "Ananya", "status": "Delivered", "fuel_efficiency": "92%", "destination": "Bangalore"},
    {"truck_id": "T03", "driver": "Vikram", "status": "Delayed", "fuel_efficiency": "78%", "destination": "Delhi"}
]

# 2. Home Route: Tells Flask to serve our visual index.html webpage
@app.route('/')
def home():
    return render_template('index.html')

# 3. Endpoint to send our fleet data to the front-end web page
@app.route('/api/fleet', methods=['GET'])
def get_fleet():
    return jsonify(fleet_data)

# 4. Optimization Logic: The math engine that calculates the best route
@app.route('/api/optimize', methods=['POST'])
def optimize_route():
    # Receive data from the user (Frontend)
    data = request.json
    distance = float(data.get('distance', 0))
    traffic_level = data.get('traffic', 'Medium') # Low, Medium, High
    
    # Simple logic formula: High traffic adds a time penalty
    traffic_multiplier = 1.0
    if traffic_level == "High":
        traffic_multiplier = 1.5
    elif traffic_level == "Low":
        traffic_multiplier = 0.8
        
    # Standard formula: Time = (Distance / Average Speed) * Traffic Modifier
    estimated_time = (distance / 60) * traffic_multiplier
    
    # Return the optimized answer back to the frontend
    return jsonify({
        "estimated_hours": round(estimated_time, 2),
        "recommended_speed": "55 km/h" if traffic_level == "High" else "65 km/h"
    })

if __name__ == '__main__':
    app.run(debug=True)