from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mysqldb import MySQL
from datetime import datetime
from functools import wraps

from config import Config
from utils.charging_logic import (
    calculate_initial_values,
    update_charging_session,
    format_duration,
    format_time_left
)

app = Flask(__name__)
app.config.from_object(Config)
mysql = MySQL(app)


# =========================================================
# HELPERS
# =========================================================

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please login as admin first.", "warning")
            return redirect(url_for("admin_login"))
        return func(*args, **kwargs)
    return wrapper

def get_station_settings():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT station_name, station_location, support_number, gst_number
        FROM station_settings
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()

    if row:
        return row

    return {
        "station_name": "EV Charge Station",
        "station_location": "Warangal, Telangana",
        "support_number": "+91 98765 43210",
        "gst_number": "EV-CHARGE-001"
    }


def seed_sample_sessions():
    """
    Insert sample sessions only if charging_sessions is empty.
    """
    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM charging_sessions")
    total = cur.fetchone()["total"]
    if total > 0:
        cur.close()
        return

    # make sure vehicles exist
    cur.execute("SELECT id, vehicle_name, battery_capacity FROM vehicles ORDER BY id LIMIT 3")
    vehicles = cur.fetchall()

    if not vehicles:
        cur.close()
        return

    now = datetime.now()

    sample_rows = [
        # vehicle_index, start%, current%, target%, power, price, units_consumed, units_left, amount, status, hours_ago_start
        (0, 20, 80, 80, 20, 12, 30.0, 0.0, 360.0, "Full", 10),
        (1, 35, 90, 90, 15, 12, 24.5, 0.0, 294.0, "Full", 8),
        (2, 10, 60, 85, 25, 12, 30.0, 15.0, 360.0, "Charging", 2),
        (0, 40, 70, 100, 10, 12, 15.0, 15.0, 180.0, "Charging", 1),
        (1, 50, 75, 100, 7, 12, 11.0, 11.0, 132.0, "Stopped", 5),
        (2, 15, 55, 75, 18, 12, 24.0, 12.0, 288.0, "Stopped", 7),
        (0, 25, 85, 85, 30, 12, 30.0, 0.0, 360.0, "Full", 12),
        (1, 60, 95, 95, 11, 12, 15.5, 0.0, 186.0, "Full", 14),
        (2, 30, 78, 90, 22, 12, 28.8, 7.2, 345.6, "Charging", 3),
        (0, 45, 65, 80, 9, 12, 10.0, 7.5, 120.0, "Stopped", 4),
    ]

    for row in sample_rows:
        v_idx, start_pct, current_pct, target_pct, charger_power, price, units_consumed, units_left, amount, status, hours_ago = row
        vehicle = vehicles[v_idx % len(vehicles)]
        battery_capacity = float(vehicle["battery_capacity"])

        current_energy = battery_capacity * (start_pct / 100.0)
        target_energy = battery_capacity * (target_pct / 100.0)
        units_required = max(target_energy - current_energy, 0)
        estimated_total_hours = round(units_required / charger_power, 4) if charger_power > 0 else 0
        time_left_hours = round(units_left / charger_power, 4) if charger_power > 0 else 0

        start_time = now.replace(microsecond=0)
        start_time = start_time.replace(hour=max(0, start_time.hour - hours_ago))
        end_time = None if status == "Charging" else now

        cur.execute("""
            INSERT INTO charging_sessions (
                vehicle_id, vehicle_name, battery_capacity,
                start_battery_percent, current_battery_percent, target_battery_percent,
                charger_power, price_per_unit,
                current_energy, target_energy,
                units_required, units_consumed, units_left,
                amount, estimated_total_hours, time_left_hours,
                total_duration_seconds, status, start_time, end_time, last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vehicle["id"],
            vehicle["vehicle_name"],
            battery_capacity,
            start_pct,
            current_pct,
            target_pct,
            charger_power,
            price,
            current_energy,
            target_energy,
            units_required,
            units_consumed,
            units_left,
            amount,
            estimated_total_hours,
            time_left_hours,
            hours_ago * 3600,
            status,
            start_time,
            end_time,
            now
        ))

    mysql.connection.commit()
    cur.close()


def get_session_by_id(session_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT cs.*, v.owner_name, v.mobile_number, v.vehicle_id AS original_vehicle_id
        FROM charging_sessions cs
        JOIN vehicles v ON cs.vehicle_id = v.id
        WHERE cs.id = %s
    """, (session_id,))
    row = cur.fetchone()
    cur.close()
    return row


