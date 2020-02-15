from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField, SelectField

class QueryForm(FlaskForm):
    """Query form."""
    query = TextField('Query')
    submit = SubmitField('Search')
    test = SubmitField('Test')
    profs = SelectField('Profs')