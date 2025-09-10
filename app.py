# app.py
import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from reportlab.pdfgen import canvas
import random
import os
import io

# ---------------------- Database ----------------------
DB_FILE = "myunispace.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()

def create_tables():
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
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        message TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT,
        course_name TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        course_code TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT,
        exam_date TEXT,
        center TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        course_code TEXT,
        date TEXT,
        status TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        course_code TEXT,
        filename TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        amount REAL,
        status TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS hostel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        room_number TEXT,
        status TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS forum (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        message TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS elections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT,
        candidate TEXT,
        timestamp TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        available INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        description TEXT,
        contact TEXT
    )''')
create_tables()
conn.commit()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------- Helpers ----------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def send_message(sender: str, receiver: str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (sender, receiver, message, timestamp) VALUES (?, ?, ?, ?)",
              (sender, receiver, message, timestamp))
    conn.commit()

def generate_pdf_bytes(text_lines):
    """Return PDF bytes for download (in-memory)."""
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf)
    y = 800
    for line in text_lines:
        pdf.drawString(50, y, line)
        y -= 18
        if y < 50:
            pdf.showPage()
            y = 800
    pdf.save()
    buf.seek(0)
    return buf.read()

def generate_pdf_file(path, text_lines):
    b = generate_pdf_bytes(text_lines)
    with open(path, "wb") as f:
        f.write(b)
    return path

def mpesa_payment(student: str, amount: float):
    status = random.choice(["SUCCESS", "FAILED"])  # simulate
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO payments (student, amount, status, timestamp) VALUES (?, ?, ?, ?)",
              (student, amount, status, timestamp))
    conn.commit()
    return status

def save_uploaded_file(uploaded_file, student, course_code="General"):
    filename = uploaded_file.name
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO assignments (student, course_code, filename, timestamp) VALUES (?, ?, ?, ?)",
              (student, course_code, filename, timestamp))
    conn.commit()
    return file_path

def save_camera_image(camera_image, username):
    filename = f"{username}_camera_{int(datetime.now().timestamp())}.png"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(camera_image.getbuffer())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO assignments (student, course_code, filename, timestamp) VALUES (?, ?, ?, ?)",
              (username, "General", filename, timestamp))
    conn.commit()
    return file_path

# Seed simple library & job board (only once)
def seed_sample_data():
    c.execute("SELECT count(*) FROM library")
    if c.fetchone()[0] == 0:
        sample_books = [
            ("Discrete Math", "Rosen", 3),
            ("Algorithm Design", "Kleinberg", 2),
            ("Database Systems", "Elmasri", 1),
            ("Operating Systems", "Tanenbaum", 2)
        ]
        c.executemany("INSERT INTO library (title, author, available) VALUES (?, ?, ?)", sample_books)
    c.execute("SELECT count(*) FROM jobs")
    if c.fetchone()[0] == 0:
        sample_jobs = [
            ("Backend Intern", "Acme Ltd", "Work on APIs", "jobs@acme.example"),
            ("Data Analyst", "DataCorp", "Analyze student data", "hr@datacorp.example")
        ]
        c.executemany("INSERT INTO jobs (title, company, description, contact) VALUES (?, ?, ?, ?)", sample_jobs)
    conn.commit()
seed_sample_data()

# ---------------------- Streamlit App ----------------------
st.set_page_config(page_title="MyUniSpace", layout="wide")
st.title("🌐 MyUniSpace — University Portal (Single-file)")

# AUTH UI
if 'username' not in st.session_state:
    auth_choice = st.sidebar.selectbox("Auth", ["Login", "Register"])

    if auth_choice == "Register":
        st.header("Register")
        role = st.selectbox("Role", ["Student", "Lecturer", "Admin"])
        full_name = st.text_input("Full name")
        student_id = st.text_input("Admission/Student ID (optional)")
        username = st.text_input("Username")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        password = st.text_input("Password", type="password")
        if st.button("Register Account"):
            if not username or not password:
                st.error("Username and password are required")
            else:
                try:
                    c.execute("INSERT INTO users (role, full_name, student_id, username, email, phone, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (role, full_name, student_id, username, email, phone, hash_password(password)))
                    conn.commit()
                    st.success("Registered successfully — please login from the sidebar")
                except Exception as e:
                    st.error("Could not register (maybe username exists).")

    elif auth_choice == "Login":
        st.header("Login")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        if st.button("Login"):
            c.execute("SELECT role, password FROM users WHERE username=?", (username_input,))
            row = c.fetchone()
            if row and verify_password(password_input, row[1]):
                st.session_state['username'] = username_input
                st.session_state['role'] = row[0]
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

# MAIN DASHBOARD (for logged-in users)
if 'username' in st.session_state:
    username = st.session_state['username']
    role = st.session_state['role']
    st.sidebar.write(f"Logged in as: **{username}** ({role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    # COMMON QUICK LINKS
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Quick actions**")
    if st.sidebar.button("My Inbox"):
        st.experimental_set_query_params(view="inbox")
    if st.sidebar.button("My Assignments"):
        st.experimental_set_query_params(view="assignments")

    # ---------- STUDENT ----------
    if role == "Student":
        st.header(f"Student Dashboard — {username}")

        # PROFILE & COURSES
        st.subheader("Profile & Courses")
        c.execute("SELECT full_name, student_id, email, phone FROM users WHERE username=?", (username,))
        profile = c.fetchone()
        st.write("Name:", profile[0] if profile else "")
        st.write("Student ID:", profile[1] if profile else "")
        st.write("Email:", profile[2] if profile else "")
        st.write("Phone:", profile[3] if profile else "")

        # REGISTER COURSE
        st.subheader("Course Registration")
        new_course = st.text_input("Course code to register (e.g. CS101)")
        if st.button("Register Course"):
            if new_course:
                c.execute("INSERT INTO registrations (student, course_code) VALUES (?, ?)", (username, new_course))
                conn.commit()
                st.success(f"Registered {new_course}")

        # VIEW REGISTERED COURSES
        c.execute("SELECT course_code FROM registrations WHERE student=?", (username,))
        reg_courses = [r[0] for r in c.fetchall()]
        st.write("Registered courses:", reg_courses if reg_courses else "None")

        # ASSIGNMENTS (upload + camera)
        st.subheader("Assignments")
        course_for_assign = st.selectbox("Select course", ["General"] + reg_courses, key="assign_course")
        uploaded = st.file_uploader("Upload file for assignment", type=["pdf","docx","doc","jpg","png"])
        cam = st.camera_input("Or capture image with camera")
        if st.button("Submit Assignment"):
            if uploaded:
                path = save_uploaded_file(uploaded, username, course_for_assign)
                st.success("Assignment uploaded: " + os.path.basename(path))
            elif cam:
                path = save_camera_image(cam, username)
                st.success("Captured image saved as assignment: " + os.path.basename(path))
            else:
                st.error("Choose a file or capture an image.")

        # VIEW & DOWNLOAD OWN ASSIGNMENTS
        st.write("Your submissions:")
        c.execute("SELECT id, course_code, filename, timestamp FROM assignments WHERE student=?", (username,))
        assigns = c.fetchall()
        for a in assigns:
            st.write(f"{a[3]} | {a[1]} | {a[2]}")
            file_path = os.path.join(UPLOAD_DIR, a[2])
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.download_button(f"Download {a[2]}", data=f.read(), file_name=a[2])

        # FEES & PAYMENTS
        st.subheader("Fees & Payments")
        amount = st.number_input("Amount (KES)", min_value=1.0, value=100.0, step=1.0)
        if st.button("Pay (simulate M-Pesa)"):
            status = mpesa_payment(username, amount)
            st.success(f"Payment status: {status}")
        if st.button("View Payments"):
            c.execute("SELECT amount, status, timestamp FROM payments WHERE student=?", (username,))
            pays = c.fetchall()
            for p in pays:
                st.write(f"{p[2]} | KES {p[0]} | {p[1]}")
        if st.button("Download Fee Statement (PDF)"):
            c.execute("SELECT amount, status, timestamp FROM payments WHERE student=?", (username,))
            pays = c.fetchall()
            lines = [f"Fee Statement for {username}", f"Generated: {datetime.now()}"]
            for p in pays:
                lines.append(f"{p[2]} | KES {p[0]} | {p[1]}")
            pdf_bytes = generate_pdf_bytes(lines)
            st.download_button("Download Fee Statement PDF", data=pdf_bytes, file_name=f"fee_statement_{username}.pdf")

        # EXAMS & RESULTS
        st.subheader("Exams & Results")
        if st.button("View Exam Timetable"):
            c.execute("SELECT course_code, exam_date, center FROM exams")
            exams = c.fetchall()
            if exams:
                for ex in exams:
                    st.write(f"{ex[0]} | {ex[1]} | {ex[2]}")
            else:
                st.info("No exams scheduled.")

        if st.button("Generate Exam Card (PDF)"):
            c.execute("SELECT course_code, exam_date, center FROM exams")
            exams = c.fetchall()
            lines = [f"Exam Card — {username}", f"Generated: {datetime.now()}"]
            for ex in exams:
                lines.append(f"{ex[0]} - {ex[1]} - {ex[2]}")
            pdf_bytes = generate_pdf_bytes(lines)
            st.download_button("Download Exam Card PDF", data=pdf_bytes, file_name=f"exam_card_{username}.pdf")

        if st.button("View Results (sample)"):
            # Random sample grades (demo)
            c.execute("SELECT course_code FROM registrations WHERE student=?", (username,))
            regs = c.fetchall()
            if not regs:
                st.info("No registered courses to show results.")
            else:
                for r in regs:
                    st.write(f"{r[0]} : {random.choice(['A','B','C','D','E','F'])}")

        # HOSTEL
        st.subheader("Hostel")
        pref_room = st.text_input("Preferred room number")
        if st.button("Apply for Hostel"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO hostel (student, room_number, status, timestamp) VALUES (?, ?, ?, ?)",
                      (username, pref_room, "Pending", timestamp))
            conn.commit()
            st.success("Hostel application submitted")
        if st.button("View Hostel Application Status"):
            c.execute("SELECT room_number, status, timestamp FROM hostel WHERE student=?", (username,))
            apps = c.fetchall()
            for a in apps:
                st.write(f"{a[2]} | Room: {a[0]} | Status: {a[1]}")

        # FORUM
        st.subheader("Forum")
        forum_post = st.text_area("Write a forum post")
        if st.button("Post to Forum"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO forum (user, message, timestamp) VALUES (?, ?, ?)", (username, forum_post, ts))
            conn.commit()
            st.success("Posted")
        if st.button("View Forum Posts"):
            c.execute("SELECT user, message, timestamp FROM forum ORDER BY id DESC")
            posts = c.fetchall()
            for p in posts:
                st.write(f"{p[2]} | {p[0]}: {p[1]}")

        # ELECTIONS
        st.subheader("Elections")
        candidate = st.text_input("Candidate name to vote for")
        if st.button("Vote"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO elections (student, candidate, timestamp) VALUES (?, ?, ?)", (username, candidate, ts))
            conn.commit()
            st.success("Vote recorded")

        # MISC: Library & Jobs
        st.subheader("Library")
        q = st.text_input("Search library (title or author)")
        if st.button("Search Library"):
            c.execute("SELECT title, author, available FROM library WHERE title LIKE ? OR author LIKE ?", (f"%{q}%", f"%{q}%"))
            books = c.fetchall()
            for b in books:
                st.write(f"{b[0]} by {b[1]} — Available: {b[2]}")

        st.subheader("Jobs & Internships")
        if st.button("View Job Board"):
            c.execute("SELECT title, company, description, contact FROM jobs")
            jobs = c.fetchall()
            for j in jobs:
                st.write(f"{j[0]} — {j[1]} | {j[2]} | Contact: {j[3]}")

        # MESSAGES (quick)
        st.subheader("Messaging")
        to = st.text_input("Send message to (username)")
        body = st.text_area("Message")
        if st.button("Send"):
            if to and body:
                send_message(username, to, body)
                st.success("Message sent")

    # ---------- LECTURER ----------
    elif role == "Lecturer":
        st.header(f"Lecturer Dashboard — {username}")

        # Add / View Courses
        st.subheader("Courses")
        lec_course_code = st.text_input("Course Code")
        lec_course_name = st.text_input("Course Name")
        if st.button("Add Course"):
            if lec_course_code and lec_course_name:
                c.execute("INSERT INTO courses (course_code, course_name) VALUES (?, ?)", (lec_course_code, lec_course_name))
                conn.commit()
                st.success("Course added")

        if st.button("View All Courses"):
            c.execute("SELECT course_code, course_name FROM courses")
            for course in c.fetchall():
                st.write(course[0], "-", course[1])

        # Post exams
        st.subheader("Exams")
        exam_course = st.text_input("Course Code for exam", key="lec_exam_course")
        exam_date = st.date_input("Exam Date", key="lec_exam_date")
        exam_center = st.text_input("Exam Center", key="lec_exam_center")
        if st.button("Post Exam Schedule"):
            c.execute("INSERT INTO exams (course_code, exam_date, center) VALUES (?, ?, ?)",
                      (exam_course, str(exam_date), exam_center))
            conn.commit()
            st.success("Exam scheduled")

        # View & grade assignments (simplified)
        st.subheader("Assignments")
        view_course = st.text_input("Course code to view submissions")
        if st.button("View Submissions"):
            c.execute("SELECT id, student, filename, timestamp FROM assignments WHERE course_code=?", (view_course,))
            subs = c.fetchall()
            if subs:
                for s in subs:
                    st.write(f"{s[3]} | {s[1]} | {s[2]}")
                    fp = os.path.join(UPLOAD_DIR, s[2])
                    if os.path.exists(fp):
                        with open(fp, "rb") as f:
                            st.download_button(f"Download {s[2]}", data=f.read(), file_name=s[2])
            else:
                st.info("No submissions")

        # Attendance
        st.subheader("Attendance")
        att_student = st.text_input("Student username")
        att_course = st.text_input("Course code")
        att_status = st.selectbox("Status", ["Present", "Absent"])
        if st.button("Mark Attendance"):
            date = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO attendance (student, course_code, date, status) VALUES (?, ?, ?, ?)",
                      (att_student, att_course, date, att_status))
            conn.commit()
            st.success("Attendance recorded")

        # Messaging & Inbox
        st.subheader("Messaging")
        to = st.text_input("Send message to (username)")
        body = st.text_area("Message body")
        if st.button("Send Message"):
            if to and body:
                send_message(username, to, body)
                st.success("Message sent")
        if st.button("View Inbox"):
            c.execute("SELECT sender, message, timestamp FROM messages WHERE receiver=?", (username,))
            msgs = c.fetchall()
            for m in msgs:
                st.write(f"{m[2]} | {m[0]}: {m[1]}")

    # ---------- ADMIN ----------
    elif role == "Admin":
        st.header(f"Admin Dashboard — {username}")

        # Manage users
        st.subheader("Users")
        if st.button("View All Users"):
            c.execute("SELECT id, role, username, full_name, email, phone FROM users")
            for u in c.fetchall():
                st.write(f"{u[0]} | {u[1]} | {u[2]} | {u[3]} | {u[4]} | {u[5]}")

        # Manage courses
        st.subheader("Courses")
        new_code = st.text_input("Course code")
        new_name = st.text_input("Course name")
        if st.button("Create Course"):
            if new_code and new_name:
                c.execute("INSERT INTO courses (course_code, course_name) VALUES (?, ?)", (new_code, new_name))
                conn.commit()
                st.success("Course created")
        if st.button("View Courses"):
            c.execute("SELECT * FROM courses")
            for row in c.fetchall():
                st.write(row)

        # Exams
        st.subheader("Exams")
        if st.button("View Exams"):
            c.execute("SELECT * FROM exams")
            for e in c.fetchall():
                st.write(e)
        # Create exam as admin
        adm_ex_course = st.text_input("Exam course code (admin)")
        adm_ex_date = st.date_input("Exam date (admin)")
        adm_ex_center = st.text_input("Exam center (admin)")
        if st.button("Create Exam (admin)"):
            c.execute("INSERT INTO exams (course_code, exam_date, center) VALUES (?, ?, ?)",
                      (adm_ex_course, str(adm_ex_date), adm_ex_center))
            conn.commit()
            st.success("Exam created")

        # Payments
        st.subheader("Payments")
        if st.button("View All Payments"):
            c.execute("SELECT * FROM payments")
            for p in c.fetchall():
                st.write(p)

        # Assignments
        st.subheader("Assignments")
        if st.button("View All Assignments"):
            c.execute("SELECT * FROM assignments ORDER BY id DESC")
            for a in c.fetchall():
                st.write(a)
                fp = os.path.join(UPLOAD_DIR, a[3])
                if os.path.exists(fp):
                    with open(fp, "rb") as f:
                        st.download_button(f"Download {a[3]}", data=f.read(), file_name=a[3])

        # Hostel
        st.subheader("Hostel applications")
        if st.button("View Hostels"):
            c.execute("SELECT * FROM hostel")
            for h in c.fetchall():
                st.write(h)
        if st.button("Approve all pending hostels (demo)"):
            c.execute("UPDATE hostel SET status='Approved' WHERE status='Pending'")
            conn.commit()
            st.success("All pending hostel applications approved (demo)")

        # Forum
        st.subheader("Forum Moderation")
        if st.button("View Forum Posts"):
            c.execute("SELECT * FROM forum ORDER BY id DESC")
            for p in c.fetchall():
                st.write(p)

        # Elections
        st.subheader("Elections")
        if st.button("View Votes"):
            c.execute("SELECT candidate, count(*) FROM elections GROUP BY candidate")
            for row in c.fetchall():
                st.write(f"{row[0]} : {row[1]} votes")

        # Academic PDFs for any student
        st.subheader("Student Documents (Admin)")
        c.execute("SELECT username FROM users WHERE role='Student'")
        student_list = [s[0] for s in c.fetchall()]
        selected_student = st.selectbox("Select student", [""] + student_list)
        if selected_student:
            if st.button("Generate Exam Card for student"):
                c.execute("SELECT course_code, exam_date, center FROM exams")
                exams = c.fetchall()
                lines = [f"Exam Card for {selected_student}", f"Generated: {datetime.now()}"]
                for ex in exams:
                    lines.append(f"{ex[0]} - {ex[1]} - {ex[2]}")
                pdf_bytes = generate_pdf_bytes(lines)
                st.download_button("Download Exam Card PDF", data=pdf_bytes, file_name=f"exam_card_{selected_student}.pdf")
            if st.button("Generate Transcript for student"):
                c.execute("SELECT course_code FROM registrations WHERE student=?", (selected_student,))
                regs = c.fetchall()
                lines = [f"Transcript for {selected_student}", f"Generated: {datetime.now()}"]
                for r in regs:
                    lines.append(f"{r[0]} : {random.choice(['A','B','C','D','E'])}")
                pdf_bytes = generate_pdf_bytes(lines)
                st.download_button("Download Transcript PDF", data=pdf_bytes, file_name=f"transcript_{selected_student}.pdf")
            if st.button("Generate Fee Statement for student"):
                c.execute("SELECT amount, status, timestamp FROM payments WHERE student=?", (selected_student,))
                pays = c.fetchall()
                lines = [f"Fee Statement for {selected_student}", f"Generated: {datetime.now()}"]
                for p in pays:
                    lines.append(f"{p[2]} | KES {p[0]} | {p[1]}")
                pdf_bytes = generate_pdf_bytes(lines)
                st.download_button("Download Fee Statement PDF", data=pdf_bytes, file_name=f"fee_statement_{selected_student}.pdf")

        # Job board & library (admin can add)
        st.subheader("Jobs & Library Admin")
        job_title = st.text_input("Job title")
        job_company = st.text_input("Company")
        job_descr = st.text_area("Description")
        job_contact = st.text_input("Contact email/phone")
        if st.button("Post Job"):
            c.execute("INSERT INTO jobs (title, company, description, contact) VALUES (?, ?, ?, ?)",
                      (job_title, job_company, job_descr, job_contact))
            conn.commit()
            st.success("Job posted")
        if st.button("View Jobs"):
            c.execute("SELECT title, company, description, contact FROM jobs")
            for j in c.fetchall():
                st.write(j)

        book_title = st.text_input("Book title")
        book_author = st.text_input("Book author")
        book_copies = st.number_input("Copies available", min_value=0, value=1)
        if st.button("Add Book"):
            c.execute("INSERT INTO library (title, author, available) VALUES (?, ?, ?)",
                      (book_title, book_author, int(book_copies)))
            conn.commit()
            st.success("Book added")
        if st.button("View Library"):
            c.execute("SELECT title, author, available FROM library")
            for b in c.fetchall():
                st.write(b)

    # Refresh commit
    conn.commit()

    

    

   


   
       
            
           

        
      
          
        

        


    
   
           
            
           
                
   
        
        
                
       
              
        
                