def persist_live_session_update(session_id):
    session_row = get_session_by_id(session_id)
    if not session_row:
        return None

    updated = update_charging_session(session_row)

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE charging_sessions
        SET current_battery_percent = %s,
            units_consumed = %s,
            units_left = %s,
            amount = %s,
            time_left_hours = %s,
            status = %s,
            end_time = %s,
            total_duration_seconds = %s,
            last_updated = %s
        WHERE id = %s
    """, (
        updated["current_battery_percent"],
        updated["units_consumed"],
        updated["units_left"],
        updated["amount"],
        updated["time_left_hours"],
        updated["status"],
        updated["end_time"],
        updated["total_duration_seconds"],
        datetime.now(),
        session_id
    ))
    mysql.connection.commit()
    cur.close()

    return get_session_by_id(session_id)


def serialize_session(session_row):
    if not session_row:
        return None

    return {
        "id": session_row["id"],
        "vehicle_name": session_row["vehicle_name"],
        "vehicle_id": session_row["original_vehicle_id"],
        "owner_name": session_row.get("owner_name"),
        "mobile_number": session_row.get("mobile_number"),
        "battery_capacity": float(session_row["battery_capacity"]),
        "start_battery_percent": float(session_row["start_battery_percent"]),
        "current_battery_percent": float(session_row["current_battery_percent"]),
        "target_battery_percent": float(session_row["target_battery_percent"]),
        "charger_power": float(session_row["charger_power"]),
        "price_per_unit": float(session_row["price_per_unit"]),
        "current_energy": float(session_row["current_energy"]),
        "target_energy": float(session_row["target_energy"]),
        "units_required": float(session_row["units_required"]),
        "units_consumed": float(session_row["units_consumed"]),
        "units_left": float(session_row["units_left"]),
        "amount": float(session_row["amount"]),
        "estimated_total_hours": float(session_row["estimated_total_hours"]),
        "time_left_hours": float(session_row["time_left_hours"]),
        "status": session_row["status"],
        "start_time": session_row["start_time"].strftime("%Y-%m-%d %H:%M:%S") if session_row["start_time"] else "",
        "end_time": session_row["end_time"].strftime("%Y-%m-%d %H:%M:%S") if session_row["end_time"] else "",
        "last_updated": session_row["last_updated"].strftime("%Y-%m-%d %H:%M:%S") if session_row["last_updated"] else "",
        "duration_text": format_duration(session_row["total_duration_seconds"]),
        "time_left_text": format_time_left(float(session_row["time_left_hours"]))
    }


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start-charging", methods=["GET", "POST"])
def start_charging():
    default_price = get_price_from_db()

    if request.method == "POST":
        vehicle_name = request.form.get("vehicle_name", "").strip()
        vehicle_unique_id = request.form.get("vehicle_id", "").strip()
        owner_name = request.form.get("owner_name", "").strip()
        mobile_number = request.form.get("mobile_number", "").strip()

        battery_capacity = request.form.get("battery_capacity", type=float)
        current_battery_percent = request.form.get("current_battery_percent", type=float)
        target_battery_percent = request.form.get("target_battery_percent", type=float)
        charger_power = request.form.get("charger_power", type=float)
        price_per_unit = request.form.get("price_per_unit", type=float)

        if not vehicle_name or not vehicle_unique_id:
            flash("Vehicle name and vehicle ID are required.", "danger")
            return redirect(url_for("start_charging"))

        if battery_capacity is None or battery_capacity <= 0:
            flash("Battery capacity must be greater than 0.", "danger")
            return redirect(url_for("start_charging"))

        if charger_power is None or charger_power <= 0:
            flash("Charger power must be greater than 0.", "danger")
            return redirect(url_for("start_charging"))

        if current_battery_percent is None or target_battery_percent is None:
            flash("Battery percentages are required.", "danger")
            return redirect(url_for("start_charging"))

        if current_battery_percent < 0 or current_battery_percent > 100:
            flash("Current battery % must be between 0 and 100.", "danger")
            return redirect(url_for("start_charging"))

        if target_battery_percent < 0 or target_battery_percent > 100:
            flash("Target battery % must be between 0 and 100.", "danger")
            return redirect(url_for("start_charging"))

        if target_battery_percent <= current_battery_percent:
            flash("Target battery % must be greater than current battery %.", "danger")
            return redirect(url_for("start_charging"))

        if price_per_unit is None or price_per_unit <= 0:
            flash("Price per unit must be greater than 0.", "danger")
            return redirect(url_for("start_charging"))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_unique_id,))
        vehicle = cur.fetchone()

        if vehicle:
            vehicle_db_id = vehicle["id"]
            cur.execute("""
                UPDATE vehicles
                SET vehicle_name=%s, owner_name=%s, mobile_number=%s, battery_capacity=%s
                WHERE id=%s
            """, (vehicle_name, owner_name, mobile_number, battery_capacity, vehicle_db_id))
        else:
            cur.execute("""
                INSERT INTO vehicles (vehicle_name, vehicle_id, owner_name, mobile_number, battery_capacity)
                VALUES (%s, %s, %s, %s, %s)
            """, (vehicle_name, vehicle_unique_id, owner_name, mobile_number, battery_capacity))
            vehicle_db_id = cur.lastrowid

        initial = calculate_initial_values(
            battery_capacity=battery_capacity,
            current_battery_percent=current_battery_percent,
            target_battery_percent=target_battery_percent,
            charger_power=charger_power,
            price_per_unit=price_per_unit
        )

        now = datetime.now()

        cur.execute("""
            INSERT INTO charging_sessions (
                vehicle_id, vehicle_name, battery_capacity,
                start_battery_percent, current_battery_percent, target_battery_percent,
                charger_power, price_per_unit,
                current_energy, target_energy,
                units_required, units_consumed, units_left,
                amount, estimated_total_hours, time_left_hours,
                status, start_time, end_time, last_updated, total_duration_seconds
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            vehicle_db_id,
            vehicle_name,
            battery_capacity,
            current_battery_percent,
            current_battery_percent,
            target_battery_percent,
            charger_power,
            price_per_unit,
            initial["current_energy"],
            initial["target_energy"],
            initial["units_required"],
            0,
            initial["units_left"],
            0,
            initial["estimated_total_hours"],
            initial["time_left_hours"],
            "Charging",
            now,
            None,
            now,
            0
        ))

        session_id = cur.lastrowid
        mysql.connection.commit()
        cur.close()

        flash("Charging session started successfully.", "success")
        return redirect(url_for("dashboard", session_id=session_id))

    return render_template("start_charging.html", default_price=default_price)


