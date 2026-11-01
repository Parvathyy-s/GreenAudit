
from flask import Flask, render_template, request

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


@app.route("/", methods=["GET", "POST"])
def home():

    results = None
    error = None
    form_data = DEFAULTS.copy()

    if request.method == "POST":

        for field in form_data:
            form_data[field] = request.form.get(field, "")

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

            # Input validation
            if min(desktops, laptops, servers) < 0:
                raise ValueError("Device counts cannot be negative.")

            if not 1 <= days <= 31:
                raise ValueError("Working days must be between 1 and 31.")

            if not 0 < hours <= 24:
                raise ValueError("Operating hours must be between 0 and 24.")

            if not 0 <= idle <= hours:
                raise ValueError(
                    "Idle hours cannot exceed operating hours."
                )

            if not 0 <= renewable <= 100:
                raise ValueError("Renewable energy must be between 0 and 100.")

            if not 0 <= recycling <= 100:
                raise ValueError("Recycling percentage must be between 0 and 100.")

            if emission_factor < 0:
                raise ValueError("Emission factor cannot be negative.")

            total_devices = desktops + laptops + servers

            if total_devices == 0:
                raise ValueError("Enter at least one device.")

            # Energy consumption in kWh/month
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

            # Carbon emissions
            carbon = total_energy * emission_factor

            # GREEN IT SCORING SYSTEM

            # 1. Operating efficiency score (35%)
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

            # 2. Idle time management score (20%)
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

            # 3. Renewable energy score (25%)
            renewable_score = renewable

            # 4. IT recycling score (20%)
            recycling_score = recycling

            # Weighted Green IT score
            raw_score = (
                energy_score * 0.35
                + idle_score * 0.20
                + renewable_score * 0.25
                + recycling_score * 0.20
            )

            # Conventional rounding
            green_score = int(raw_score + 0.5)

            # Rating
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

            # Recommendations
            recommendations = []

            if hours > 8:
                recommendations.append(
                    "Optimize device operating schedules to reduce "
                    "unnecessary energy consumption."
                )

            if idle_percentage > 20:
                recommendations.append(
                    "Enable automatic sleep mode and power management "
                    "to reduce idle energy consumption."
                )

            if renewable < 50:
                recommendations.append(
                    "Increase renewable electricity adoption "
                    "to improve sustainability."
                )

            if recycling < 50:
                recommendations.append(
                    "Strengthen IT e-waste collection and recycling practices."
                )

            if server_energy > total_energy * 0.4:
                recommendations.append(
                    "Review server utilization and consider workload "
                    "consolidation to improve energy efficiency."
                )

            if not recommendations:
                recommendations.append(
                    "Excellent work! Your organization demonstrates "
                    "strong sustainable IT practices."
                )

            # Results passed to HTML
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

        except (ValueError, TypeError) as e:
            error = str(e) or "Please enter valid values."

    return render_template(
        "index.html",
        results=results,
        error=error,
        form_data=form_data
    )


if __name__ == "__main__":
    app.run(debug=True)
