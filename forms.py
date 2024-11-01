from unicodedata import category
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Length

class BudgetForm(FlaskForm):
  category = StringField('Category', validators=[DataRequired(), Length(max=50)])
  limit_amount = DecimalField('Limit Amount', validators=[DataRequired(), NumberRange(min=0.01)], places=2)

class TransactionForm(FlaskForm):
  amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
  date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
  description = TextAreaField('Description', validators=[Length(max=200)])

