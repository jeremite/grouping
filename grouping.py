from flask import Flask,render_template,request,redirect,url_for
import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq

app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
app.config['UPLOAD_PATH'] = os.path.join(APP_ROOT, 'OutputFolder')
app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.parquet']
@app.route('/')
def home():
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files, fileName='')


@app.route('/', methods=['POST'])
def upload_files():
    for uploaded_file in request.files.getlist('file'):
        filename = uploaded_file.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        #uploaded_file.save(uploaded_file.filename)
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

@app.route('/Login')
def Login():
    return render_template('login.html')

@app.route('/<string:name>')
def show(name):
    csvFile = os.path.join(app.config['UPLOAD_PATH'], name)
    files = os.listdir(app.config['UPLOAD_PATH'])
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,  engine='pyarrow')
    return render_template('index.html', files=files, fileName= name, data=table.to_html())

if __name__ == '__main__':
    app.run(port=5000, debug=True)
