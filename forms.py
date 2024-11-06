from unicodedata import category
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

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
