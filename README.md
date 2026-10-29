# 🌱 Greenhouse Monitoring System (GMS)

**Group Alpha**

---

## 📌 Overview

The **Greenhouse Monitoring System (GMS)** is a full-stack monitoring platform designed to track and visualize environmental conditions inside a greenhouse.

The system:

* Collects environmental data (currently via API, later via sensors)
* Stores readings in a database
* Displays insights through a web dashboard

It is built to scale from **simulated API data → real IoT sensor integration (e.g., Raspberry Pi + Shelly devices)**.

---

## ⚙️ Tech Stack

### Backend

* Python
* MongoDB Atlas
* OpenWeather API
* pymongo
* python-dotenv

### Frontend

* Streamlit

---

## 🎯 Project Objectives

* Monitor environmental conditions across greenhouse zones
* Visualize temperature and humidity data
* Build a scalable system for IoT sensor integration
* Transition from API-based simulation → real sensor data

---

## 🏗️ System Architecture

* **Data Source** → OpenWeather API (temporary simulation)
* **Backend** → Fetch, transform, store data in MongoDB
* **Database** → MongoDB Atlas (cloud)
* **Frontend** → Streamlit dashboard for visualization

---

## 🚀 Backend Setup

### 📋 Requirements

* Python 3.10+
* pip
* MongoDB Atlas account (or local MongoDB)

---

### 🔹 1. Clone Repository

```bash
git clone <your-repo-url>
cd greenhouse-monitoring-system/backend
```

---

### 🔹 2. Create Virtual Environment

#### 🪟 Windows

```bash
python -m venv .venv
```

#### 🍎 Mac / Linux

```bash
python3 -m venv .venv
```

---

### 🔹 3. Activate Virtual Environment

#### 🪟 Windows (PowerShell)

```bash
.\.venv\Scripts\Activate.ps1
```

#### 🍎 Mac / Linux

```bash
source .venv/bin/activate
```

---

### 🔹 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 🔹 5. Create `.env` File

Create a `.env` file in the **backend folder**:

```env
MONGO_URI=your_mongodb_connection_string
DB_NAME=greenhouse_db

OPENWEATHER_API_KEY=your_openweather_api_key
OPENWEATHER_CITY=Akron
OPENWEATHER_COUNTRY=US
OPENWEATHER_UNITS=metric

ZONE=zone1
```

---

### 🔹 6. Run Backend

```bash
python -m app.ingest_openweather_live
```

---

## 💻 Frontend Setup (Streamlit)

### 📋 Requirements

* Python 3.10+
* Git

---

### 🔹 Setup & Run

#### 🍎 Mac / Linux

```bash
cd frontend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app/Home.py
```

---

#### 🪟 Windows

```bash
cd frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app/Home.py
```

---

### 🌐 Access App

Once running, open your browser at:

```
http://localhost:8501
```

---

## 🧪 Running Tests

### 📋 Overview

This test suite validates the backend using a **Test-Driven Development (TDD)** approach.

---

### ✅ What is Tested

* Weather API fetching (`get_weather`)
* Data transformation (`transform_data`)
* Database saving (`save_data`)
* Full pipeline (`collect_data_to_db`)
* Database connection (`init_db_collection`)

---

### ▶️ Run Tests

#### 🪟 Windows

```bash
.\backend\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests
```

#### 🍎 Mac / Linux

```bash
source backend/.venv/bin/activate
python -m unittest discover -s tests
```

---

### ⚡ Quick Test Command

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

### 📝 Notes

* Uses Python `unittest`
* Uses mock/fake objects (no real API calls)
* No external services are required
* Scheduler loop is not tested

---

## 🔄 Development Approach

* Phase 1: Use OpenWeather API to simulate sensor data
* Phase 2: Integrate IoT devices (e.g., Raspberry Pi, Shelly sensors)
* Phase 3: Expand zones and analytics

---

## 🌿 Future Improvements

* Real-time sensor integration (Shelly H&T, Raspberry Pi)
* Alerts/notifications for abnormal conditions
* Historical analytics & trends
* Multi-zone scalability
* Mobile-friendly UI

---

## 👥 Team

**Group Alpha**

---

## 📌 Summary

The Greenhouse Monitoring System is a scalable, full-stack application that:

* Collects environmental data
* Stores it efficiently
* Visualizes it clearly
