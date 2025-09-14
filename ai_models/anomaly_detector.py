import pandas as pd

def detect_drift(df, column='clinker_free_lime_percent', window=30, threshold=0.5):
    if len(df) < window: return None
    recent = df[column].rolling(window).mean().iloc[-1]
    baseline = df[column].rolling(window*3).mean().iloc[-1] if len(df) >= window*3 else df[column].mean()
    delta = recent - baseline
    if abs(delta) > threshold:
        return {'anomaly':True, 'delta':float(delta)}
    return {'anomaly':False, 'delta':float(delta)}
