
# 🚗 AutoClaim AI
### AI-Based Vehicle Damage Detection and Insurance Claim Estimation System

AutoClaim AI is a web-based application that uses Artificial Intelligence and Machine Learning to detect vehicle damage, identify damaged parts, estimate repair costs, and calculate insurance claims.

The system also provides a spare parts marketplace where users can explore available vehicle spare parts and connect with registered shop owners.

## ✨ Features

### 🚘 AI-Based Vehicle Damage Detection
- Upload vehicle images for damage analysis.
- Detect vehicle damage using YOLO and deep learning models.
- Identify damaged vehicle parts.
- Display damage confidence and severity.

### 💰 Repair Cost Estimation
- Estimate repair costs for damaged vehicle parts.
- Calculate individual part costs.
- Estimate labor charges.
- Generate total repair cost.

### 🛡️ Insurance Claim Estimation
- Calculate insurance claim breakdowns.
- Support different insurance policy types.
- Estimate insurance claim probability.
- Display insurance-related calculations.

### 📄 Insurance PDF Report Generation
- Generate insurance claim reports in PDF format.
- Include vehicle and damage information.
- Display repair cost and insurance calculations.

### 🔧 Spare Parts Marketplace
- Browse available vehicle spare parts.
- Search spare parts by name.
- View prices and availability.
- Connect users with spare parts shop owners.

### 👥 User Management System

The application supports three types of users:

- **Admin:** Manage users, approve shop owners, and manage spare parts.
- **User:** Upload vehicle images, analyze damage, estimate repair costs, and search for spare parts.
- **Shop Owner:** Manage shop profiles, upload spare parts, update availability, and receive customer notifications.

### 📍 Location-Based Spare Parts Search
- Retrieve spare parts with shop location information.
- Calculate approximate distances using the Haversine formula when user coordinates are provided.

---

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Programming Language | Python, JavaScript |
| Backend | Flask |
| Frontend | HTML, CSS, JavaScript |
| Machine Learning | TensorFlow, PyTorch |
| Object Detection | YOLO |
| Database | SQLite |
| Authentication | Werkzeug Password Hashing |
| PDF Generation | Python PDF Generation Libraries |
| Package Management | pip, npm |

---

## 📂 Project Structure

```text
Tejal Project/
│
├── dataset/
│   └── Training and Testing Dataset
│
├── ml_model/
│   ├── model_weights/
│   │   ├── damage_detector.h5
│   │   └── best.pt
│   ├── predict_yolo.py
│   ├── insurance_calculator.py
│   └── pdf_generator.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── user_dashboard.html
│   ├── shop_dashboard.html
│   └── admin_dashboard.html
│
├── app.py
├── system.py
├── requirements.txt
├── package-lock.json
├── .gitignore
└── README.md
```

---

## ⚙️ Installation and Setup

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/FRIEND_USERNAME/AI-Vehicle-Damage-Detection-and-Insurance-Claim-System.git
```

### 2. Navigate to the Project Directory

```bash
cd AI-Vehicle-Damage-Detection-and-Insurance-Claim-System
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Application

```bash
python app.py
```

### 7. Open in Browser

Visit:

```text
http://127.0.0.1:5000
```

---

## 🧠 Machine Learning Models

The project uses machine learning and deep learning technologies for vehicle damage analysis.

- **YOLO:** Used for vehicle damage detection.
- **TensorFlow/Keras:** Used for deep learning model support.
- **PyTorch:** Used for loading and running PyTorch-based model weights.

Model weights are maintained in:

```text
ml_model/model_weights/
```

The training and testing dataset is maintained separately in the `dataset/` directory.

---

## 🔄 Application Workflow

1. User registers or logs into the application.
2. User uploads an image of a damaged vehicle.
3. The AI model analyzes the uploaded image.
4. The system identifies damaged vehicle parts.
5. Repair costs are estimated.
6. Insurance claim calculations are performed.
7. An insurance report can be generated in PDF format.
8. Users can explore available spare parts from registered shops.

---

## 🗄️ Database

The application uses SQLite for storing application information.

The main database tables include:

- `users`
- `shop_profiles`
- `spare_parts`
- `damage_reports`
- `notifications`

The database is initialized automatically when the Flask application starts.

---

## 🚀 Future Enhancements

- Improve vehicle damage detection accuracy.
- Support additional vehicle categories and damage types.
- Integrate insurance company APIs.
- Add online spare parts purchasing and payment functionality.
- Implement accurate GPS-based shop locations.
- Deploy the application on a cloud platform.
- Improve insurance claim estimation using additional training data.

---

## 📌 Project Information

| Field | Details |
|---|---|
| Project Name | AutoClaim AI |
| Project Title | AI-Based Vehicle Damage Detection and Insurance Claim Estimation System |
| Project Type | Web-Based Application |
| Domain | Artificial Intelligence, Machine Learning, Automotive Technology, Insurance Technology |
| Backend | Python Flask |
| Database | SQLite |

---

## ⚠️ Disclaimer

This application provides AI-assisted vehicle damage analysis and estimated insurance calculations for informational purposes. The results are estimates and do not represent official insurance approval or replace professional vehicle inspection.

---

## 📄 License

This project is developed for educational and development purposes. An appropriate license should be added before public reuse or distribution.
