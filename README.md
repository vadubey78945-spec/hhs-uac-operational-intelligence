# 📊 UAC Care Transition Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458.svg)
![Plotly](https://img.shields.io/badge/Plotly-Data_Visualization-3F4F75.svg)



🔗 **Live Dashboard:** [View Application Here](https://hhs-uac-analytics.streamlit.app)


## 📖 Overview
The **UAC Care Transition Analytics** project is an operational intelligence dashboard designed to monitor, analyze, and optimize the pipeline of Unaccompanied Alien Children (UAC) transitioning between U.S. Customs and Border Protection (CBP) custody and the Department of Health & Human Services (HHS) care.

This dashboard provides executive-level visibility into system bottlenecks, transfer efficiencies, and discharge stability, enabling data-driven strategic interventions and policy adjustments.

## ✨ Key Features
- **Automated Data Processing:** Robust preprocessing pipeline that handles messy CSV formats, text artifacts (commas in numbers), and dynamically remaps columns.
- **Real-Time KPI Tracking:** Instant calculation of critical operational metrics (Transfer Efficiency, Discharge Effectiveness, Pipeline Throughput).
- **Interactive Visualizations:** High-fidelity, smooth `Plotly` charts that auto-scale to handle massive disparities between total care populations and daily intake/discharge volumes.
- **Bottleneck Detection System:** Algorithmic identification of sustained systemic blockages, complete with severity heatmaps and a flagged period ledger.
- **Automated Insights Engine:** Generates plain-text operational insights and strategic recommendations based on live data trends.
- **Executive Reporting:** One-click download of an Executive Summary Snapshot (.md) and sanitized raw processed data (.csv).

📈 **Core KPIs Monitored**

1. **Transfer Efficiency Ratio:** Tracks how effectively CBP transfers children out of temporary custody. *(Evaluated against dynamic, user-defined thresholds)*
2. **Discharge Effectiveness Index:** Measures the rate at which HHS successfully places children out of shelter care. *(Evaluated against dynamic, user-defined thresholds)*
3. **Pipeline Throughput:** The holistic ratio of HHS discharges relative to incoming CBP apprehensions. *(Evaluated against dynamic, user-defined thresholds)*
4. **Backlog Accumulation Rate:** Calculates the daily net-new bottleneck (Apprehensions minus Discharges).
5. **Outcome Stability Score:** A 7-day rolling standard deviation of discharges to measure operational consistency.

## 🛠️ Technology Stack
- **Frontend / UI:** [Streamlit](https://streamlit.io/)
- **Data Manipulation:** Pandas, NumPy
- **Visualizations:** [Plotly Express / Graph Objects]
- **Architecture:** Modular Python backend separating data loading, preprocessing, metrics computation, and UI rendering.

## 📂 Project Structure
```text
care-transition-analytics/
│
├── app/
│   └── streamlit_app.py        # Main Streamlit dashboard application
│
├── src/
│   ├── data_loader.py          # Handles CSV uploads and local file fetching
│   ├── preprocessing.py        # Sanitizes inputs, handles dates, and interpolates data
│   ├── metrics.py              # Contains mathematical logic for KPI generation
│   ├── bottleneck.py           # Algorithmic bottleneck detection and scoring
│   ├── visualization.py        # Plotly chart generation functions
│   └── utils.py                # Text generation for automated insights
│
├── data/
│   └── HHS_Unaccompanied_Alien_Children_Program.csv  # Bundled default dataset
│
├── README.md                   # Project documentation
└── requirements.txt            # Python dependencies

Installation & Setup
1. Clone the repository:

#Bash
git clone (https://github.com/vadubey78945-spec/hhs-uac-operational-intelligence.git)
cd care-transition-analytics

2. Create a virtual environment:

#Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Install required dependencies:

#Bash
pip install -r requirements.txt


4. Run the Dashboard:

#Bash
streamlit run app/streamlit_app.py

📊 Expected Data Format
The application is designed to intelligently parse datasets originating from HHS/CBP public releases. The robust preprocessor looks for the following core columns (regardless of exact column name variations):

* Date (Chronological record)

* Apprehensions (CBP Intake)

* In CBP Custody (Current CBP load)

* Transfers Out (CBP to HHS transitions)

* In HHS Care (Current HHS load)

* Discharges (HHS out-placements)

💡 Usage Guide

* Data Source: Use the sidebar to either upload a fresh CSV or use the bundled historical dataset.

* Dynamic Thresholds: Adjust KPI thresholds (sliders) in the sidebar to simulate different policy goals and instantly see which metrics pass or fail.

* Deep Dives: Use the tabs (Overview, KPI Trends, Bottleneck Analysis, Insights) to drill down from high-level summaries into specific chronological blockers.


⚖️ Disclaimer
This project was developed for academic/internship demonstration purposes. It utilizes publicly available data structures from the U.S. Department of Health & Human Services. The operational insights generated are algorithmic and do not represent official U.S. Government policy or statements.