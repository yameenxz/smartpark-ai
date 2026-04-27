# ParkWise AI – Intelligent Parking Allocation System

## Overview

ParkWise AI is a machine learning-driven parking management system designed to optimize parking space utilization in commercial environments.

The system predicts vehicle dwell time using inputs such as vehicle type, arrival time, and visit purpose, and dynamically allocates parking slots to reduce congestion and improve efficiency.

---

## Problem Statement

Traditional parking systems rely on static allocation strategies, which often result in:

* Inefficient utilization of parking space
* Increased congestion and waiting time
* Lack of predictive insights

ParkWise AI addresses these issues using a data-driven, predictive allocation approach.

---

## System Architecture

### Machine Learning Model

* Predicts parking duration based on:

  * Vehicle type
  * Arrival time
  * Visit purpose
* Trained on enhanced dataset
* Achieved Mean Absolute Error ≈ 0.39 hours

### Allocation Engine

* Dynamically assigns parking slots
* Matches predicted duration with optimal slot zones
* Optimized for efficient space utilization

### Database Layer

* SQLite-based backend
* Maintains real-time slot availability
* Updates dynamically after allocation

---

## Tech Stack

* Python
* Flask
* SQLite
* Scikit-learn
* HTML, CSS

---

## Key Features

* Predictive parking duration
* Intelligent slot allocation
* Real-time database updates
* Optimized allocation logic
* Modular system design

---

## Methodology

### Data Engineering

* Generated synthetic dataset
* Added visit purpose feature
* Improved dataset variability

### Model Training

* Implemented full ML pipeline
* Preprocessed and structured features
* Evaluated across multiple scenarios

### System Integration

* Integrated ML model with allocation engine
* Ensured smooth module interaction

### Testing & Validation

* Tested across multiple input cases
* Validated allocation and database logic

### Optimization

* Improved query performance
* Refactored code for modularity
* Enhanced system stability

---

## Project Structure

```
.
├── app.py
├── parking_engine.py
├── allocate_slot.py
├── generate_dataset.py
├── generate_slots.py
├── train_model.py
├── setup_database.py
├── reset_database.py
├── view_database.py
├── parking_model.pkl
├── parking_system.db
├── parking_slots_dataset.csv
├── synthetic_parking_dataset.csv
├── static/
├── requirements.txt
```

---

## How to Run

```bash
pip install -r requirements.txt
python generate_dataset.py
python train_model.py
python app.py
```

---

## Future Enhancements

* Integration with real-time IoT sensors
* Cloud deployment (AWS / GCP)
* Analytics dashboard
* Improved model accuracy

---

## Contact

[eng23cs0367@dsu.edu.in](mailto:eng23cs0367@dsu.edu.in)
