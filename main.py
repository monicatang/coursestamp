from flask import flash, Flask, render_template, request, redirect
from forms import QueryForm
from flask_wtf.csrf import CSRFProtect
import os, sys, houndify
import speech_recognition as sr
from phrase_occurrences import find_occurrences
import re

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)
csrf = CSRFProtect(app)

search_string = ''

SECRET_KEY = 'go bears'
app.config['SECRET_KEY'] = SECRET_KEY
client_id = app.config['HOUNDIFY_ID']
client_key = app.config['HOUNDIFY_KEY']
user_id = app.config['HOUNDIFY_USR']
client = houndify.StreamingHoundClient(client_id, client_key, user_id, sampleRate=8000)

@app.route('/', methods=('GET', 'POST'))
def home():
    print("hello")
    select = QueryForm(request.form)
    if request.method == 'POST':
        prof_name = request.form['profs']
        return redirect('/'+prof_name)
    opt_list = [x[0] for x in os.walk('examples')]
    print(opt_list)
    opt_list = [i.replace('examples\\', '') for i in opt_list if 'raw_subtitles' not in i]
    opt_list = [i.replace('examples/', '') for i in opt_list if 'raw_subtitles' not in i]
    opt_list = [(i.replace('_', ' ').title(), i) for i in opt_list]
    print(opt_list)
    return render_template('index.html', form=select, option_list=opt_list[1:], dropdown = True, search_menu = False)

@app.route('/<prof_name>', methods=('GET', 'POST'))
def pick_prof(prof_name):
    search = QueryForm(request.form)
    if request.method == 'POST':
        search_string = request.form['query']
        return redirect('/'+prof_name+'/'+search_string)
    f = open("examples/"+prof_name+"/"+prof_name+".txt", "r")
    prof_name = prof_name.replace("_", " ").title()
    course_name = f.read()
    return render_template('index.html', form=search, dropdown = False, search_menu = True, course_name=course_name, prof_name=prof_name)

@app.route('/<prof_name>/<search_term>', methods=('GET', 'POST'))
def results(prof_name, search_term):
    titles, urls, raw_phrases, term_idxes = find_occurrences(search_term, "examples/"+prof_name+"/"+prof_name+".json")
    leftContexts = []
    rightContexts = []
    titleContexts = []
    for idx, phrase in enumerate(raw_phrases):
        leftContexts.append(phrase[:term_idxes[idx]])
        rightContexts.append(phrase[term_idxes[idx]+len(search_term):])
        titleContexts.append(titles[idx])
    search = QueryForm(request.form)
    if request.method == 'POST':
        search_string = request.form['query']
        return redirect('/'+prof_name+'/'+search_string)
    return render_template('index.html', form=search, 
        name=search_term, urls=urls, leftContexts=leftContexts, 
        rightContexts=rightContexts, titleContexts=titleContexts, showViewer=len(urls)>0, dropdown = False, search_menu = True)

def listen():
    search = QueryForm(request.form)
    rec = sr.Recognizer()
    with sr.Microphone() as source:
        rec.adjust_for_ambient_noise(source)
        app.logger.info("I'm listening...")
        audio = rec.listen(source, phrase_time_limit=5)
    search_string = rec.recognize_houndify(audio, client_id, client_key)
    return search_string

if __name__ == "__main__":
    app.run(debug=True)