from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mentorconnect.db"
db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    interest = db.Column(db.String(100))

class Mentor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    skill = db.Column(db.String(100))
    approved = db.Column(db.Boolean, default=False)

class SessionBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))
    mentor_id = db.Column(db.Integer, db.ForeignKey("mentor.id"))
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    feedback = db.Column(db.String(300))
    rating = db.Column(db.Integer)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        s = Student(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            interest=request.form["interest"],
        )
        db.session.add(s)
        db.session.commit()
        flash("Registered successfully. Please login.")
        return redirect(url_for("student_login"))
    return render_template("register.html", role="student")

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        s = Student.query.filter_by(email=request.form["email"]).first()
        if s and check_password_hash(s.password, request.form["password"]):
            session["student_id"] = s.id
            return redirect(url_for("student_dashboard"))
        flash("Invalid credentials")
    return render_template("login.html", role="student")

@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect(url_for("student_login"))
    student = Student.query.get(session["student_id"])
    mentors = Mentor.query.filter_by(approved=True, skill=student.interest).all()
    bookings = SessionBooking.query.filter_by(student_id=student.id).all()
    return render_template("dashboard.html", role="student", user=student, mentors=mentors, bookings=bookings)

@app.route("/student/book/<int:mentor_id>")
def book_session(mentor_id):
    if "student_id" not in session:
        return redirect(url_for("student_login"))
    booking = SessionBooking(student_id=session["student_id"], mentor_id=mentor_id)
    db.session.add(booking)
    db.session.commit()
    flash("Session requested!")
    return redirect(url_for("student_dashboard"))

@app.route("/student/feedback/<int:booking_id>", methods=["POST"])
def give_feedback(booking_id):
    b = SessionBooking.query.get(booking_id)
    b.feedback = request.form["feedback"]
    b.rating = int(request.form["rating"])
    db.session.commit()
    return redirect(url_for("student_dashboard"))

@app.route("/mentor/register", methods=["GET", "POST"])
def mentor_register():
    if request.method == "POST":
        m = Mentor(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            skill=request.form["skill"],
        )
        db.session.add(m)
        db.session.commit()
        flash("Registered. Waiting for admin approval.")
        return redirect(url_for("mentor_login"))
    return render_template("register.html", role="mentor")

@app.route("/mentor/login", methods=["GET", "POST"])
def mentor_login():
    if request.method == "POST":
        m = Mentor.query.filter_by(email=request.form["email"]).first()
        if m and check_password_hash(m.password, request.form["password"]):
            session["mentor_id"] = m.id
            return redirect(url_for("mentor_dashboard"))
        flash("Invalid credentials")
    return render_template("login.html", role="mentor")

@app.route("/mentor/dashboard")
def mentor_dashboard():
    if "mentor_id" not in session:
        return redirect(url_for("mentor_login"))
    mentor = Mentor.query.get(session["mentor_id"])
    requests_ = SessionBooking.query.filter_by(mentor_id=mentor.id).all()
    return render_template("dashboard.html", role="mentor", user=mentor, requests=requests_)

@app.route("/mentor/respond/<int:booking_id>/<action>")
def respond_request(booking_id, action):
    b = SessionBooking.query.get(booking_id)
    b.status = "Accepted" if action == "accept" else "Rejected"
    db.session.commit()
    return redirect(url_for("mentor_dashboard"))

@app.route("/admin")
def admin_dashboard():
    students = Student.query.all()
    mentors = Mentor.query.all()
    return render_template("dashboard.html", role="admin", students=students, mentors=mentors)

@app.route("/admin/approve/<int:mentor_id>")
def approve_mentor(mentor_id):
    m = Mentor.query.get(mentor_id)
    m.approved = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)