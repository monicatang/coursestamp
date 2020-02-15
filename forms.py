from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField

class QueryForm(FlaskForm):
    """Query form."""
    query = TextField('Query')
    submit = SubmitField('Search')