from flask import flash, Flask, render_template, request, redirect
from forms import QueryForm
from flask_wtf.csrf import CSRFProtect
import os
import sys
from phrase_occurances import find_occurances

app = Flask(__name__)
app.config.from_object(__name__)
csrf = CSRFProtect(app)

search_string = ''

SECRET_KEY = 'go bears'
app.config['SECRET_KEY'] = SECRET_KEY

@app.route('/', methods=('GET', 'POST'))
def home():
    search = QueryForm(request.form)
    if request.method == 'POST':
        search_string = request.form['query']
        return redirect('/'+search_string)
    return render_template('index.html', form=search)

@app.route('/<search_term>', methods=('GET', 'POST'))
def results(search_term):
    data = find_occurances(search_term, "andrew_ng.json")
    search = QueryForm(request.form)
    if request.method == 'POST':
        search_string = request.form['query']
        return redirect('/'+search_string)
    return render_template('index.html', form=search, name=search_term, data=data, showViewer=len(data)>0)

# @app.route('/background_process_test')
# def background_process_test():
#     print ("Hello")
#     return ("nothing")

# @app.route('/background_process_test2')
# def background_process_test2():
#     print ("Goodbye")
#     print(search_string)
#     return ("nothing")

if __name__ == "__main__":
    app.run(debug=True)