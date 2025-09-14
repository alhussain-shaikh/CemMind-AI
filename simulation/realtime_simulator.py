import time
import random
import json
from datetime import datetime

def generate_sensor_reading():
    return {
        "timestamp": datetime.utcnow().isoformat()+'Z',
        "kiln_temp_C": round(random.gauss(1450, 15), 3),
        "mill_power_kW": round(random.gauss(4200, 150), 3),
        "raw_feed_rate_tph": round(random.gauss(250, 10), 3),
        "AF_rate_percent": round(max(0, min(40, random.gauss(15, 5))), 3),
        "clinker_free_lime_percent": round(random.gauss(1.5, 0.3), 3),
        "blain_surface_cm2g": round(random.gauss(3400, 100), 3),
        "CO2_emission_kgpt": round(random.gauss(850, 30), 3)
    }

def run_realtime_stream(iterations=60, delay=1):
    """Run a simple console streamer that prints JSON lines - can be piped into Pub/Sub or a consumer."""
    for i in range(iterations):
        reading = generate_sensor_reading()
        print(json.dumps(reading))
        time.sleep(delay)

if __name__ == '__main__':
    run_realtime_stream()
