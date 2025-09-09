import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os
import random
from reportlab.pdfgen import canvas

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("university.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT,
    full_name TEXT,
    student_id TEXT,
    username TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    password TEXT
)''')

# Messages table
c.execute('''CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    timestamp TEXT
)''')

# Courses table
c.execute('''CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT,
    course_name TEXT
)''')

# Registrations table
c.execute('''CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course_code TEXT
)''')

# Exams table
c.execute('''CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT,
    exam_date TEXT,
    center TEXT
)''')

# Attendance table
c.execute('''CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course_code TEXT,
    date TEXT,
    status TEXT
)''')

# Assignment uploads table
c.execute('''CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course_code TEXT,
    filename TEXT,
    timestamp TEXT
)''')

# M-Pesa payments table
c.execute('''CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    amount REAL,
    status TEXT,
    timestamp TEXT
)''')

# Hostel applications table
c.execute('''CREATE TABLE IF NOT EXISTS hostel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    room_number TEXT,
    status TEXT,
    timestamp TEXT
)''')

# Forum posts table
c.execute('''CREATE TABLE IF NOT EXISTS forum (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    message TEXT,
    timestamp TEXT
)''')

# Election votes table
c.execute('''CREATE TABLE IF NOT EXISTS elections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    candidate TEXT,
    timestamp TEXT
)''')

conn.commit()

# ---------- HELPER FUNCTIONS ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def send_message(sender, receiver, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
              (sender, receiver, message, timestamp))
    conn.commit()

def generate_pdf(filename, text_lines):
    c = canvas.Canvas(filename)
    y = 800
    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()

def mpesa_payment(student, amount):
    status = random.choice(["SUCCESS", "FAILED"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO payments (student, amount, status, timestamp) VALUES (?, ?, ?, ?)",
              (student, amount, status, timestamp))
    conn.commit()
    return status

# ---------- STREAMLIT APP ----------
st.set_page_config(page_title="MyUniSpace Portal", layout="wide")
st.title("🌐 MyUniSpace Portal")

# Sidebar menu
if 'username' not in st.session_state:
    menu = ["Home", "Register", "Login"]
    choice = st.sidebar.selectbox("Menu", menu)

# ---------- REGISTER ----------
if 'username' not in st.session_state and choice == "Register":
    st.subheader("Create an Account")
    role = st.selectbox("Role", ["Student", "Lecturer", "Admin"])
    full_name = st.text_input("Full Name")
    student_id = st.text_input("Admission/Student ID (optional for Lecturer/Admin)")
    username = st.text_input("Username")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    password = st.text_input("Password", type='password')
    if st.button("Register"):
        if username and password:
            try:
                c.execute("INSERT INTO users (role, full_name, student_id, username, email, phone, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (role, full_name, student_id, username, email, phone, hash_password(password)))
                conn.commit()
                st.success(f"{role} registered successfully!")
            except:
                st.error("Username already exists.")

# ---------- LOGIN ----------
elif 'username' not in st.session_state and choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        c.execute("SELECT role, password FROM users WHERE username=?", (username,))
        data = c.fetchone()
        if data and verify_password(password, data[1]):
            role = data[0]
            st.session_state['username'] = username
            st.session_state['role'] = role
            st.success(f"Logged in as {role}")
        else:
            st.error("Invalid credentials")

# ---------- DASHBOARDS ----------
if 'username' in st.session_state:
    username = st.session_state['username']
    role = st.session_state['role']
    st.sidebar.write(f"Logged in as: {username} ({role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    if role == "Student":
        st.subheader(f"Student Dashboard ({username})")
        # All student features with buttons reacting
        course_code = st.text_input("Course Code (for registration or assignment)")
        uploaded_file = st.file_uploader("Upload Assignment", type=["pdf","docx","jpg","png"])
        camera_image = st.camera_input("Or take a picture for Assignment")
        if st.button("Submit Assignment"):
            if uploaded_file or camera_image:
                file_path = os.path.join("uploads", uploaded_file.name if uploaded_file else f"{username}_camera.png")
                os.makedirs("uploads", exist_ok=True)
                with open(file_path, "wb") as f:
                    if uploaded_file:
                        f.write(uploaded_file.getbuffer())
                    else:
                        f.write(camera_image.getbuffer())
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO assignments (student, course_code, filename, timestamp) VALUES (?, ?, ?, ?)",
                          (username, course_code, os.path.basename(file_path), timestamp))
                conn.commit()
                st.success("Assignment uploaded successfully!")

        if st.button("Register Course"):
            if course_code:
                c.execute("INSERT INTO registrations (student, course_code) VALUES (?, ?)", (username, course_code))
                conn.commit()
                st.success("Course Registered")

        if st.button("Pay Fees"):
            amount = st.number_input("Enter Amount", min_value=1)
            if st.button("Pay Now"):
                status = mpesa_payment(username, amount)
                st.success(f"Payment {status}")

        if st.button("View Courses"):
            c.execute("SELECT course_code FROM registrations WHERE student=?", (username,))
            courses = c.fetchall()
            st.write(courses if courses else "No courses registered.")

        if st.button("View Exam Timetable"):
            c.execute("SELECT course_code, exam_date, center FROM exams")
            exams = c.fetchall()
            for exam in exams:
                st.write(f"{exam[0]} | {exam[1]} | {exam[2]}")

        if st.button("Hostel Application"):
            room = st.text_input("Preferred Room Number")
            if st.button("Apply"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO hostel (student, room_number, status, timestamp) VALUES (?, ?, ?, ?)",
                          (username, room, "Pending", timestamp))
                conn.commit()
                st.success("Hostel application submitted!")

        if st.button("Forum"):
            post = st.text_area("Write your post")
            if st.button("Post"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO forum (user, message, timestamp) VALUES (?, ?, ?)", (username, post, timestamp))
                conn.commit()
                st.success("Posted to forum!")
            st.write("Forum Posts:")
            c.execute("SELECT user, message, timestamp FROM forum ORDER BY id DESC")
            posts = c.fetchall()
            for p in posts:
                st.write(f"{p[2]} | {p[0]}: {p[1]}")

        if st.button("Vote in Elections"):
            candidate = st.text_input("Enter Candidate Name")
            if st.button("Submit Vote"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO elections (student, candidate, timestamp) VALUES (?, ?, ?)",
                          (username, candidate, timestamp))
                conn.commit()
                st.success("Vote submitted!")

        if st.button("Send Message"):
            receiver = st.text_input("Receiver username")
            message = st.text_area("Message")
            if st.button("Send"):
                send_message(username, receiver, message)
                st.success("Message sent!")

        if st.button("View Messages"):
            c.execute("SELECT sender, message, timestamp FROM messages WHERE receiver=?", (username,))
            msgs = c.fetchall()
            for msg in msgs:
                st.write(f"{msg[2]} | {msg[0]}: {msg[1]}")

    elif role == "Lecturer":
        st.subheader(f"Lecturer Dashboard ({username})")
        # Lecturer features: post exams, mark attendance, grade assignments
        course_code = st.text_input("Course Code")
        exam_date = st.date_input("Exam Date")
        center = st.text_input("Exam Center")
        if st.button("Post Exam"):
            c.execute("INSERT INTO exams (course_code, exam_date, center) VALUES (?, ?, ?)", (course_code, exam_date, center))
            conn.commit()
            st.success("Exam posted!")

        student_name = st.text_input("Student Username for Attendance")
        status = st.selectbox("Attendance Status", ["Present", "Absent"])
        if st.button("Mark Attendance"):
            date = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO attendance (student, course_code, date, status) VALUES (?, ?, ?, ?)",
                      (student_name, course_code, date, status))
            conn.commit()
            st.success("Attendance marked!")

        if st.button("View Assignments"):
            c.execute("SELECT * FROM assignments WHERE course_code=?", (course_code,))
            assgns = c.fetchall()
            for a in assgns:
                st.write(a)

        if st.button("Send Message"):
            receiver = st.text_input("Receiver username")
            message = st.text_area("Message")
            if st.button("Send"):
                send_message(username, receiver, message)
                st.success("Message sent!")

    elif role == "Admin":
        st.subheader("Admin Dashboard")
        if st.button("Manage Users"):
            c.execute("SELECT id, role, username, full_name, email, phone FROM users")
            users = c.fetchall()
            for u in users:
                st.write(f"{u[0]} | {u[1]} | {u[2]} | {u[3]} | {u[4]} | {u[5]}")

        if st.button("View Messages"):
            c.execute("SELECT sender, receiver, message, timestamp FROM messages")
            msgs = c.fetchall()
            for msg in msgs:
                st.write(f"{msg[3]} | {msg[0]} -> {msg[1]}: {msg[2]}")

        if st.button("All Courses"):
            c.execute("SELECT * FROM courses")
            courses = c.fetchall()
            for course in courses:
                st.write(course)

        if st.button("All Exams"):
            c.execute("SELECT * FROM exams")
            exams = c.fetchall()
            for exam in exams:
                st.write(exam)

        if st.button("All Payments"):
            c.execute("SELECT * FROM payments")
            payments = c.fetchall()
            for p in payments:
                st.write(p)

        if st.button("All Assignments"):
            c.execute("SELECT * FROM assignments")
            assgns = c.fetchall()
            for a in assgns:
                st.write(a)

        if st.button("Hostel Applications"):
            c.execute("SELECT * FROM hostel")
            hostels = c.fetchall()
            for h in hostels:
                st.write(h)

        if st.button("Election Votes"):
            c.execute("SELECT * FROM elections")
            votes = c.fetchall()
            for v in votes:
                st.write(v)

        if st.button("Forum Posts"):
            c.execute("SELECT * FROM forum")
            posts = c.fetchall()
            for p in posts:
                st.write(p)





    
   
           
            
           
                
   
        
        
                
       
              
        
                
