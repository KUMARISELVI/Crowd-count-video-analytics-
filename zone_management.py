import cv2
import numpy as np
import mysql.connector
from datetime import datetime

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Moon@231",
        database="crowdcount_db"
    )

# ---------------- GLOBAL VARIABLES ----------------
zones = []
current_points = []
mode = "auto"  # automatic detection mode by default

# ---------------- DATABASE FUNCTIONS ----------------
def save_zone_to_db(label, points):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO zones (label, topleft_x, topleft_y, topright_x, topright_y, 
                           bottomright_x, bottomright_y, bottomleft_x, bottomleft_y)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (label,
          points[0][0], points[0][1],
          points[1][0], points[1][1],
          points[2][0], points[2][1],
          points[3][0], points[3][1]))
    conn.commit()
    cursor.close()
    conn.close()

def load_zones_from_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM zones")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def delete_zone_from_db(zone_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM zones WHERE id=%s", (zone_id,))
    conn.commit()
    cursor.close()
    conn.close()

def save_population_to_db(zone_id, count):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO zone_population (zone_id, population_count) VALUES (%s,%s)", (zone_id, count))
    conn.commit()
    cursor.close()
    conn.close()

# ---------------- MOUSE CALLBACK ----------------
def mouse_callback(event, x, y, flags, param):
    global current_points, zones
    if mode != "draw":
        return

    if event == cv2.EVENT_LBUTTONDOWN:
        current_points.append((x, y))
        if len(current_points) == 4:
            label = input("Enter zone label: ")
            save_zone_to_db(label, current_points)
            print(f"Zone '{label}' saved!")
            current_points = []

# ---------------- PERSON DETECTION / COUNTING ----------------
def detect_people(frame):
    """Dummy detection for demo. Replace with YOLO/SSD/OpenCV DNN."""
    height, width, _ = frame.shape
    count = np.random.randint(0, 5)  # simulate 0-4 people
    boxes = [(np.random.randint(0, width//2), np.random.randint(0, height//2),
              np.random.randint(width//2, width), np.random.randint(height//2, height))
             for _ in range(count)]
    return boxes

def count_people_in_zone(boxes, zone):
    x_min = min(zone["topleft_x"], zone["bottomleft_x"])
    x_max = max(zone["topright_x"], zone["bottomright_x"])
    y_min = min(zone["topleft_y"], zone["topright_y"])
    y_max = max(zone["bottomleft_y"], zone["bottomright_y"])
    count = 0
    for (x1, y1, x2, y2) in boxes:
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        if x_min <= cx <= x_max and y_min <= cy <= y_max:
            count += 1
    return count

def draw_zone_with_population(frame, zone, population, zone_id):
    pts = [(zone["topleft_x"], zone["topleft_y"]),
           (zone["topright_x"], zone["topright_y"]),
           (zone["bottomright_x"], zone["bottomright_y"]),
           (zone["bottomleft_x"], zone["bottomleft_y"])]
    # Draw green polygon for zone
    cv2.polylines(frame, [np.array(pts)], True, (0, 255, 0), 2)
    # Draw zone ID
    cv2.putText(frame, f"ID{zone_id}", pts[0], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    # Draw population inside zone
    cv2.putText(frame, f"Pop: {population}", (pts[0][0], pts[0][1]+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
    # Alert if population exceeds threshold
    threshold = zone.get("threshold", 3)  # default threshold
    if population > threshold:
        cv2.putText(frame, "ALERT!", (pts[0][0], pts[0][1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

# ---------------- MAIN ----------------
cap = cv2.VideoCapture(0)
cv2.namedWindow("Zone Management")
cv2.setMouseCallback("Zone Management", mouse_callback)

print("Controls: 'D'=Draw Zone | 'P'=Preview Zones | 'X'=Delete Zone | ESC=Exit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # ESC
        break
    elif key == ord('d'):
        mode = "draw"
        print("Mode: Draw Zones")
    elif key == ord('p'):
        mode = "preview"
        zones = load_zones_from_db()
        print("Mode: Preview Zones")
    elif key == ord('x'):
        zones = load_zones_from_db()
        print("\nZones Available:")
        for z in zones:
            print(f"{z['id']}. {z['label']}")
        zid = int(input("Enter Zone ID to delete: "))
        delete_zone_from_db(zid)
        zones = load_zones_from_db()
        mode = "preview"

    # ---------------- NEW: Automatic Zone Population ----------------
    boxes = detect_people(frame)
    if mode in ["preview", "draw", "auto"]:
        for zone in load_zones_from_db():
            population = count_people_in_zone(boxes, zone)
            if population > 0:  # only show zone if people detected
                draw_zone_with_population(frame, zone, population)
                save_population_to_db(zone["id"], population)

    # Draw detected people (optional visual)
    for (x1, y1, x2, y2) in boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255,255,0), 2)

    cv2.imshow("Zone Management", frame)

cap.release()
cv2.destroyAllWindows()
