# Satelite image filter
An ultra-efficient, low-compute **Edge AI / Computer Vision** pipeline designed to run directly on satellite hardware (e.g., CubeSats). It filters out "not worthy" images (cluttered with heavy clouds, fog, or empty ocean water) directly on orbit, ensuring that **only high-value, actionable data is transmitted back to Earth**. 

By processing pixels on the edge, this project eliminates the **Downlink Bottleneck**, saving up to 70% of satellite communication bandwidth and drastically reducing transmission costs.

---

## 🚀 The Problem & Our Solution

- **The Problem:** Satellites capture terabytes of data daily, but over **70% of it is obscured by clouds** or contains empty features. Sending these raw, useless gigabytes to Earth wastes expensive radio channel bandwidth and delays critical imaging tasks.
- **Our Solution:** Instead of heavy, energy-draining Deep Learning models that drain space batteries, we built a fast image analyzer using pure linear algebra and pixel matrix manipulation. It determines an image's worthiness in milliseconds using minimal CPU/RAM.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Image Processing:** Pillow (PIL) for efficient image asset loading and transformation.
- **Core Engine:** NumPy for high-speed matrix calculations and pixel-level threshold analysis.
- **Frontend Dashboard:** Streamlit for simulating the satellite's onboard environment or the ground control station.
- **Version Control:** GitHub

---

## ⚙️ How It Works (The Logic)

The core algorithm processes images through a highly optimized pipeline:
1. **Luminance & Contrast Mapping:** Pillow converts incoming satellite feeds into raw pixel arrays.
2. **Cloud & Garbage Masking:** NumPy evaluates spatial noise and brightness matrices. If a specific threshold of white/gray pixels (representing heavy cloud cover) or uniform textures (empty open water) is crossed, the image is flagged as `DISCARD`.
3. **Feature Density Verification:** Images with structural details, unique color variances, or high entropy are flagged as `WORTHY` and queued for high-priority Downlink transmission.

---

## 🖥️ Live Dashboard Preview

The **Streamlit** application allows operators to simulate the process:
- Upload raw satellite image streams.
- Dynamically adjust the Cloud/Waste Threshold sliders.
- View real-time metrics on **Bandwidth Saved ($/MB)** and data prioritization.

---

## 📦 Installation & Local Setup

To run the satellite dashboard simulation locally, follow these steps:

### 1. Clone the repository
```bash
git clone https://github.com
cd YOUR_REPOSITORY_NAME
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
*(Make sure your `requirements.txt` includes: `streamlit`, `numpy`, and `Pillow`)*

### 3. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 👥 Team & Hackathon Context
Developed during the [Name of Hackathon] 2026. 

- **[Your Name/Handle]** - Core Algorithm & NumPy Processing
- **[Teammate Name]** - Streamlit Interface & Logic Integration

*“Save the gigabytes, rescue the terabytes. Making space data instant.”*
