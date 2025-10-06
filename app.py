from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
import mysql.connector
import bcrypt
import os
import json
from flask import send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import random  # Temporary: simulate people detection
import cv2
import numpy as np

# ---------------- CONFIG ----------------
app = Flask(__name__)
app.secret_key = "kumari"  # Required for session

# For saving zones
ZONES_FILE = "zones.json"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="Moon@231",
        database="crowdcount_db"
    )

# ---------------- ROUTES ----------------
# 1. Index (Login/Register)
@app.route("/", methods=["GET"])
def index():
    if "user_id" in session:
        return redirect(url_for("upload_video"))
    return render_template("login.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        user_id, stored_hashed = user
        stored_hashed = stored_hashed.encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_hashed):
            session["user_id"] = user_id
            return redirect(url_for("upload_video"))

    flash("Invalid login credentials")
    return redirect(url_for("register"))

@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password.decode("utf-8"))
        )
        conn.commit()
        flash("Registration successful! Please log in.")
    except mysql.connector.Error as e:
        flash(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login"))

# 2. Upload Video
@app.route("/upload", methods=["GET", "POST"])
def upload_video():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "video" not in request.files:
            flash("No video uploaded")
            return redirect(url_for("upload_video"))

        video = request.files["video"]
        if video.filename == "":
            flash("No selected file")
            return redirect(url_for("upload_video"))

        filename = secure_filename(video.filename)
        video.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        session["video_filename"] = filename
        return redirect(url_for("draw_zone"))

    return render_template("upload.html")

# 3. Draw Zones
@app.route("/draw", methods=["GET", "POST"])
def draw_zone():
    if "user_id" not in session or "video_filename" not in session:
        return redirect(url_for("upload_video"))

    video_filename = session["video_filename"]

    if request.method == "POST":
        zone_data = request.get_json().get("zones")
        if zone_data:
            all_data = []
            if os.path.exists(ZONES_FILE):
                with open(ZONES_FILE, "r") as f:
                    all_data = json.load(f)

            # Remove previous zones for this video
            all_data = [v for v in all_data if v.get("video") != video_filename]
            all_data.append({"video": video_filename, "zones": zone_data})

            with open(ZONES_FILE, "w") as f:
                json.dump(all_data, f, indent=4)

            return {"status": "success"}

    return render_template("draw.html", video_filename=video_filename)

# 4. Dashboard
@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    video_filename = session.get("video_filename", "")
    zones = []

    if os.path.exists(ZONES_FILE):
        with open(ZONES_FILE, "r") as f:
            all_data = json.load(f)
            for v in all_data:
                if v.get("video") == video_filename:
                    zones = v.get("zones", [])
                    break

    return render_template("dashboard.html", zones=zones, video=os.path.join(app.config["UPLOAD_FOLDER"], video_filename))

# ---------------- NEW: Real-time Population API ----------------
@app.route("/get_population", methods=["GET"])
def get_population():
    """Returns simulated real-time population counts for each zone."""
    video_filename = session.get("video_filename", "")
    zones_data = []

    if os.path.exists(ZONES_FILE):
        with open(ZONES_FILE, "r") as f:
            all_data = json.load(f)
            for v in all_data:
                if v.get("video") == video_filename:
                    for zone in v.get("zones", []):
                        # Simulate population count
                        population = random.randint(0, 5)
                        zones_data.append({
                            "label": zone["label"],
                            "population": population
                        })
                    break

    return jsonify(zones_data)
# ---------------- NEW: Video Streaming ----------------
def generate_frames(video_path):
    cap = cv2.VideoCapture(video_path)

    # Load zones for this video
    video_zones = []
    if os.path.exists(ZONES_FILE):
        with open(ZONES_FILE, "r") as f:
            all_data = json.load(f)
            for v in all_data:
                if v.get("video") == os.path.basename(video_path):
                    video_zones = v.get("zones", [])
                    break

    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop video
            continue

        # Simulate people detection
        height, width, _ = frame.shape
        boxes = [(random.randint(0, width//2), random.randint(0, height//2),
                  random.randint(width//2, width), random.randint(height//2, height))
                 for _ in range(random.randint(0, 5))]

        # Draw people
        for (x1, y1, x2, y2) in boxes:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255,255,0), 2)

        # Draw zones
        for idx, zone in enumerate(video_zones):
            pts = [(zone["topleft_x"], zone["topleft_y"]),
                   (zone["topright_x"], zone["topright_y"]),
                   (zone["bottomright_x"], zone["bottomright_y"]),
                   (zone["bottomleft_x"], zone["bottomleft_y"])]
            cv2.polylines(frame, [np.array(pts)], True, (0,255,0), 2)
            cv2.putText(frame, f"ID{idx+1}", pts[0], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            population = sum(1 for (x1,y1,x2,y2) in boxes
                             if pts[0][0] <= (x1+x2)//2 <= pts[2][0] and pts[0][1] <= (y1+y2)//2 <= pts[2][1])
            cv2.putText(frame, f"Pop:{population}", (pts[0][0], pts[0][1]+20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route("/video_feed")
def video_feed():
    if "video_filename" not in session:
        return redirect(url_for("upload_video"))
    video_path = os.path.join(app.config["UPLOAD_FOLDER"], session["video_filename"])
    return Response(generate_frames(video_path), mimetype='multipart/x-mixed-replace; boundary=frame')

# Delete Zone
@app.route("/delete_zone", methods=["POST"])
def delete_zone():
    label = request.form.get("label")
    if os.path.exists(ZONES_FILE):
        with open(ZONES_FILE, "r") as f:
            zones = json.load(f)
        zones = [z for z in zones if z.get("label") != label]
        with open(ZONES_FILE, "w") as f:
            json.dump(zones, f, indent=4)
    flash(f"Zone '{label}' deleted.")
    return redirect(url_for("dashboard"))

# Update Zone
@app.route("/update_zone", methods=["POST"])
def update_zone():
    old_label = request.form.get("old_label")
    new_label = request.form.get("new_label")
    if os.path.exists(ZONES_FILE):
        with open(ZONES_FILE, "r") as f:
            zones = json.load(f)
        for z in zones:
            if z.get("label") == old_label:
                z["label"] = new_label
        with open(ZONES_FILE, "w") as f:
            json.dump(zones, f, indent=4)
    flash(f"Zone updated: {old_label} → {new_label}")
    return redirect(url_for("dashboard"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
