# app.py
import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# -------------------------
# Database setup
# -------------------------
conn = sqlite3.connect("myunispace.db", check_same_thread=False)
c = conn.cursor()

# Users
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    role TEXT,
    password TEXT
)''')

# Courses
c.execute('''CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT,
    lecturer_id INTEGER
)''')

# Assignments
c.execute('''CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    description TEXT,
    due_date TEXT
)''')

# Fees
c.execute('''CREATE TABLE IF NOT EXISTS fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    amount REAL,
    status TEXT
)''')

# Hostel
c.execute('''CREATE TABLE IF NOT EXISTS hostel (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    room_number TEXT,
    status TEXT
)''')

# Announcements
c.execute('''CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    date TEXT
)''')

conn.commit()

# -------------------------
# Helper functions
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(name, email, password, role):
    c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
              (name, email, hash_password(password), role))
    conn.commit()

def login_user(email, password):
    c.execute("SELECT * FROM users WHERE email=? AND password=?",
              (email, hash_password(password)))
    return c.fetchone()

def get_courses():
    c.execute("SELECT courses.id, courses.course_name, users.name FROM courses LEFT JOIN users ON courses.lecturer_id = users.id")
    return c.fetchall()

def get_assignments(course_id):
    c.execute("SELECT * FROM assignments WHERE course_id=?", (course_id,))
    return c.fetchall()

def get_fees(student_id):
    c.execute("SELECT * FROM fees WHERE student_id=?", (student_id,))
    return c.fetchall()

def get_hostel(student_id):
    c.execute("SELECT * FROM hostel WHERE student_id=?", (student_id,))
    return c.fetchall()

def get_announcements():
    c.execute("SELECT * FROM announcements ORDER BY date DESC")
    return c.fetchall()

# -------------------------
# Session state
# -------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

# -------------------------
# App Layout
# -------------------------
st.title("🌐 MyUniSpace Portal")

menu = ["Login", "Register"]
if st.session_state.logged_in:
    menu = ["Dashboard", "Logout"]

choice = st.sidebar.selectbox("Menu", menu)

# -------------------------
# Register Page
# -------------------------
if choice == "Register":
    st.subheader("Create Account")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Register As", ["Student", "Lecturer", "Admin"])
    if st.button("Sign Up"):
        if name and email and password:
            try:
                register_user(name, email, password, role)
                st.success("Account created! You can login now.")
            except:
                st.error("Email already exists.")
        else:
            st.error("Please fill all fields.")

# -------------------------
# Login Page
# -------------------------
elif choice == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(email, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = {"id": user[0], "name": user[1], "email": user[2], "role": user[3]}
            st.success(f"Welcome {user[1]}!")
        else:
            st.error("Invalid credentials")

# -------------------------
# Dashboard
# -------------------------
elif choice == "Dashboard":
    user = st.session_state.user
    st.subheader(f"Hello, {user['name']} ({user['role']})")

    # ---------------------
    # Admin Features
    # ---------------------
    if user['role'] == "Admin":
        st.write("### Admin Features")
        st.write("Manage Users, Courses, Assignments, Fees, Hostel, Announcements")

        st.write("#### Create Announcement")
        ann_title = st.text_input("Title", key="ann_title")
        ann_content = st.text_area("Content", key="ann_content")
        if st.button("Post Announcement"):
            c.execute("INSERT INTO announcements (title, content, date) VALUES (?, ?, ?)",
                      (ann_title, ann_content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("Announcement posted!")

        st.write("#### Existing Announcements")
        announcements = get_announcements()
        for ann in announcements:
            st.write(f"**{ann[1]}** ({ann[3]}): {ann[2]}")

    # ---------------------
    # Lecturer Features
    # ---------------------
    elif user['role'] == "Lecturer":
        st.write("### Lecturer Features")
        st.write("Upload Courses & Assignments")

        st.write("#### Add Course")
        course_name = st.text_input("Course Name", key="lec_course")
        if st.button("Add Course"):
            c.execute("INSERT INTO courses (course_name, lecturer_id) VALUES (?, ?)", (course_name, user['id']))
            conn.commit()
            st.success("Course added!")

        st.write("#### Add Assignment")
        courses = get_courses()
        course_options = {f"{c[1]} (ID:{c[0]})": c[0] for c in courses if c[2] == user['name']}
        if course_options:
            selected_course = st.selectbox("Select Course", list(course_options.keys()))
            assign_title = st.text_input("Assignment Title", key="assign_title")
            assign_desc = st.text_area("Description", key="assign_desc")
            assign_due = st.date_input("Due Date")
            if st.button("Add Assignment"):
                c.execute("INSERT INTO assignments (course_id, title, description, due_date) VALUES (?, ?, ?, ?)",
                          (course_options[selected_course], assign_title, assign_desc, assign_due.strftime("%Y-%m-%d")))
                conn.commit()
                st.success("Assignment added!")
        else:
            st.info("No courses assigned.")

    # ---------------------
    # Student Features
    # ---------------------
    elif user['role'] == "Student":
        st.write("### Student Features")
        st.write("View Courses, Assignments, Fees, Hostel, Announcements")

        st.write("#### Courses & Assignments")
        courses = get_courses()
        for course in courses:
            st.write(f"**{course[1]}** (Lecturer: {course[2]})")
            assignments = get_assignments(course[0])
            for assign in assignments:
                st.write(f"- {assign[2]} (Due: {assign[4]})")

        st.write("#### Fees")
        fees = get_fees(user['id'])
        if fees:
            for f in fees:
                st.write(f"Amount: {f[2]}, Status: {f[3]}")
        else:
            st.info("No fees records.")

        st.write("#### Hostel Booking")
        hostel = get_hostel(user['id'])
        if hostel:
            for h in hostel:
                st.write(f"Room: {h[2]}, Status: {h[3]}")
        else:
            st.info("No hostel booking.")

        st.write("#### Announcements")
        announcements = get_announcements()
        for ann in announcements:
            st.write(f"**{ann[1]}** ({ann[3]}): {ann[2]}")

# -------------------------
# Logout
# -------------------------
elif choice == "Logout":
    st.session_state.logged_in = False
    st.session_state.user = None
    st.success("You have logged out.")
