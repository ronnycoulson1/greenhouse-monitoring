# Frontend Specification (Streamlit)

## Purpose
This document defines the Streamlit frontend requirements for **Phase 1** of the Greenhouse Monitoring System. The goal is to build and validate the user interface while hardware and sensor integration is still in progress.

---

## Phase 1 Scope

### In Scope
- Streamlit **multi page** application
- Zone navigation:
  - **Zone 1** implemented first
  - later Zone 2 / Zone 3 
- Display environmental metrics for the selected zone:
  - Temperature
  - Humidity
  -  soil moisture
  - pH 
  - light placeholders(adjustment ?)

### Data Source for Phase 1 (Important Clarification)
During Phase 1, the UI will display data pulled from the **OpenWeather API**.  
This is **temporary** and is used  for our future sensor/database readings so the team can build and test the dashboard now.

Later, when Raspberry Pi + sensors + database are ready, we will replace the OpenWeather source with real greenhouse readings **without changing the overall UI design**.

---

## Phase 1 “Done” Criteria
Phase 1 is considered complete when:
- The app runs as a Streamlit multi-page dashboard
- Users can select **Zone 1** and view current metrics (at minimum temperature and humidity)
- The UI displays a zone status (e.g., OK / Warning / Alert) based on simple thresholds
- Zone 2 / Zone 3 exist as placeholders or basic pages

## Future possible updates
 ... 


