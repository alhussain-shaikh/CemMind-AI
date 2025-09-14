from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='CemMind API')

class SensorReading(BaseModel):
    timestamp: str
    kiln_temp_C: float
    mill_power_kW: float
    raw_feed_rate_tph: float
    AF_rate_percent: float
    clinker_free_lime_percent: float
    blain_surface_cm2g: float
    CO2_emission_kgpt: float

# simple in-memory buffer (POC)
BUFFER = []

@app.post('/ingest')
async def ingest_reading(reading: SensorReading):
    BUFFER.append(reading.dict())
    return {'status':'ok','buffer_len':len(BUFFER)}

@app.get('/latest')
async def latest():
    if not BUFFER:
        return {'status':'empty'}
    return BUFFER[-1]
