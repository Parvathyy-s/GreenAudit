# 🌱 GreenAudit – Green IT Sustainability Audit Tool

GreenAudit is a Flask-based web application designed to evaluate an organization's IT sustainability practices. It estimates energy consumption and carbon emissions based on IT infrastructure usage and generates a Green IT score along with recommendations for improving sustainability.

## 🚀 Features

- **Energy Consumption Estimation:** Calculates monthly energy consumption based on the number of desktops, laptops and servers.
- **Carbon Emission Estimation:** Estimates carbon emissions using energy consumption and a configurable emission factor.
- **Green IT Score:** Evaluates sustainability practices using a weighted scoring system.
- **Score Breakdown:** Displays individual scores for operating efficiency, idle time management, renewable energy usage and IT recycling.
- **Visual Analytics:** Presents device-wise energy consumption through a bar chart.
- **Smart Recommendations:** Provides suggestions to improve energy efficiency and sustainable IT practices.
- **Input Validation:** Validates user inputs to ensure meaningful audit results.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS
- **Visualization:** Chart.js
- **Version Control:** Git and GitHub

## 📊 Green IT Scoring Methodology

GreenAudit calculates a sustainability score out of 100 using four weighted parameters:

| Parameter | Weight |
|---|---:|
| Operating Efficiency | 35% |
| Idle Time Management | 20% |
| Renewable Energy Usage | 25% |
| IT Recycling Practices | 20% |

The final score is used to classify the organization's sustainability performance:

- 85–100: Excellent
- 70–84: Good
- 50–69: Moderate
- 30–49: Needs Improvement
- Below 30: Poor

*Note: This is a project-defined heuristic scoring model and not an externally certified sustainability rating.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Parvathyy-s/GreenAudit.git
```

### 2. Navigate to the project directory

```bash
cd GreenAudit
```

### 3. Create a virtual environment

```bash
python3 -m venv venv
```

### 4. Activate the virtual environment

For macOS/Linux:

```bash
source venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

```bash
python app.py
```

### 7. Open in your browser

```text
http://127.0.0.1:5000/
```

## 📁 Project Structure

```text
GreenAudit/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── templates/
│   └── index.html
│
└── static/
    └── style.css
```

## 🔮 Future Enhancements

- Integration with real-time IT infrastructure monitoring.
- Support for automated energy usage data collection.
- Historical audit reports and sustainability trend analysis.
- Exportable audit reports.
- More detailed sustainability analytics.

## 👩‍💻 Author

**Parvathy S**

GitHub: [@Parvathyy-s](https://github.com/Parvathyy-s)

---

*GreenAudit – Towards more sustainable IT practices.* 🌍