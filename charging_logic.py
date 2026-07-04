from datetime import datetime

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def calculate_initial_values(battery_capacity, current_battery_percent, target_battery_percent, charger_power, price_per_unit):
    """
    Initial charging session calculations.
    """
    current_energy = battery_capacity * (current_battery_percent / 100.0)
    target_energy = battery_capacity * (target_battery_percent / 100.0)

    units_required = max(target_energy - current_energy, 0)

    if charger_power > 0:
        time_required_hours = units_required / charger_power
    else:
        time_required_hours = 0

    return {
        "current_energy": round(current_energy, 4),
        "target_energy": round(target_energy, 4),
        "units_required": round(units_required, 4),
        "units_left": round(units_required, 4),
        "estimated_total_hours": round(time_required_hours, 4),
        "time_left_hours": round(time_required_hours, 4),
        "amount": 0.0
    }

def update_charging_session(session_row):
    """
    Simulates live charging based on elapsed real time.
    This function recalculates:
    - current battery %
    - units consumed
    - units left
    - amount
    - time left
    - status
    """

    # Convert Decimal/DB values to float safely
    battery_capacity = float(session_row["battery_capacity"])
    start_battery_percent = float(session_row["start_battery_percent"])
    target_battery_percent = float(session_row["target_battery_percent"])
    charger_power = float(session_row["charger_power"])
    price_per_unit = float(session_row["price_per_unit"])

    current_energy_initial = float(session_row["current_energy"])
    target_energy = float(session_row["target_energy"])

    start_time = session_row["start_time"]
    last_status = session_row["status"]

    # If already complete or stopped, return as-is
    if last_status in ("Full", "Stopped"):
        return {
            "current_battery_percent": round(float(session_row["current_battery_percent"]), 2),
            "units_consumed": round(float(session_row["units_consumed"]), 4),
            "units_left": round(float(session_row["units_left"]), 4),
            "amount": round(float(session_row["amount"]), 2),
            "time_left_hours": round(float(session_row["time_left_hours"]), 4),
            "status": last_status,
            "end_time": session_row["end_time"],
            "total_duration_seconds": int(session_row["total_duration_seconds"])
        }

    now = datetime.now()
    elapsed_seconds = max((now - start_time).total_seconds(), 0)
    elapsed_hours = elapsed_seconds / 3600.0

    # Total energy delivered so far = charger_power * elapsed_time
    possible_units_delivered = charger_power * elapsed_hours

    # But don't exceed required units
    units_required = max(target_energy - current_energy_initial, 0)
    units_consumed = min(possible_units_delivered, units_required)

    current_energy_live = current_energy_initial + units_consumed
    current_energy_live = min(current_energy_live, target_energy)

    # Current battery %
    current_battery_percent = (current_energy_live / battery_capacity) * 100 if battery_capacity > 0 else 0
    current_battery_percent = clamp(current_battery_percent, start_battery_percent, target_battery_percent)

    units_left = max(target_energy - current_energy_live, 0)
    amount = units_consumed * price_per_unit

    time_left_hours = (units_left / charger_power) if charger_power > 0 else 0

    status = "Charging"
    end_time = None
    total_duration_seconds = int(elapsed_seconds)

    # Auto complete when target reached
    if current_battery_percent >= target_battery_percent or units_left <= 0.0001:
        current_battery_percent = target_battery_percent
        units_consumed = units_required
        units_left = 0
        amount = units_consumed * price_per_unit
        time_left_hours = 0
        status = "Full"
        end_time = now
        total_duration_seconds = int(elapsed_seconds)

    return {
        "current_battery_percent": round(current_battery_percent, 2),
        "units_consumed": round(units_consumed, 4),
        "units_left": round(units_left, 4),
        "amount": round(amount, 2),
        "time_left_hours": round(time_left_hours, 4),
        "status": status,
        "end_time": end_time,
        "total_duration_seconds": total_duration_seconds
    }

def format_duration(seconds):
    """
    Convert total seconds to HH:MM:SS
    """
    seconds = int(seconds or 0)
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

def format_time_left(hours_float):
    """
    Convert decimal hours into 'Xh Ym Zs'
    """
    total_seconds = int(max(hours_float, 0) * 3600)
    hrs = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hrs}h {mins}m {secs}s"