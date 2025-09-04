import streamlit as st
import sqlite3
import hashlib
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import random

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("university.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT,
    username TEXT UNIQUE,
    password TEXT,
    email TEXT
)
''')

# Messages table
c.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    timestamp TEXT
)
''')

# Courses table
c.execute('''
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT,
    course_name TEXT
)
''')

# Registrations table
c.execute('''
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course_code TEXT
)
''')

# Exams table
c.execute('''
CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT,
    exam_date TEXT,
    center TEXT
)
''')

# Attendance table
c.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course_code TEXT,
    date TEXT,
    status TEXT
)
''')

# Assignment uploads table
c.execute('''
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    course_code TEXT,
    filename TEXT,
    timestamp TEXT
)
''')

# M-Pesa payments table
c.execute('''
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student TEXT,
    amount REAL,
    status TEXT,
    timestamp TEXT
)
''')

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
st.set_page_config(page_title="University Portal", layout="wide")
st.title("🌐 University Portal System")

menu = ["Home", "Register", "Login"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------- REGISTER ----------
if choice == "Register":
    st.subheader("Create an Account")
    role = st.selectbox("Role", ["Student", "Lecturer", "Admin"])
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    if st.button("Register"):
        if username and password:
            try:
                c.execute("INSERT INTO users (role, username, password, email) VALUES (?, ?, ?, ?)",
                          (role, username, hash_password(password), email))
                conn.commit()
                st.success(f"{role} registered successfully!")
            except:
                st.error("Username already exists.")

# ---------- LOGIN ----------
elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        c.execute("SELECT role, password FROM users WHERE username=?", (username,))
        data = c.fetchone()
        if data and verify_password(password, data[1]):
            role = data[0]
            st.success(f"Logged in as {role}")
            st.session_state['username'] = username
            st.session_state['role'] = role
        else:
            st.error("Invalid credentials")

# ---------- DASHBOARDS ----------
if 'username' in st.session_state:
    username = st.session_state['username']
    role = st.session_state['role']

    if role == "Student":
        st.subheader(f"Student Dashboard ({username})")
        student_menu = ["My Courses", "Register Course", "Exams", "Messages", "Generate PDFs",
                        "Assignments Upload", "M-Pesa Payment", "Attendance"]
        student_choice = st.selectbox("Options", student_menu)

        if student_choice == "My Courses":
            st.write("📚 Registered Courses")
            c.execute("SELECT course_code FROM registrations WHERE student=?", (username,))
            courses = c.fetchall()
            for course in courses:
                st.write(course[0])

        elif student_choice == "Register Course":
            st.write("📝 Register for Courses")
            course_code = st.text_input("Course Code")
            if st.button("Register Course"):
                c.execute("INSERT INTO registrations (student, course_code) VALUES (?, ?)", (username, course_code))
                conn.commit()
                st.success("Course Registered")

        elif student_choice == "Exams":
            st.write("📝 Exam Schedule")
            c.execute("SELECT course_code, exam_date, center FROM exams")
            exams = c.fetchall()
            for exam in exams:
                st.write(f"{exam[0]} - {exam[1]} - {exam[2]}")

        elif student_choice == "Messages":
            st.write("💬 Send Message")
            receiver = st.text_input("To")
            message = st.text_area("Message")
            if st.button("Send"):
                send_message(username, receiver, message)
                st.success("Message Sent!")

            st.write("📨 Inbox")
            c.execute("SELECT sender, message, timestamp FROM messages WHERE receiver=?", (username,))
            msgs = c.fetchall()
            for msg in msgs:
                st.write(f"{msg[2]} | {msg[0]}: {msg[1]}")

        elif student_choice == "Generate PDFs":
            st.write("📄 Generate PDFs")
            pdf_option = st.selectbox("Select", ["Fee Statement", "Clearance Form", "Exam Card"])
            if st.button("Generate PDF"):
                filename = f"{pdf_option}_{username}.pdf"
                text_lines = [f"{pdf_option} for {username}", f"Generated on {datetime.now()}"]
                generate_pdf(filename, text_lines)
                st.success(f"{filename} created!")

        elif student_choice == "Assignments Upload":
            st.write("📂 Upload Assignment / TP")
            course_code = st.text_input("Course Code")
            uploaded_file = st.file_uploader("Choose a file")
            if st.button("Upload"):
                if uploaded_file:
                    file_path = os.path.join("uploads", uploaded_file.name)
                    os.makedirs("uploads", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO assignments (student, course_code, filename, timestamp) VALUES (?, ?, ?, ?)",
                              (username, course_code, uploaded_file.name, timestamp))
                    conn.commit()
                    st.success("File uploaded successfully!")

        elif student_choice == "M-Pesa Payment":
            st.write("💰 Simulate M-Pesa Payment")
            amount = st.number_input("Enter Amount", min_value=1)
            if st.button("Pay"):
                status = mpesa_payment(username, amount)
                st.success(f"Payment {status}!")

        elif student_choice == "Attendance":
            st.write("📋 View Attendance")
            c.execute("SELECT course_code, date, status FROM attendance WHERE student=?", (username,))
            att = c.fetchall()
            for a in att:
                st.write(f"{a[1]} | {a[0]} | {a[2]}")

    elif role == "Lecturer":
        st.subheader(f"Lecturer Dashboard ({username})")
        lecturer_menu = ["My Courses", "Post Exam", "Messages", "Mark Attendance"]
        lecturer_choice = st.selectbox("Options", lecturer_menu)

        if lecturer_choice == "My Courses":
            st.write("📚 Courses you teach")
            c.execute("SELECT course_code FROM courses")
            courses = c.fetchall()
            for course in courses:
                st.write(course[0])

        elif lecturer_choice == "Post Exam":
            st.write("📝 Schedule an Exam")
            course_code = st.text_input("Course Code")
            exam_date = st.date_input("Exam Date")
            center = st.text_input("Exam Center")
            if st.button("Post Exam"):
                c.execute("INSERT INTO exams (course_code, exam_date, center) VALUES (?, ?, ?)",
                          (course_code, exam_date, center))
                conn.commit()
                st.success("Exam Posted")

        elif lecturer_choice == "Messages":
            st.write("💬 Send Message")
            receiver = st.text_input("To")
            message = st.text_area("Message")
            if st.button("Send"):
                send_message(username, receiver, message)
                st.success("Message Sent!")

            st.write("📨 Inbox")
            c.execute("SELECT sender, message, timestamp FROM messages WHERE receiver=?", (username,))
            msgs = c.fetchall()
            for msg in msgs:
                st.write(f"{msg[2]} | {msg[0]}: {msg[1]}")

        elif lecturer_choice == "Mark Attendance":
            st.write("📋 Mark Attendance")
            student_name = st.text_input("Student Username")
            course_code = st.text_input("Course Code")
            status = st.selectbox("Status", ["Present", "Absent"])
            if st.button("Submit Attendance"):
                date = datetime.now().strftime("%Y-%m-%d")
                c.execute("INSERT INTO attendance (student, course_code, date, status) VALUES (?, ?, ?, ?)",
                          (student_name, course_code, date, status))
                conn.commit()
                st.success("Attendance marked!")

    elif role == "Admin":
        st.subheader("Admin Panel")
        admin_menu = ["Manage Users", "View Messages", "All Courses", "All Exams", "All Payments"]
        admin_choice = st.selectbox("Options", admin_menu)

        if admin_choice == "Manage Users":
            c.execute("SELECT id, role, username, email FROM users")
            users = c.fetchall()
            st.write("Registered Users:")
            for u in users:
                st.write(f"{u[0]} | {u[1]} | {u[2]} | {u[3]}")

        elif admin_choice == "View Messages":
            c.execute("SELECT sender, receiver, message, timestamp FROM messages")
            msgs = c.fetchall()
            for msg in msgs:
                st.write(f"{msg[3]} | {msg[0]} -> {msg[1]}: {msg[2]}")

        elif admin_choice == "All Courses":
            c.execute("SELECT * FROM courses")
            courses = c.fetchall()
            for course in courses:
                st.write(course)

        elif admin_choice == "All Exams":
            c.execute("SELECT * FROM exams")
            exams = c.fetchall()
            for exam in exams:
                st.write(exam)

        elif admin_choice == "All Payments":
            c.execute("SELECT * FROM payments")
            payments = c.fetchall()
            for p in payments:
                st.write(p)
