# EV Vehicle Charging Monitoring & Billing System

A full-stack **EV Charging Station Dashboard** built with:

- Python
- Flask
- MySQL
- HTML5
- CSS3
- JavaScript
- Bootstrap 5

This project simulates EV charging sessions in real time and displays:

- Battery percentage charged
- Battery percentage remaining
- Units consumed (kWh)
- Units left to full charge
- Live bill amount
- Estimated time left
- Charging status (Charging / Full / Stopped)
- Charging history
- Admin dashboard
- Receipt / bill page

---

# Features

## 1. Start Charging Session
Enter:
- Vehicle name
- Vehicle ID
- Battery capacity (kWh)
- Current battery %
- Target battery %
- Charger power (kW)
- Price per unit
- Owner / mobile number

## 2. Live Charging Dashboard
Shows:
- Battery progress
- Units consumed
- Units left
- Current bill amount
- Time left
- Status
- Start time / end time

## 3. Charging History
Filter by:
- Vehicle
- Status
- Date

## 4. Admin Dashboard
Displays:
- Total sessions
- Total units delivered
- Total revenue
- Active charging sessions
- Completed sessions
- Stopped sessions

## 5. Receipt / Bill Page
Printable charging receipt with session summary.

---

# Project Structure

ev_charging_system/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── schema.sql
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── charging.js
│   └── images/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── start_charging.html
│   ├── dashboard.html
│   ├── history.html
│   ├── admin.html
│   └── receipt.html
│
└── utils/
    ├── __init__.py
    └── charging_logic.py

---

# Database Setup

## 1. Open MySQL
If `mysql` is not in PATH, use:

```bash
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p