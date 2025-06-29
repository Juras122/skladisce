import serial
import time
import os
from datetime import datetime
import requests # <--- NEW: Import requests library

# --- Configuration ---
SERIAL_PORT = 'COM3'   # Replace with your Arduino's serial port (remains local)
BAUD_RATE = 9600       # Must match your Arduino sketch's baud rate

# IMPORTANT: This will be your Render app's URL. You'll get this AFTER deploying to Render.
# For now, put a placeholder. You'll update this once your Render app is live.
RENDER_APP_URL = 'YOUR_RENDER_APP_URL_HERE' # e.g., 'https://skladi-app.onrender.com'


def setup_serial():
    """Establishes and returns a serial connection."""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
        time.sleep(2)  # Give some time for the serial connection to establish
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        print("Please check if the Arduino is connected and the port is correct.")
        return None

def process_data(line):
    """Parses a line of data and returns a dictionary of IDs and values."""
    data = {}
    parts = line.strip().split(',')
    for part in parts:
        if ':' in part:
            id_val = part.split(':')
            if len(id_val) == 2:
                data[id_val[0]] = id_val[1]
    return data

def send_data_to_render(data):
    """Sends each ID's value to the remote Flask API on Render."""
    for id_name, value in data.items():
        payload = {
            'id': id_name,
            'value': value,
            # 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # You can send timestamp from here if needed
        }
        try:
            # The API endpoint on your Flask server to receive sensor data
            response = requests.post(f"{RENDER_APP_URL}/api/sensor_data_upload", json=payload)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            print(f"Sent {id_name}: {value} to Render. Response: {response.status_code} - {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data for {id_name} to Render: {e}")

def main():
    ser = setup_serial()
    if not ser:
        return

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if line: # Ensure the line is not empty
                    print(f"Received: {line}")
                    parsed_data = process_data(line)
                    if parsed_data:
                        send_data_to_render(parsed_data) # Send data to the remote server
            time.sleep(0.1) # Small delay to prevent busy-waiting
    except KeyboardInterrupt:
        print("\nExiting program.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    # Ensure you've replaced 'YOUR_RENDER_APP_URL_HERE' before running!
    if RENDER_APP_URL == 'YOUR_RENDER_APP_URL_HERE':
        print("WARNING: RENDER_APP_URL is not set. Please update sensor_reader.py with your Render app's URL.")
    main()