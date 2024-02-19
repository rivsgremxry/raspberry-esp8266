from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# Create a SQLAlchemy database instance
db = SQLAlchemy()


# Define a database model for sensor data
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    humidity = db.Column(db.Float)
    temperature = db.Column(db.Float)
    timestamp = db.Column(
        db.TIMESTAMP, default=lambda: datetime.now(pytz.timezone("Europe/Riga"))
    )


# Define a database model for scheduler configuration
class SchedulerConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scheduler_enabled = db.Column(db.Boolean)
    schedule_type = db.Column(db.String(20))
    selected_time = db.Column(db.String(5))
