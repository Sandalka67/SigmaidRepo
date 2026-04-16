# 🛡️ Signaid

**Emergency aid for remote communities.** > *Built for HackTUES 12 by Team Syrax.*

---

## 📖 About The Project

In critical moments, every second counts. **Signaid** is a real-time web application designed to bridge the gap between individuals in distress and emergency responders. By utilizing browser-based geolocation and a dynamic interactive map, Signaid allows users to broadcast their exact coordinates and relevant medical conditions instantly.

Whether in a remote village or a crowded city, Signaid provides a clean, panic-proof interface to get help on the map immediately.

---

## ✨ Key Features

* **One-Click SOS:** A highly visible, accessible emergency button that instantly grabs the user's GPS coordinates (Latitude/Longitude).
* **Live Map Visualization:** Powered by Leaflet.js and OpenStreetMap, active signals are immediately plotted on a live map of Bulgaria.
* **Smart Medical Context:** Users can pre-select medical conditions (e.g., Hypertension, Heart Disease) on their profile, which are attached to their emergency signal for responders to see.
* **Emergency Categorization:** A clean modal UI allows users to specify the type of emergency (Wildfire, Flood, Health, etc.) and add custom notes before sending.
* **Dynamic Dashboard:** Real-time UI updates track the community impact, showing Total Signals, Active Emergencies, and Resolved cases without requiring a page refresh.
* **State Management:** Built-in safeguards prevent users from spamming the network, locking the UI into an "Active" state until the emergency is safely resolved.

---

## 🛠️ Built With

**Frontend:**
* HTML5 & CSS3
* JavaScript (Vanilla DOM Manipulation & Fetch API)
* Bootstrap 5 (Responsive UI & Styling)
* Leaflet.js (Interactive Mapping)

**Backend:**
* Python 3
* Flask (RESTful API & Routing)
* SQLite / SQLAlchemy (Database & User Management)

---

## ⚙️ How to Run Locally

### 1. Prerequisites
Make sure you have Python installed. You can check by typing `python --version` in your terminal.

### 2. Folder Structure
Your project directory matches this architecture:

```text
SIGNAIDREPO/
├── backend/
│   ├── database/
│   │   └── models.py            # SQLAlchemy database schemas & classes
│   ├── instance/                # Backend specific instance folder
│   └── app.py                   # Main Flask server and API routing
├── frontend/
│   ├── static/
│   │   ├── interact.js          # Core frontend logic and modal interactions
│   │   ├── mapimplementation.js # Leaflet.js map initialization and rendering
│   │   └── style.css            # Custom UI styling and modal animations
│   └── templates/
│       ├── base.html            # Base Jinja layout template
│       ├── index.html           # Main dashboard and emergency modal
│       ├── login.html           # User login page
│       ├── map.html             # Standalone full-screen map view
│       ├── profile.html         # User profile and health conditions selection
│       └── register.html        # User registration page
├── instance/                    # Root instance folder (Contains signaid.db)
├── .gitignore                   # Ignored files for version control
├── HACKTUES12_FINAL.pptx        # Pitch deck / Presentation
└── README.md                    # Project documentation
3. Installation & Setup
Clone the repository:

Bash
git clone [https://github.com/yourusername/SignaidRepo.git](https://github.com/yourusername/SignaidRepo.git)
cd SignaidRepo
Create a Virtual Environment (Highly Recommended):

Bash
python -m venv venv
Activate on Windows: venv\Scripts\activate

Activate on macOS/Linux: source venv/bin/activate

Install Dependencies:
Install Flask and SQLAlchemy to run the backend:

Bash
pip install Flask Flask-SQLAlchemy
4. Running the Application
Ensure your terminal is in the root directory or the backend directory (depending on how your paths are set in app.py).

Start the Flask development server:

Bash
python backend/app.py 
(Note: Adjust the run command slightly depending on your terminal's current working directory).

Open your web browser and navigate to: http://127.0.0.1:5000
