from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

DATA_DIRECTORY = 'arduino_data'

# Ensure the data directory exists when the Flask app starts
# This will be on Render's persistent disk
if not os.path.exists(DATA_DIRECTORY):
    os.makedirs(DATA_DIRECTORY)
    print(f"Server: Created data directory {DATA_DIRECTORY}")

@app.route('/')
def index():
    # Flask will serve index.html from the root directory
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # This route serves static files like CSS, JS, and images
    # It will look for files in the root directory relative to the app
    # E.g., for 'style/Home.css', it will look for './style/Home.css'
    return send_from_directory('.', filename)

# Helper function to read the last line from a file
def get_last_line(filepath):
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if lines:
                return lines[-1].strip()
        return None
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error reading last line from {filepath}: {e}")
        return None

@app.route('/api/items')
def get_all_items_latest_data():
    items_data = []
    # Ensure DATA_DIRECTORY is correctly mounted on Render
    if not os.path.exists(DATA_DIRECTORY):
        print(f"Server: Data directory {DATA_DIRECTORY} does not exist!")
        return jsonify({'error': 'Data directory not found'}), 500

    for filename in os.listdir(DATA_DIRECTORY):
        if filename.endswith('.txt'):
            item_id = filename.replace('.txt', '')
            file_path = os.path.join(DATA_DIRECTORY, filename)
            last_line = get_last_line(file_path)
            
            if last_line:
                # We expect "timestamp,value" from sensor_reader.py or sensor_data_upload endpoint
                parts = last_line.split(',', 1) # Split only on the first comma
                timestamp_str = parts[0] if len(parts) > 0 else "Unknown Time"
                value = parts[1] if len(parts) > 1 else "Unknown Value"

                config_file = os.path.join(DATA_DIRECTORY, f"{item_id}_config.json")
                item_name = f"Izdelek {item_id}"
                item_location = f"L {item_id}"
                item_comment = f"Podatki iz senzorja {item_id}"

                if os.path.exists(config_file):
                    try:
                        with open(config_file, 'r') as cf:
                            config_data = json.load(cf)
                            item_name = config_data.get('ime', item_name)
                            item_location = config_data.get('lokacija', item_location)
                            item_comment = config_data.get('komentar', item_comment)
                    except Exception as e:
                        print(f"Error reading config for {item_id}: {e}")

                items_data.append({
                    'id': item_id,
                    'ime': item_name,
                    'kolicina': value, # This is the sensor value
                    'lokacija': item_location,
                    'komentar': item_comment,
                    'timestamp': timestamp_str
                })
    
    return jsonify(items_data)

# NEW ENDPOINT: To receive sensor data from sensor_reader.py
@app.route('/api/sensor_data_upload', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400

    item_id = data.get('id')
    value = data.get('value')
    
    if not item_id or value is None: # Value could be 0, so check for None
        return jsonify({'error': 'Missing "id" or "value" in JSON payload'}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_path = os.path.join(DATA_DIRECTORY, f"{item_id}.txt")
    try:
        # Ensure DATA_DIRECTORY exists, especially on initial deploy or restart
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        with open(file_path, 'a') as f: # 'a' for append mode
            f.write(f"{timestamp},{value}\n") # Write timestamp, value, then a newline
        print(f"Server: Received and saved {item_id}: {value} at {timestamp} to {file_path}")
        return jsonify({'message': f'Data for {item_id} received and saved successfully.'}), 200
    except IOError as e:
        print(f"Server: Error writing to file {file_path}: {e}")
        return jsonify({'error': f'Error writing data to file: {e}'}), 500
    except Exception as e:
        print(f"Server: An unexpected error occurred during data upload: {e}")
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500


# Endpoint to update an item's non-sensor data (Ime, Lokacija, Komentar)
@app.route('/api/items/<string:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    new_ime = data.get('ime')
    new_lokacija = data.get('lokacija')
    new_komentar = data.get('komentar')

    config_file = os.path.join(DATA_DIRECTORY, f"{item_id}_config.json")
    
    current_config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as cf:
                current_config = json.load(cf)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {config_file}. Starting fresh.")
            current_config = {}

    if new_ime is not None:
        current_config['ime'] = new_ime
    if new_lokacija is not None:
        current_config['lokacija'] = new_lokacija
    if new_komentar is not None:
        current_config['komentar'] = new_komentar

    try:
        # Ensure DATA_DIRECTORY exists, especially on initial deploy or restart
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        with open(config_file, 'w') as cf:
            json.dump(current_config, cf, indent=4)
        print(f"Server: Updated config for {item_id}: {current_config}")
        return jsonify({'message': 'Item updated successfully', 'updated_fields': current_config}), 200
    except IOError as e:
        print(f"Server: Error writing config file for ID {item_id}: {e}")
        return jsonify({'error': f'Error writing config file for ID {item_id}: {e}'}), 500
    except Exception as e:
        print(f"Server: An unexpected error occurred during update: {e}")
        return jsonify({'error': f'An unexpected error occurred during update: {e}'}), 500

# Remove the __main__ block as Gunicorn will start the app
# if __name__ == '__main__':
#     print("Starting Flask server...")
#     print(f"Data directory being monitored: {os.path.abspath(DATA_DIRECTORY)}")
#     app.run(debug=True, port=5000)