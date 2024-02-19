# Import necessary libraries and modules
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import schedule
import time
import pytz
from threading import Thread

# Create a Flask web application
app = Flask(__name__)

# Configure the database connection URI
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://flask_esp:flask_esp@localhost/flask_esp"
)

# Create a SQLAlchemy database instance
db = SQLAlchemy(app)

# Shared variables for scheduler configuration
scheduler_enabled = False
schedule_type = "daily"
selected_time = "00:00"


# Define a database model for sensor data
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    humidity = db.Column(db.Float)
    temperature = db.Column(db.Float)
    timestamp = db.Column(
        db.TIMESTAMP, default=lambda: datetime.now(pytz.timezone("Europe/Riga"))
    )


# Define a function to clear all data in the SensorData table
def clear_data():
    with app.app_context():
        # Clear all data in the SensorData table
        SensorData.query.delete()
        db.session.commit()


# Define a function to configure and start the scheduled tasks
def configure_schedule():
    global scheduler_enabled, schedule_type, selected_time

    while True:
        if scheduler_enabled:
            if schedule_type == "daily":
                schedule.every().day.at(selected_time).do(clear_data)
            elif schedule_type == "weekly":
                schedule.every().week.at(selected_time).do(clear_data)

            # Reset scheduler configuration
            scheduler_enabled = False

        schedule.run_pending()
        time.sleep(1)


# Define the main route for rendering the index.html template
@app.route("/")
def index():
    # Get a list of unique sensor names from the database
    sensor_names = db.session.query(SensorData.name).distinct().all()

    # Initializing lists for storing temperature and humidity data
    sensor_data_list = []

    # Process each sensor
    for sensor_name in sensor_names:
        # Get the latest data for each sensor
        latest_data = (
            SensorData.query.filter_by(name=sensor_name[0])
            .order_by(SensorData.timestamp.desc())
            .first()
        )

        # If the data is available, add it to the lists
        if latest_data:
            # Define a new name for each sensor
            display_name = (
                "Corridor"
                if sensor_name[0] == "esp8266-1"
                else "Bedroom" if sensor_name[0] == "esp8266-2" else sensor_name[0]
            )

            sensor_data_list.append(
                {
                    "name": display_name,
                    "temperature": latest_data.temperature,
                    "humidity": latest_data.humidity,
                    "timestamp": (
                        latest_data.timestamp.strftime("%H:%M")
                        if latest_data.timestamp
                        else "N/A"
                    ),
                }
            )

    # Calculate average values only for active sensors
    avg_data_temperature = (
        round(
            sum(data["temperature"] for data in sensor_data_list)
            / len(sensor_data_list),
            1,
        )
        if sensor_data_list
        else None
    )
    avg_data_humidity = (
        round(
            sum(data["humidity"] for data in sensor_data_list) / len(sensor_data_list),
            1,
        )
        if sensor_data_list
        else None
    )

    # Render the index.html template with data
    return render_template(
        "index.html",
        sensor_data_list=sensor_data_list,
        avg_data_temperature=avg_data_temperature,
        avg_data_humidity=avg_data_humidity,
    )


# Define a route to handle the addition of sensor data via POST requests
@app.route("/add_data", methods=["POST"])
def add_data():
    # Retrieve data from the POST request
    name = request.form.get("name")
    humidity = request.form.get("humidity")
    temperature = request.form.get("temperature")

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


# Define a route to configure the scheduler
@app.route("/configure_schedule", methods=["GET", "POST"])
def configure_schedule_route():
    global scheduler_enabled, schedule_type, selected_time

    if request.method == "POST":
        # Retrieve form data
        toggle_status = request.form.get("toggle_status")
        schedule_type = request.form.get("schedule_type")
        selected_time = request.form.get("selected_time")

        # Update scheduler settings based on form data
        scheduler_enabled = toggle_status == "on"

    # Render the configuration template
    return render_template("configure_schedule.html")


# Start the scheduled tasks in a separate thread
if __name__ == "__main__":
    # Create the SensorData table if it doesn't exist
    with app.app_context():
        db.create_all()

    # Configure and start the scheduled tasks
    scheduler_thread = Thread(target=configure_schedule)
    scheduler_thread.start()

    # Run the Flask application
    app.run(debug=True, host="0.0.0.0")

    # Wait for the scheduler thread to finish
    scheduler_thread.join()
