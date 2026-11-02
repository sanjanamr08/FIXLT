
from pathlib import Path

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)

from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)

from werkzeug.security import (
    generate_password_hash, check_password_hash
)


# Application setup
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

app.config["SECRET_KEY"] = "fixit-development-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + str(BASE_DIR / "database" / "fixit.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

(BASE_DIR / "database").mkdir(exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# User database
class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=False)

    email = db.Column(
        db.String(150), unique=True, nullable=False
    )

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(30), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


# Login management
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Homepage
@app.route("/")
def home():
    return render_template("index.html")


# Registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "")

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")

        elif len(name) > 120 or len(email) > 150:
            flash("Name or email is too long.", "error")

        elif role not in ["student", "teacher", "staff"]:
            flash("Please select a valid role.", "error")

        elif len(password) < 8:
            flash("Password must have at least 8 characters.", "error")

        elif password != confirm_password:
            flash("Passwords do not match.", "error")

        elif User.query.filter_by(email=email).first():
            flash("This email is already registered.", "error")

        else:

            user = User(
                name=name,
                email=email,
                role=role
            )

            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")

            return redirect(url_for("login"))

    return render_template("register.html")


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            flash(f"Welcome to FixIt, {user.name}!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# Dashboard
@app.route("/dashboard")
@login_required
def dashboard():

    return f"""
        <h1>Welcome to FixIt, {current_user.name}!</h1>
        <p>Your role: {current_user.role}</p>
        <a href="/logout">Logout</a>
    """


# Logout
@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have logged out successfully.", "success")

    return redirect(url_for("home"))


# Create database tables
with app.app_context():
    db.create_all()


# Run application
if __name__ == "__main__":
    app.run(debug=True)
