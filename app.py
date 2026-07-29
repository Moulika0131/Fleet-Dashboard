"""
Cloud Fleet Analytics Dashboard - Backend API (v2)
----------------------------------------------------
Upgrades from v1:
  1. Real persistent storage using SQLite (instead of a hardcoded list)
  2. Real shortest-path routing using Dijkstra's algorithm
     (instead of a flat distance/traffic formula)
  3. Input validation on all endpoints
"""

from flask import Flask, jsonify, request
import sqlite3
import heapq
import os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'fleet.db')


# ============================================================
# DATABASE LAYER
# ============================================================
def get_db_connection():
    """Opens a connection to the SQLite database file."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, like a dict
    return conn


def init_db():
    """Creates the trucks table if it doesn't exist yet, and seeds
    it with sample data the first time the app runs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trucks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            truck_id TEXT NOT NULL,
            driver TEXT NOT NULL,
            status TEXT NOT NULL,
            fuel_efficiency REAL,
            destination TEXT,
            distance_km REAL
        )
    ''')

    cursor.execute('SELECT COUNT(*) FROM trucks')
    if cursor.fetchone()[0] == 0:
        seed_trucks = [
            ('TRK-101', 'Ravi Kumar', 'On Route', 8.5, 'Coimbatore', 500),
            ('TRK-102', 'Anitha S', 'Idle', 7.2, 'Kochi', 200),
            ('TRK-103', 'Suresh P', 'On Route', 9.0, 'Bangalore', 350),
        ]
        cursor.executemany(
            '''INSERT INTO trucks
               (truck_id, driver, status, fuel_efficiency, destination, distance_km)
               VALUES (?, ?, ?, ?, ?, ?)''',
            seed_trucks
        )

    conn.commit()
    conn.close()


# ============================================================
# ROUTE NETWORK (used by the optimization algorithm)
# Format: city -> list of (neighbor_city, distance_km)
# ============================================================
ROUTE_GRAPH = {
    "Chennai":    [("Coimbatore", 500), ("Bangalore", 350)],
    "Coimbatore": [("Chennai", 500), ("Kochi", 200), ("Bangalore", 360)],
    "Bangalore":  [("Chennai", 350), ("Kochi", 460), ("Coimbatore", 360)],
    "Kochi":      [("Coimbatore", 200), ("Bangalore", 460)],
}

TRAFFIC_MULTIPLIER = {
    "Low": 0.8,
    "Medium": 1.0,
    "High": 1.5,
}


def dijkstra_shortest_path(graph, start, end):
    """
    Dijkstra's shortest-path algorithm.

    Given a graph of cities connected by roads (with distances as
    'weights'), this finds the route between `start` and `end` with
    the smallest total distance -- exactly like Google Maps picking
    the shortest driving route among several possible paths.

    Returns: (total_distance_km, [city1, city2, ...]) or (None, [])
             if no path exists.
    """
    if start not in graph or end not in graph:
        return None, []

    # Min-heap of (distance_so_far, current_city, path_taken_so_far)
    queue = [(0, start, [])]
    visited = set()

    while queue:
        cost, node, path = heapq.heappop(queue)

        if node in visited:
            continue
        visited.add(node)
        path = path + [node]

        if node == end:
            return cost, path

        for neighbor, weight in graph.get(node, []):
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path))

    return None, []  # end city unreachable from start


# ============================================================
# API ROUTES
# ============================================================
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Fleet Analytics API v2 is running"})


@app.route('/api/fleet', methods=['GET'])
def get_fleet():
    """Returns every truck currently stored in the database."""
    conn = get_db_connection()
    trucks = conn.execute('SELECT * FROM trucks').fetchall()
    conn.close()
    return jsonify([dict(row) for row in trucks])


@app.route('/api/fleet', methods=['POST'])
def add_truck():
    """Adds a new truck record to the database."""
    data = request.get_json()
    required = ['truck_id', 'driver', 'status', 'fuel_efficiency', 'destination', 'distance_km']

    if not data or not all(field in data for field in required):
        return jsonify({"error": f"Required fields: {required}"}), 400

    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO trucks
           (truck_id, driver, status, fuel_efficiency, destination, distance_km)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (data['truck_id'], data['driver'], data['status'],
         data['fuel_efficiency'], data['destination'], data['distance_km'])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Truck added successfully"}), 201


@app.route('/api/fleet/<int:truck_id>', methods=['DELETE'])
def delete_truck(truck_id):
    """Removes a truck record by its database id."""
    conn = get_db_connection()
    result = conn.execute('DELETE FROM trucks WHERE id = ?', (truck_id,))
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        return jsonify({"error": "truck not found"}), 404
    return jsonify({"message": "truck deleted"})


@app.route('/api/optimize', methods=['POST'])
def optimize_route():
    """
    Given a start city, end city, and traffic condition, this returns
    the shortest route (via Dijkstra) and an estimated travel time
    adjusted for traffic.
    """
    data = request.get_json()
    if not data or 'start' not in data or 'end' not in data:
        return jsonify({"error": "start and end cities are required"}), 400

    start = data['start']
    end = data['end']
    traffic = data.get('traffic', 'Medium')

    if traffic not in TRAFFIC_MULTIPLIER:
        return jsonify({"error": "traffic must be one of: Low, Medium, High"}), 400

    distance, path = dijkstra_shortest_path(ROUTE_GRAPH, start, end)

    if distance is None:
        return jsonify({"error": f"No route found between {start} and {end}"}), 404

    avg_speed_kmph = 60
    estimated_time_hr = (distance / avg_speed_kmph) * TRAFFIC_MULTIPLIER[traffic]

    return jsonify({
        "start": start,
        "end": end,
        "shortest_path": path,
        "total_distance_km": distance,
        "traffic_condition": traffic,
        "estimated_time_hr": round(estimated_time_hr, 2)
    })


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
