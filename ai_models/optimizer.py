# Simple optimizer stub: uses heuristic rules to propose setpoints
def optimize_energy(latest):
    actions = []
    # heuristic example
    if latest.get('mill_power_kW',0) > 4300:
        actions.append({'loop':'mill','action':'reduce_feed','amount_percent':1.5})
    if latest.get('AF_rate_percent',0) < 20:
        actions.append({'loop':'fuel','action':'increase_AF','amount_percent':1.0})
    return {'actions':actions,'estimated_savings_percent':1.2}
