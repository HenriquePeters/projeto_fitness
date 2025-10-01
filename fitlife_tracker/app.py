from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
import json

# -----------------------------
# Configurações iniciais
# -----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vidafit123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vidafit.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -----------------------------
# Modelos
# -----------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    meals = db.relationship('Meal', backref='user', lazy=True)
    workouts = db.relationship('Workout', backref='user', lazy=True)
    progresses = db.relationship('Progress', backref='user', lazy=True)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float)
    body_fat = db.Column(db.Float)
    notes = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# -----------------------------
# Forms
# -----------------------------
class RegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Login')

class MealForm(FlaskForm):
    description = StringField('Descrição', validators=[DataRequired()])
    calories = IntegerField('Calorias', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class WorkoutForm(FlaskForm):
    exercise = StringField('Exercício', validators=[DataRequired()])
    sets = IntegerField('Séries', validators=[DataRequired()])
    reps = IntegerField('Repetições', validators=[DataRequired()])
    weight = FloatField('Peso (kg)', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class ProgressForm(FlaskForm):
    weight = FloatField('Peso (kg)', validators=[DataRequired()])
    height = FloatField('Altura (cm)')
    body_fat = FloatField('Gordura (%)')
    notes = TextAreaField('Observações')
    submit = SubmitField('Salvar')

# -----------------------------
# Login Manager
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------------
# Rotas de Usuário
# -----------------------------
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Conta criada com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login falhou. Verifique email e senha', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -----------------------------
# Dashboard
# -----------------------------
@app.route("/")
@login_required
def dashboard():
    last_meal = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.date.desc()).first()
    last_workout = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).first()
    last_progress = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.date.desc()).first()

    weight_data = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.date).all()
    weight_labels = [p.date.strftime("%d/%m") for p in weight_data]
    weight_values = [p.weight for p in weight_data]

    today = datetime.today()
    last_7_days = today - timedelta(days=6)
    calories_data = db.session.query(func.date(Meal.date), func.sum(Meal.calories)) \
        .filter(Meal.user_id == current_user.id, Meal.date >= last_7_days) \
        .group_by(func.date(Meal.date)).all()
    calories_labels = [c[0].strftime("%d/%m") for c in calories_data]
    calories_values = [c[1] for c in calories_data]

    last_6_weeks = today - timedelta(weeks=6)
    workouts_data = db.session.query(func.strftime("%W", Workout.date), func.count(Workout.id)) \
        .filter(Workout.user_id == current_user.id, Workout.date >= last_6_weeks) \
        .group_by(func.strftime("%W", Workout.date)).all()
    workout_labels = [f"Semana {w[0]}" for w in workouts_data]
    workout_values = [w[1] for w in workouts_data]

    return render_template(
        'dashboard.html',
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

# -----------------------------
# CRUD Refeições
# -----------------------------
@app.route("/meals")
@login_required
def meals():
    meals = Meal.query.filter_by(user_id=current_user.id).order_by(Meal.date.desc()).all()
    return render_template('meals.html', meals=meals)

@app.route("/meal/new", methods=['GET','POST'])
@login_required
def new_meal():
    form = MealForm()
    if form.validate_on_submit():
        meal = Meal(description=form.description.data, calories=form.calories.data, user_id=current_user.id)
        db.session.add(meal)
        db.session.commit()
        flash('Refeição registrada!', 'success')
        return redirect(url_for('meals'))
    return render_template('meal_form.html', form=form, title="Nova Refeição")

@app.route("/meal/edit/<int:meal_id>", methods=['GET','POST'])
@login_required
def edit_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    form = MealForm(obj=meal)
    if form.validate_on_submit():
        meal.description = form.description.data
        meal.calories = form.calories.data
        db.session.commit()
        flash('Refeição atualizada!', 'success')
        return redirect(url_for('meals'))
    return render_template('meal_form.html', form=form, title="Editar Refeição")

@app.route("/meal/delete/<int:meal_id>")
@login_required
def delete_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    db.session.delete(meal)
    db.session.commit()
    flash('Refeição excluída!', 'success')
    return redirect(url_for('meals'))

# -----------------------------
# CRUD Treinos
# -----------------------------
@app.route("/workouts")
@login_required
def workouts():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
    return render_template('workouts.html', workouts=workouts)

@app.route("/workout/new", methods=['GET','POST'])
@login_required
def new_workout():
    form = WorkoutForm()
    if form.validate_on_submit():
        workout = Workout(
            exercise=form.exercise.data,
            sets=form.sets.data,
            reps=form.reps.data,
            weight=form.weight.data,
            user_id=current_user.id
        )
        db.session.add(workout)
        db.session.commit()
        flash('Treino registrado!', 'success')
        return redirect(url_for('workouts'))
    return render_template('workout_form.html', form=form, title="Novo Treino")

# -----------------------------
# CRUD Progresso
# -----------------------------
@app.route("/progress")
@login_required
def progress():
    progresses = Progress.query.filter_by(user_id=current_user.id).order_by(Progress.date.desc()).all()
    return render_template('progress.html', progresses=progresses)

@app.route("/progress/new", methods=['GET','POST'])
@login_required
def new_progress():
    form = ProgressForm()
    if form.validate_on_submit():
        prog = Progress(
            weight=form.weight.data,
            height=form.height.data,
            body_fat=form.body_fat.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(prog)
        db.session.commit()
        flash('Progresso registrado!', 'success')
        return redirect(url_for('progress'))
    return render_template('progress_form.html', form=form, title="Novo Registro de Progresso")

@app.route("/progress/edit/<int:progress_id>", methods=['GET','POST'])
@login_required
def edit_progress(progress_id):
    prog = Progress.query.get_or_404(progress_id)
    form = ProgressForm(obj=prog)
    if form.validate_on_submit():
        prog.weight = form.weight.data
        prog.height = form.height.data
        prog.body_fat = form.body_fat.data
        prog.notes = form.notes.data
        db.session.commit()
        flash('Progresso atualizado!', 'success')
        return redirect(url_for('progress'))
    return render_template('progress_form.html', form=form, title="Editar Registro de Progresso")

@app.route("/progress/delete/<int:progress_id>")
@login_required
def delete_progress(progress_id):
    prog = Progress.query.get_or_404(progress_id)
    db.session.delete(prog)
    db.session.commit()
    flash('Progresso excluído!', 'success')
    return redirect(url_for('progress'))


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Cria todas as tabelas
    app.run(debug=True)

