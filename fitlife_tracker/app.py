from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

# Inicialização do app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fitlife.db"
app.config["SECRET_KEY"] = "minha_chave_super_secreta"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Configuração de login
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# ======================
# MODELOS
# ======================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    meals = db.relationship("Meal", backref="user", lazy=True)
    workouts = db.relationship("Workout", backref="user", lazy=True)
    progresses = db.relationship("Progress", backref="user", lazy=True)


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    calories = db.Column(db.Integer)


class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    exercise = db.Column(db.String(100))
    sets = db.Column(db.Integer)
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)


class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=True)
    body_fat = db.Column(db.Float, nullable=True)
    notes = db.Column(db.String(200), nullable=True)

# ======================
# FORMULÁRIOS
# ======================
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange

class RegisterForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirmar Senha", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Registrar")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")

class MealForm(FlaskForm):
    description = StringField("Descrição", validators=[DataRequired()])
    calories = IntegerField("Calorias", validators=[DataRequired()])
    submit = SubmitField("Salvar")

class WorkoutForm(FlaskForm):
    exercise = StringField("Exercício", validators=[DataRequired()])
    sets = IntegerField("Séries", validators=[DataRequired(), NumberRange(min=1)])
    reps = IntegerField("Repetições", validators=[DataRequired(), NumberRange(min=1)])
    weight = FloatField("Peso (kg)")
    submit = SubmitField("Salvar")

class ProgressForm(FlaskForm):
    weight = FloatField("Peso (kg)", validators=[DataRequired()])
    height = FloatField("Altura (cm)")
    body_fat = FloatField("Gordura Corporal (%)")
    notes = StringField("Observações", validators=[Length(max=200)])
    submit = SubmitField("Salvar")

# ======================
# LOGIN MANAGER
# ======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ======================
# ROTAS DE AUTENTICAÇÃO
# ======================
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Login realizado!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Email ou senha inválidos.", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("login"))

# ======================
# DASHBOARD
# ======================
@app.route("/")
@login_required
def dashboard():
    last_meal = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.date.desc()).first()
    last_workout = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).first()
    last_progress = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.date.desc()).first()

    return render_template(
        "dashboard.html",
        last_meal=last_meal,
        last_workout=last_workout,
        last_progress=last_progress
    )

# ======================
# CRUD MEALS
# ======================
@app.route("/meals")
@login_required
def meals():
    meals = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.date.desc()).all()
    return render_template("meals.html", meals=meals)

@app.route("/meals/new", methods=["GET", "POST"])
@login_required
def new_meal():
    form = MealForm()
    if form.validate_on_submit():
        meal = Meal(user_id=current_user.id, description=form.description.data, calories=form.calories.data)
        db.session.add(meal)
        db.session.commit()
        flash("Refeição adicionada!", "success")
        return redirect(url_for("meals"))
    return render_template("meal_form.html", form=form, title="Nova Refeição")

@app.route("/meals/edit/<int:meal_id>", methods=["GET", "POST"])
@login_required
def edit_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    if meal.user_id != current_user.id:
        flash("Acesso negado!", "danger")
        return redirect(url_for("meals"))
    form = MealForm(obj=meal)
    if form.validate_on_submit():
        meal.description = form.description.data
        meal.calories = form.calories.data
        db.session.commit()
        flash("Refeição atualizada!", "success")
        return redirect(url_for("meals"))
    return render_template("meal_form.html", form=form, title="Editar Refeição")

@app.route("/meals/delete/<int:meal_id>")
@login_required
def delete_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    if meal.user_id != current_user.id:
        flash("Acesso negado!", "danger")
        return redirect(url_for("meals"))
    db.session.delete(meal)
    db.session.commit()
    flash("Refeição excluída!", "info")
    return redirect(url_for("meals"))

# ======================
# CRUD WORKOUTS
# ======================
@app.route("/workouts")
@login_required
def workouts():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
    return render_template("workouts.html", workouts=workouts)

@app.route("/workouts/new", methods=["GET", "POST"])
@login_required
def new_workout():
    form = WorkoutForm()
    if form.validate_on_submit():
        workout = Workout(
            user_id=current_user.id,
            exercise=form.exercise.data,
            sets=form.sets.data,
            reps=form.reps.data,
            weight=form.weight.data
        )
        db.session.add(workout)
        db.session.commit()
        flash("Treino registrado!", "success")
        return redirect(url_for("workouts"))
    return render_template("workout_form.html", form=form, title="Novo Treino")

