from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, TextAreaField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, NumberRange, Length, Regexp

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters."),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$',
               message="Password must contain at least one letter, one number, and one special character.")
    ])
    submit = SubmitField('Register')

class BudgetForm(FlaskForm):
  category = StringField('Category', validators=[DataRequired(), Length(max=50)])
  limit_amount = DecimalField('Limit Amount', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
  submit = SubmitField('Add Budget')

class TransactionForm(FlaskForm):
  amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
  date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
  description = TextAreaField('Description', validators=[Length(max=200)])
  submit = SubmitField('Add Transaction')


class GoalForm(FlaskForm):
  goal_name = StringField('Goal Name', validators=[DataRequired(), Length(max=50)])
  target_amount = DecimalField('Target Amount', validators=[DataRequired(), NumberRange(min=1)], places=2)
  submit = SubmitField('Set Goal')
