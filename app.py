
import os
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()

app = Flask(__name__)

DEVICE_POWER = {
    "desktop": 200,
    "laptop": 65,
    "server": 500
}

DEFAULTS = {
    "desktops": "10",
    "laptops": "5",
    "servers": "2",
    "hours": "8",
    "days": "22",
    "idle": "2",
    "renewable": "20",
    "recycling": "30",
    "emission_factor": "0.8"
}


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "greenaudit")
    )


def initialize_database():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            id INT AUTO_INCREMENT PRIMARY KEY,
            audit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            desktops INT,
            laptops INT,
            servers INT,
            operating_hours FLOAT,
            working_days INT,
            idle_hours FLOAT,
            renewable_percentage FLOAT,
            recycling_percentage FLOAT,
            emission_factor FLOAT,
            total_devices INT,
            total_energy FLOAT,
            desktop_energy FLOAT,
            laptop_energy FLOAT,
            server_energy FLOAT,
            carbon_emissions FLOAT,
            green_score INT,
            rating VARCHAR(50)
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


@app.route("/", methods=["GET", "POST"])
def home():
    results = None
    error = None
    form_data = DEFAULTS.copy()

    if request.method == "POST":
        for field in form_data:
            form_data[field] = request.form.get(field, "")

        connection = None
        cursor = None

        try:
            desktops = int(form_data["desktops"])
            laptops = int(form_data["laptops"])
            servers = int(form_data["servers"])

            hours = float(form_data["hours"])
            days = int(form_data["days"])
            idle = float(form_data["idle"])

            renewable = float(form_data["renewable"])
            recycling = float(form_data["recycling"])
            emission_factor = float(form_data["emission_factor"])

            if min(desktops, laptops, servers) < 0:
                raise ValueError("Device counts cannot be negative.")

            if not 1 <= days <= 31:
                raise ValueError("Working days must be between 1 and 31.")

            if not 0 < hours <= 24:
                raise ValueError("Operating hours must be between 0 and 24.")

            if not 0 <= idle <= hours:
                raise ValueError("Idle hours cannot exceed operating hours.")

            if not 0 <= renewable <= 100 or not 0 <= recycling <= 100:
                raise ValueError("Percentages must be between 0 and 100.")

            if emission_factor < 0:
                raise ValueError("Emission factor cannot be negative.")

            total_devices = desktops + laptops + servers

            if total_devices == 0:
                raise ValueError("Enter at least one device.")

            desktop_energy = (
                DEVICE_POWER["desktop"] * desktops * hours * days / 1000
            )

            laptop_energy = (
                DEVICE_POWER["laptop"] * laptops * hours * days / 1000
            )

            server_energy = (
                DEVICE_POWER["server"] * servers * hours * days / 1000
            )

            total_energy = (
                desktop_energy + laptop_energy + server_energy
            )

            carbon = total_energy * emission_factor

            # Green IT scoring components
            if hours <= 6:
                energy_score = 100
            elif hours <= 8:
                energy_score = 90
            elif hours <= 10:
                energy_score = 80
            elif hours <= 12:
                energy_score = 65
            elif hours <= 16:
                energy_score = 45
            else:
                energy_score = 25

            idle_percentage = (idle / hours) * 100

            if idle_percentage <= 10:
                idle_score = 100
            elif idle_percentage <= 20:
                idle_score = 85
            elif idle_percentage <= 35:
                idle_score = 70
            elif idle_percentage <= 50:
                idle_score = 50
            else:
                idle_score = 25

            renewable_score = renewable
            recycling_score = recycling

            raw_score = (
                energy_score * 0.35
                + idle_score * 0.20
                + renewable_score * 0.25
                + recycling_score * 0.20
            )

            green_score = int(raw_score + 0.5)

            if green_score >= 85:
                rating = "Excellent"
            elif green_score >= 70:
                rating = "Good"
            elif green_score >= 50:
                rating = "Moderate"
            elif green_score >= 30:
                rating = "Needs Improvement"
            else:
                rating = "Poor"

            recommendations = []

            if hours > 8:
                recommendations.append(
                    "Optimize operating schedules to reduce energy consumption."
                )

            if idle_percentage > 20:
                recommendations.append(
                    "Enable automatic sleep mode and power management."
                )

            if renewable < 50:
                recommendations.append(
                    "Increase renewable electricity adoption."
                )

            if recycling < 50:
                recommendations.append(
                    "Strengthen IT e-waste collection and recycling practices."
                )

            if server_energy > total_energy * 0.4:
                recommendations.append(
                    "Review server utilization and consider workload consolidation."
                )

            if not recommendations:
                recommendations.append(
                    "Excellent work! Continue maintaining sustainable IT practices."
                )

            results = {
                "devices": total_devices,
                "energy": round(total_energy, 2),
                "desktop_energy": round(desktop_energy, 2),
                "laptop_energy": round(laptop_energy, 2),
                "server_energy": round(server_energy, 2),
                "carbon": round(carbon, 2),
                "score": green_score,
                "rating": rating,
                "energy_score": energy_score,
                "idle_score": idle_score,
                "renewable_score": renewable_score,
                "recycling_score": recycling_score,
                "recommendations": recommendations
            }

            # Save audit to MySQL
            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO audits (
                    desktops, laptops, servers,
                    operating_hours, working_days, idle_hours,
                    renewable_percentage, recycling_percentage,
                    emission_factor, total_devices, total_energy,
                    desktop_energy, laptop_energy, server_energy,
                    carbon_emissions, green_score, rating
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                desktops, laptops, servers,
                hours, days, idle,
                renewable, recycling, emission_factor,
                total_devices, total_energy,
                desktop_energy, laptop_energy, server_energy,
                carbon, green_score, rating
            ))

            connection.commit()

        except (ValueError, TypeError) as e:
            error = str(e) or "Please enter valid values."

        except mysql.connector.Error as e:
            error = (
                "Audit calculated, but database saving failed. "
                f"MySQL error: {e}"
            )

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

    return render_template(
        "index.html",
        results=results,
        error=error,
        form_data=form_data
    )


@app.route("/history")
def history():
    audits = []
    error = None

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                audit_date,
                total_devices,
                desktops,
                laptops,
                servers,
                total_energy,
                carbon_emissions,
                green_score,
                rating
            FROM audits
            ORDER BY audit_date DESC, id DESC
        """)

        audits = cursor.fetchall()

    except mysql.connector.Error as e:
        error = f"Could not load audit history: {e}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return render_template(
        "history.html",
        audits=audits,
        error=error
    )


if __name__ == "__main__":
    initialize_database()
    print("GreenAudit database connected successfully!")
    app.run(debug=True)