@app.route("/workouts/edit/<int:workout_id>", methods=["GET", "POST"])
@login_required
def edit_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        flash("Acesso negado!", "danger")
        return redirect(url_for("workouts"))
    form = WorkoutForm(obj=workout)
    if form.validate_on_submit():
        workout.exercise = form.exercise.data
        workout.sets = form.sets.data
        workout.reps = form.reps.data
        workout.weight = form.weight.data
        db.session.commit()
        flash("Treino atualizado!", "success")
        return redirect(url_for("workouts"))
    return render_template("workout_form.html", form=form, title="Editar Treino")

@app.route("/workouts/delete/<int:workout_id>")
@login_required
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        flash("Acesso negado!", "danger")
        return redirect(url_for("workouts"))
    db.session.delete(workout)
    db.session.commit()
    flash("Treino excluído!", "info")
    return redirect(url_for("workouts"))

# ======================
# CRUD PROGRESS
# ======================
@app.route("/progress")
@login_required
def progress():
    progresses = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.date.desc()).all()
    return render_template("progress.html", progresses=progresses)

@app.route("/progress/new", methods=["GET", "POST"])
@login_required
def new_progress():
    form = ProgressForm()
    if form.validate_on_submit():
        progress = Progress(
            user_id=current_user.id,
            weight=form.weight.data,
            height=form.height.data,
            body_fat=form.body_fat.data,
            notes=form.notes.data
        )
        db.session.add(progress)
        db.session.commit()
        flash("Progresso registrado!", "success")
        return redirect(url_for("progress"))
    return render_template("progress_form.html", form=form, title="Novo Progresso")

@app.route("/progress/edit/<int:progress_id>", methods=["GET", "POST"])
@login_required
def edit_progress(progress_id):
    progress = Progress.query.get_or_404(progress_id)
    if progress.user_id != current_user.id:
        flash("Acesso negado!", "danger")
        return redirect(url_for("progress"))
    form = ProgressForm(obj=progress)
    if form.validate_on_submit():
        progress.weight = form.weight.data
        progress.height = form.height.data
        progress.body_fat = form.body_fat.data
        progress.notes = form.notes.data
        db.session.commit()
        flash("Progresso atualizado!", "success")
        return redirect(url_for("progress"))
    return render_template("progress_form.html", form=form, title="Editar Progresso")

@app.route("/progress/delete/<int:progress_id>")
@login_required
def delete_progress(progress_id):
    progress = Progress.query.get_or_404(progress_id)
    if progress.user_id != current_user.id:
        flash("Acesso negado!", "danger")
        return redirect(url_for("progress"))
    db.session.delete(progress)
    db.session.commit()
    flash("Progresso excluído!", "info")
    return redirect(url_for("progress"))

# ======================
# RODAR APP
# ======================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

from flask import jsonify
import json
from sqlalchemy import func
from datetime import datetime, timedelta

@app.route("/")
@login_required
def dashboard():
    # Últimos registros individuais
    last_meal = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.date.desc()).first()
    last_workout = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).first()
    last_progress = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.date.desc()).first()

    # --- Dados para gráficos ---
    # Evolução do peso
    weight_data = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.date).all()
    weight_labels = [p.date.strftime("%d/%m") for p in weight_data]
    weight_values = [p.weight for p in weight_data]

    # Calorias por dia (últimos 7 dias)
    today = datetime.today()
    last_7_days = today - timedelta(days=6)
    calories_data = (
        db.session.query(func.date(Meal.date), func.sum(Meal.calories))
        .filter(Meal.user_id == current_user.id, Meal.date >= last_7_days)
        .group_by(func.date(Meal.date))
        .order_by(func.date(Meal.date))
        .all()
    )
    calories_labels = [c[0].strftime("%d/%m") for c in calories_data]
    calories_values = [c[1] for c in calories_data]

    # Treinos por semana (últimas 6 semanas)
    last_6_weeks = today - timedelta(weeks=6)
    workouts_data = (
        db.session.query(func.strftime("%W", Workout.date), func.count(Workout.id))
        .filter(Workout.user_id == current_user.id, Workout.date >= last_6_weeks)
        .group_by(func.strftime("%W", Workout.date))
        .all()
    )
    workout_labels = [f"Semana {w[0]}" for w in workouts_data]
    workout_values = [w[1] for w in workouts_data]

    return render_template(
        "dashboard.html",
        last_meal=last_meal,
        last_workout=last_workout,
        last_progress=last_progress,
        weight_labels=json.dumps(weight_labels),
        weight_values=json.dumps(weight_values),
        calories_labels=json.dumps(calories_labels),
        calories_values=json.dumps(calories_values),
        workout_labels=json.dumps(workout_labels),
        workout_values=json.dumps(workout_values)
    )
