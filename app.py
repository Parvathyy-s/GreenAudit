import os
from io import BytesIO

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

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


def get_recommendations(hours, idle, renewable, recycling, server_energy, total_energy):
    recommendations = []
    idle_percentage = (idle / hours) * 100 if hours else 0

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

    if total_energy > 0 and server_energy > total_energy * 0.4:
        recommendations.append(
            "Review server utilization and consider workload consolidation."
        )

    if not recommendations:
        recommendations.append(
            "Excellent work! Continue maintaining sustainable IT practices."
        )

    return recommendations


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

            total_energy = desktop_energy + laptop_energy + server_energy
            carbon = total_energy * emission_factor

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

            recommendations = get_recommendations(
                hours, idle, renewable, recycling, server_energy, total_energy
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
            results["audit_id"] = cursor.lastrowid

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


@app.route("/compare", methods=["GET", "POST"])
def compare():
    audits = []
    comparison = None
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
                total_energy,
                carbon_emissions,
                green_score,
                rating
            FROM audits
            ORDER BY audit_date ASC, id ASC
        """)

        audits = cursor.fetchall()

        if request.method == "POST":
            baseline_id = request.form.get("baseline_id", type=int)
            current_id = request.form.get("current_id", type=int)

            if not baseline_id or not current_id:
                error = "Please select both audits."

            elif baseline_id == current_id:
                error = "Please select two different audits."

            else:
                cursor.execute("""
                    SELECT
                        id,
                        audit_date,
                        total_energy,
                        carbon_emissions,
                        green_score,
                        rating
                    FROM audits
                    WHERE id IN (%s, %s)
                """, (baseline_id, current_id))

                selected = {
                    audit["id"]: audit
                    for audit in cursor.fetchall()
                }

                if baseline_id not in selected or current_id not in selected:
                    error = "One or both selected audits could not be found."

                else:
                    baseline = selected[baseline_id]
                    current = selected[current_id]

                    old_energy = float(baseline["total_energy"] or 0)
                    new_energy = float(current["total_energy"] or 0)

                    old_carbon = float(baseline["carbon_emissions"] or 0)
                    new_carbon = float(current["carbon_emissions"] or 0)

                    old_score = int(baseline["green_score"] or 0)
                    new_score = int(current["green_score"] or 0)

                    def reduction(old_value, new_value):
                        if old_value == 0:
                            return None
                        return round(
                            ((old_value - new_value) / old_value) * 100, 2
                        )

                    comparison = {
                        "baseline": baseline,
                        "current": current,
                        "energy_change": round(new_energy - old_energy, 2),
                        "carbon_change": round(new_carbon - old_carbon, 2),
                        "score_change": new_score - old_score,
                        "energy_reduction": reduction(old_energy, new_energy),
                        "carbon_reduction": reduction(old_carbon, new_carbon)
                    }

    except mysql.connector.Error as e:
        error = f"Could not load comparison data: {e}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    return render_template(
        "comparison.html",
        audits=audits,
        comparison=comparison,
        error=error
    )


@app.route("/download/<int:audit_id>")
def download_report(audit_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM audits
            WHERE id = %s
        """, (audit_id,))

        audit = cursor.fetchone()

        if audit is None:
            return "Audit report not found.", 404

        recommendations = get_recommendations(
            float(audit["operating_hours"] or 0),
            float(audit["idle_hours"] or 0),
            float(audit["renewable_percentage"] or 0),
            float(audit["recycling_percentage"] or 0),
            float(audit["server_energy"] or 0),
            float(audit["total_energy"] or 0)
        )

    except mysql.connector.Error as e:
        return f"Could not generate report: {e}", 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="GreenTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#176b45"),
        fontSize=22,
        leading=28,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#176b45"),
        fontSize=13,
        leading=17,
        spaceBefore=12,
        spaceAfter=7
    ))
    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13
    ))

    story = []

    audit_date = audit["audit_date"]
    if audit_date:
        date_text = audit_date.strftime("%d %B %Y, %I:%M %p")
    else:
        date_text = "Date unavailable"

    story.append(Paragraph("GreenAudit", styles["GreenTitle"]))
    story.append(Paragraph("IT Sustainability Audit Report", styles["Heading2"]))
    story.append(Paragraph(
        f"Audit ID: {audit['id']} &nbsp;&nbsp; | &nbsp;&nbsp; Date: {date_text}",
        styles["SmallText"]
    ))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(
        width="100%", thickness=1, color=colors.HexColor("#b7d9c5")
    ))

    story.append(Paragraph("1. Audit Inputs", styles["SectionHeading"]))

    input_data = [
        ["Parameter", "Value"],
        ["Desktops", str(audit["desktops"])],
        ["Laptops", str(audit["laptops"])],
        ["Servers", str(audit["servers"])],
        ["Total devices", str(audit["total_devices"])],
        ["Operating hours per day", f"{audit['operating_hours']} hours"],
        ["Working days per month", str(audit["working_days"])],
        ["Idle hours per day", f"{audit['idle_hours']} hours"],
        ["Renewable energy", f"{audit['renewable_percentage']}%"],
        ["IT recycling", f"{audit['recycling_percentage']}%"],
        ["Emission factor", f"{audit['emission_factor']} kg CO2/kWh"]
    ]

    input_table = Table(input_data, colWidths=[85 * mm, 75 * mm])
    input_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176b45")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5e2d9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f3f8f4")]),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    story.append(input_table)

    story.append(Paragraph("2. Energy Consumption", styles["SectionHeading"]))

    energy_data = [
        ["Device type", "Energy consumption (kWh/month)"],
        ["Desktop", f"{float(audit['desktop_energy'] or 0):.2f}"],
        ["Laptop", f"{float(audit['laptop_energy'] or 0):.2f}"],
        ["Server", f"{float(audit['server_energy'] or 0):.2f}"],
        ["Total", f"{float(audit['total_energy'] or 0):.2f}"]
    ]

    energy_table = Table(energy_data, colWidths=[85 * mm, 75 * mm])
    energy_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176b45")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e4f2e9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5e2d9")),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))
    story.append(energy_table)

    story.append(Paragraph("3. Carbon Emissions", styles["SectionHeading"]))
    story.append(Paragraph(
        f"Estimated monthly carbon emissions: "
        f"<b>{float(audit['carbon_emissions'] or 0):.2f} kg CO2</b>",
        styles["BodyText"]
    ))

    story.append(Paragraph("4. Green IT Score", styles["SectionHeading"]))
    story.append(Paragraph(
        f"Green IT Score: <b>{audit['green_score']}/100</b><br/>"
        f"Overall Rating: <b>{audit['rating']}</b>",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The Green IT score is a project-defined assessment based on the "
        "audit inputs and weighted scoring method used by GreenAudit.",
        styles["SmallText"]
    ))

    story.append(Paragraph("5. Recommendations", styles["SectionHeading"]))
    for recommendation in recommendations:
        story.append(Paragraph(
            f"&bull; {recommendation}",
            styles["BodyText"]
        ))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 14))
    story.append(HRFlowable(
        width="100%", thickness=0.7, color=colors.HexColor("#b7d9c5")
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Generated by GreenAudit | IT Sustainability Audit System",
        styles["SmallText"]
    ))

    document.build(story)
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"GreenAudit_Report_{audit_id}.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    initialize_database()
    print("GreenAudit database connected successfully!")
    app.run(debug=True)
