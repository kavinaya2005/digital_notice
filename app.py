from flask import Flask, render_template, request, redirect, session, url_for
import pymysql
import os
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- FILE UPLOAD CONFIG ----------
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- EMAIL CONFIG ----------
EMAIL_ADDRESS = "kavinayaa256@gmail.com"
EMAIL_PASSWORD = "hhkpofwdmznynwmz"   # Gmail App Password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------- DATABASE CONNECTION ----------
def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="abcd1234",
        database="digital_notice_board",
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------- PASSWORD HASHING ----------
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ---------- EMAIL FUNCTIONS ----------
def send_email_notification(subject, message, recipient_email):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = recipient_email
        msg["Subject"] = subject

        body = f"""
        <html>
            <body>
                <h3>Digital Notice Board</h3>
                {message}
            </body>
        </html>
        """
        msg.attach(MIMEText(body, "html"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"Email sent to {recipient_email}")

    except Exception as e:
        print("Email Error:", e)

def notify_all_users(subject, message):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT email FROM users WHERE email IS NOT NULL AND email != ''")
    users = cur.fetchall()
    con.close()

    for user in users:
        send_email_notification(subject, message, user["email"])

# ---------- ALLOWED ROLES ----------
ALLOWED_ROLES = ["Student", "Admin", "HOD", "Faculty", "Placement", "Exam"]

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        con.close()

        if user and verify_password(password, user["password"]):
            session["user"] = user["username"]
            session["role"] = user["role"]
            session["department"] = user["department"]
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# ---------- SIGNUP ----------
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm = request.form.get("confirm_password")

    # New: role and department from form
    role = request.form.get("role", "Student")
    department = request.form.get("department", "").strip()

    if not all([username, email, password, confirm]):
        return render_template("login.html", signup_error="All fields are required")

    if password != confirm:
        return render_template("login.html", signup_error="Passwords do not match")

    if len(password) < 6:
        return render_template("login.html", signup_error="Password must be at least 6 characters")

    # Validate role and default department
    if role not in ALLOWED_ROLES:
        role = "Student"
    if not department:
        department = "General"

    con = get_db()
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        con.close()
        return render_template("login.html", signup_error="Username already exists")

    hashed = hash_password(password)

    try:
        cur.execute("""
            INSERT INTO users (username, email, password, role, department)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, hashed, role, department))

        con.commit()
        con.close()

        send_email_notification(
            "Welcome to Digital Notice Board",
            f"<p>Hello <b>{username}</b>,</p><p>Your account was created successfully.</p>",
            email
        )

        return render_template("login.html", signup_success="Account created successfully! Please login.")

    except Exception as e:
        con.close()
        return render_template("login.html", signup_error=str(e))

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user=session["user"],
        role=session["role"],
        department=session["department"]
    )

# ---------- POST NOTICE ----------
@app.route("/post_notice", methods=["GET", "POST"])
def post_notice():
    if "user" not in session:
        return redirect(url_for("login"))

    if session["role"] not in ["Admin", "HOD", "Faculty", "Placement", "Exam"]:
        return "Access Denied", 403

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category = request.form["category"]
        priority = request.form["priority"]
        target = request.form["target"]
        posted_by = session["user"]

        file = request.files.get("file")
        filename = None

        if file and file.filename:
            filename = f"{int(time.time())}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        con = get_db() 
        cur = con.cursor()
        cur.execute("""INSERT INTO notices 
            (title, content, category, priority, target, file, posted_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (title, content, category, priority, target, filename, posted_by))
        con.commit()
        con.close()

        notify_all_users(
            "New Notice Posted",
            f"<p><b>{title}</b></p><p>{content}</p><p>Posted by {posted_by}</p>"
        )

        return redirect(url_for("view_notices"))

    return render_template("post_notice.html")

# ---------- VIEW NOTICES ----------
@app.route("/view_notices")
def view_notices():
    if "user" not in session:
        return redirect(url_for("login"))

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM notices ORDER BY created_at DESC")
    notices = cur.fetchall()
    con.close()

    return render_template("view_notices.html", notices=notices)

# ---------- DELETE NOTICE ----------
@app.route("/delete_notice/<int:notice_id>", methods=["POST"])
def delete_notice(notice_id):
    if "user" not in session:
        return redirect(url_for("login"))

    con = get_db()
    cur = con.cursor()

    if session["role"] == "Admin":
        cur.execute("DELETE FROM notices WHERE id=%s", (notice_id,))
    else:
        cur.execute(
            "DELETE FROM notices WHERE id=%s AND posted_by=%s",
            (notice_id, session["user"])
        )

    con.commit()
    con.close()
    return redirect(url_for("view_notices"))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