@app.route("/dashboard/<int:session_id>")
def dashboard(session_id):
    session_row = persist_live_session_update(session_id)
    if not session_row:
        flash("Charging session not found.", "danger")
        return redirect(url_for("history"))

    session_data = serialize_session(session_row)
    return render_template("dashboard.html", session=session_data)


@app.route("/api/session/<int:session_id>")
def api_session(session_id):
    session_row = persist_live_session_update(session_id)
    if not session_row:
        return jsonify({"success": False, "message": "Session not found"}), 404

    return jsonify({"success": True, "session": serialize_session(session_row)})


@app.route("/stop-charging/<int:session_id>", methods=["POST"])
def stop_charging(session_id):
    session_row = persist_live_session_update(session_id)
    if not session_row:
        flash("Session not found.", "danger")
        return redirect(url_for("history"))

    if session_row["status"] == "Full":
        flash("Charging is already complete.", "info")
        return redirect(url_for("dashboard", session_id=session_id))

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE charging_sessions
        SET status=%s, end_time=%s, last_updated=%s
        WHERE id=%s
    """, ("Stopped", datetime.now(), datetime.now(), session_id))
    mysql.connection.commit()
    cur.close()

    flash("Charging session stopped successfully.", "warning")
    return redirect(url_for("dashboard", session_id=session_id))


@app.route("/history")
def history():
    vehicle_search = request.args.get("vehicle", "").strip()
    status_filter = request.args.get("status", "").strip()
    date_filter = request.args.get("date", "").strip()

    query = """
        SELECT cs.*, v.vehicle_id AS original_vehicle_id
        FROM charging_sessions cs
        JOIN vehicles v ON cs.vehicle_id = v.id
        WHERE 1=1
    """
    params = []

    if vehicle_search:
        query += " AND (cs.vehicle_name LIKE %s OR v.vehicle_id LIKE %s)"
        like_term = f"%{vehicle_search}%"
        params.extend([like_term, like_term])

    if status_filter:
        query += " AND cs.status = %s"
        params.append(status_filter)

    if date_filter:
        query += " AND DATE(cs.start_time) = %s"
        params.append(date_filter)

    query += " ORDER BY cs.id DESC"

    cur = mysql.connection.cursor()
    cur.execute(query, tuple(params))
    sessions = cur.fetchall()
    cur.close()

    sessions_data = []
    for s in sessions:
        if s["status"] == "Charging":
            persist_live_session_update(s["id"])
            s = get_session_by_id(s["id"])
        sessions_data.append(serialize_session(s))

    return render_template("history.html", sessions=sessions_data)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM admin_users WHERE username=%s AND password=%s", (username, password))
        admin = cur.fetchone()
        cur.close()

        if admin:
            session["admin_logged_in"] = True
            session["admin_username"] = admin["username"]
            flash("Admin login successful.", "success")
            return redirect(url_for("admin"))

        flash("Invalid admin username or password.", "danger")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin():
    cur = mysql.connection.cursor()

    cur.execute("SELECT id FROM charging_sessions WHERE status='Charging'")
    active_rows = cur.fetchall()
    for row in active_rows:
        persist_live_session_update(row["id"])

    cur.execute("SELECT COUNT(*) AS total_sessions FROM charging_sessions")
    total_sessions = cur.fetchone()["total_sessions"]

    cur.execute("SELECT IFNULL(SUM(units_consumed), 0) AS total_units FROM charging_sessions")
    total_units = float(cur.fetchone()["total_units"])

    cur.execute("SELECT IFNULL(SUM(amount), 0) AS total_revenue FROM charging_sessions")
    total_revenue = float(cur.fetchone()["total_revenue"])

    cur.execute("SELECT COUNT(*) AS active_sessions FROM charging_sessions WHERE status='Charging'")
    active_sessions = cur.fetchone()["active_sessions"]

    cur.execute("SELECT COUNT(*) AS completed_sessions FROM charging_sessions WHERE status='Full'")
    completed_sessions = cur.fetchone()["completed_sessions"]

    cur.execute("SELECT COUNT(*) AS stopped_sessions FROM charging_sessions WHERE status='Stopped'")
    stopped_sessions = cur.fetchone()["stopped_sessions"]

    cur.execute("""
        SELECT status, COUNT(*) AS count
        FROM charging_sessions
        GROUP BY status
    """)
    status_rows = cur.fetchall()

    status_counts = {"Charging": 0, "Full": 0, "Stopped": 0}
    for row in status_rows:
        status_counts[row["status"]] = row["count"]

    cur.execute("""
        SELECT vehicle_name, ROUND(SUM(units_consumed), 2) AS total_units
        FROM charging_sessions
        GROUP BY vehicle_name
        ORDER BY total_units DESC
        LIMIT 5
    """)
    vehicle_rows = cur.fetchall()

    cur.execute("""
        SELECT id, vehicle_name, current_battery_percent, target_battery_percent,
               units_consumed, amount, status, start_time
        FROM charging_sessions
        ORDER BY id DESC
        LIMIT 8
    """)
    recent_sessions = cur.fetchall()

    station = get_station_settings()
    cur.close()

    return render_template(
        "admin.html",
        total_sessions=total_sessions,
        total_units=round(total_units, 2),
        total_revenue=round(total_revenue, 2),
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        stopped_sessions=stopped_sessions,
        recent_sessions=recent_sessions,
        status_counts=status_counts,
        vehicle_rows=vehicle_rows,
        station=station
    )


@app.route("/receipt/<int:session_id>")
def receipt(session_id):
    session_row = persist_live_session_update(session_id)
    if not session_row:
        flash("Session not found.", "danger")
        return redirect(url_for("history"))

    station = get_station_settings()
    return render_template("receipt.html", session=serialize_session(session_row), station=station)


@app.errorhandler(404)
def not_found(error):
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("index.html"), 500

@app.route("/admin/seed-data", methods=["POST"])
@admin_required
def admin_seed_data():
    seed_sample_sessions()
    flash("Sample charging sessions inserted successfully.", "success")
    return redirect(url_for("admin"))
@app.route("/admin/station-settings", methods=["POST"])
@admin_required
def update_station_settings():
    station_name = request.form.get("station_name", "").strip()
    station_location = request.form.get("station_location", "").strip()
    support_number = request.form.get("support_number", "").strip()
    gst_number = request.form.get("gst_number", "").strip()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM station_settings ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()

    if row:
        cur.execute("""
            UPDATE station_settings
            SET station_name=%s, station_location=%s, support_number=%s, gst_number=%s
            WHERE id=%s
        """, (station_name, station_location, support_number, gst_number, row["id"]))
    else:
        cur.execute("""
            INSERT INTO station_settings (station_name, station_location, support_number, gst_number)
            VALUES (%s, %s, %s, %s)
        """, (station_name, station_location, support_number, gst_number))

    mysql.connection.commit()
    cur.close()

    flash("Station settings updated successfully.", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True)