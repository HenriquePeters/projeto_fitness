from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegisterForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirmar Senha", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Cadastrar")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Senha", validators=[DataRequired()])
    submit = SubmitField("Entrar")

class MealForm(FlaskForm):
    description = StringField("Descrição da refeição", validators=[DataRequired(), Length(max=200)])
    calories = IntegerField("Calorias", validators=[DataRequired()])
    submit = SubmitField("Salvar")

class WorkoutForm(FlaskForm):
    exercise = StringField("Exercício", validators=[DataRequired(), Length(max=100)])
    sets = IntegerField("Séries", validators=[DataRequired()])
    reps = IntegerField("Repetições", validators=[DataRequired()])
    weight = FloatField("Peso (kg)")
    submit = SubmitField("Salvar")
    
class ProgressForm(FlaskForm):
    weight = FloatField("Peso (kg)", validators=[DataRequired()])
    height = FloatField("Altura (cm)")
    body_fat = FloatField("Gordura Corporal (%)")
    notes = StringField("Observações", validators=[Length(max=200)])
    submit = SubmitField("Salvar")
    