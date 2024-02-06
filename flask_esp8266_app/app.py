# Import necessary libraries and modules
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import schedule
import time
import pytz

# Create a Flask web application
app = Flask(__name__)

# Configure the database connection URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://flask_esp:flask_esp@localhost/flask_esp'

# Create a SQLAlchemy database instance
db = SQLAlchemy(app)

# Define a database model for sensor data
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    humidity = db.Column(db.Float)
    temperature = db.Column(db.Float)
    timestamp = db.Column(db.TIMESTAMP, default=lambda: datetime.now(pytz.timezone('Europe/Riga')))

# Define a function to clear all data in the SensorData table
def clear_data():
    with app.app_context():
        # Clear all data in the SensorData table
        SensorData.query.delete()
        db.session.commit()

# Define the main route for rendering the index.html template
@app.route('/')
def index():
    # Retrieve the latest data for esp8266-1 and esp8266-2 sensors
    latest_data_esp8266_1 = SensorData.query.filter_by(name='esp8266-1').order_by(SensorData.timestamp.desc()).first()
    latest_data_esp8266_2 = SensorData.query.filter_by(name='esp8266-2').order_by(SensorData.timestamp.desc()).first()

    # Check if data exists before accessing attributes
    if latest_data_esp8266_1:
        temperature_esp8266_1 = latest_data_esp8266_1.temperature
        humidity_esp8266_1 = latest_data_esp8266_1.humidity
    else:
        temperature_esp8266_1 = None
        humidity_esp8266_1 = None

    if latest_data_esp8266_2:
        temperature_esp8266_2 = latest_data_esp8266_2.temperature
        humidity_esp8266_2 = latest_data_esp8266_2.humidity
    else:
        temperature_esp8266_2 = None
        humidity_esp8266_2 = None

    # Calculate average current temperature and humidity for esp8266-1 and esp8266-2 sensors
    avg_data_temperature = round(((temperature_esp8266_1 or 0) + (temperature_esp8266_2 or 0)) / 2, 1)
    avg_data_humidity = round(((humidity_esp8266_1 or 0) + (humidity_esp8266_2 or 0)) / 2, 1)

    # Render the index.html template with data
    return render_template('index.html',
                           latest_data_esp8266_1=latest_data_esp8266_1,
                           latest_data_esp8266_2=latest_data_esp8266_2,
                           avg_data_temperature=avg_data_temperature,
                           avg_data_humidity=avg_data_humidity)

# Define a route to handle the addition of sensor data via POST requests
@app.route('/add_data', methods=['POST'])
def add_data():
    # Retrieve data from the POST request
    name = request.form.get('name')
    humidity = request.form.get('humidity')
    temperature = request.form.get('temperature')

    # Check if the received data is valid
    if name is not None and humidity is not None and temperature is not None:
        # Create a new SensorData instance and add it to the database
        new_data = SensorData(name=name, humidity=humidity, temperature=temperature)
        db.session.add(new_data)
        db.session.commit()

        # Return a success response
        return "Data added successfully", 200
    else:
        # Return an error response for invalid data
        return "Invalid data", 400

# Schedule a daily task to clear data in the SensorData table at 00:00
schedule.every().day.at("00:00").do(clear_data)

# Define a function to run the scheduled tasks in a separate thread
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduled tasks in a separate thread
if __name__ == '__main__':
    from threading import Thread
    scheduler_thread = Thread(target=run_schedule)
    scheduler_thread.start()

    # Create the SensorData table if it doesn't exist
    with app.app_context():
        db.create_all()

    # Run the Flask application
    app.run(debug=True, host='0.0.0.0')

    # Wait for the scheduler thread to finish
    scheduler_thread.join()
