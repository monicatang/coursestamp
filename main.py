from flask import flash, Flask, render_template, request, redirect
from forms import QueryForm
from flask_wtf.csrf import CSRFProtect
import os, sys, houndify
import speech_recognition as sr
from phrase_occurrences import find_occurrences

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)
csrf = CSRFProtect(app)

search_string = ''
RESULT_LIMIT = 100
SECRET_KEY = 'go bears'
app.config['SECRET_KEY'] = SECRET_KEY
client_id = app.config['HOUNDIFY_ID']
client_key = app.config['HOUNDIFY_KEY']
user_id = app.config['HOUNDIFY_USR']
client = houndify.StreamingHoundClient(client_id, client_key, user_id, sampleRate=8000)

@app.route('/', methods=('GET', 'POST'))
def home():
    search = QueryForm(request.form)
    if request.method == 'POST':
        if request.form['search'] == "voice":
            search_string = listen()
        else:
            search_string = request.form['query']
        return redirect('/'+search_string)
    return render_template('index.html', form=search)

@app.route('/<search_term>', methods=('GET', 'POST'))
def results(search_term):
    titles, urls, raw_phrases, term_idxes = find_occurrences(search_term, "examples/andrew_ng/andrew_ng.json")
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
        return redirect('/'+search_string)
    return render_template('index.html', form=search, 
        name=search_term, urls=urls[:RESULT_LIMIT], leftContexts=leftContexts,
        rightContexts=rightContexts, titleContexts=titleContexts, showViewer=len(urls)>0)

def listen():
    search = QueryForm(request.form)
    rec = sr.Recognizer()
    with sr.Microphone() as source:
        rec.adjust_for_ambient_noise(source)
        app.logger.info("I'm listening...")
        audio = rec.listen(source, phrase_time_limit=3)
    search_string = rec.recognize_houndify(audio, client_id, client_key)
    return search_string

if __name__ == "__main__":
    app.run(debug=True)