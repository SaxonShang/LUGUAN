def get_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp_raw = f.read()
    temperature = int(temp_raw) / 1000.0
    return temperature
