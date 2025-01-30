import random

def get_temperature():
    """Simulates getting temperature from a sensor."""
    return round(random.uniform(20, 35), 2)  # Fake sensor data

def get_humidity():
    """Simulates getting humidity from a sensor."""
    return round(random.uniform(40, 80), 2)  # Fake sensor data
