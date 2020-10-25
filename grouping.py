from flask import Flask,render_template,request,redirect,url_for,jsonify,make_response
import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq
from dbhelper import DBHelper
import json
import datetime
import numpy as np
import sys




app = Flask(__name__)
DB = DBHelper()

DEFAULT_SELECT = "Choose Here"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
csvfolderpath = os.path.join(APP_ROOT, 'OutputFolder')

@app.route('/')
def home():
    files = os.listdir(csvfolderpath)
    return render_template('index.html', files=files, fileName='')

@app.route('/<string:name>')
def show(name):
    csvFile = os.path.join(csvfolderpath, name)
    files = os.listdir(csvfolderpath)
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile, nrows=20)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,  engine='pyarrow')
        table = table.head(20)
    return render_template('index.html', files=files, fileName= name, data=table.to_html())

@app.route('/selection',methods=['GET','POST'])
def selection():

    files = os.listdir(csvfolderpath)
    files = [file for file in files if not file.startswith(".")]

    #file_name = get_value_with_fallback("file_name")
    file_name = get_value_with_fallback('file_name')
    DB.add_file_name(file_name)
    #used_cols= post_values_with_fallback("used_cols")
    #target_cols= post_values_with_fallback("target_cols")
    #relations,cols = rel_col(file_name,used_cols,target_cols)
    cols = get_col(file_name)

    response = make_response(render_template("selection.html",
      files=files,
      file_name=file_name,
      cols=sorted(cols)))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("file_name", file_name, expires=expires)
    #response.set_cookie("used_cols", used_cols, expires=expires)
    #response.set_cookie("target_cols", target_cols, expires=expires)
    return response
    #return render_template('selection.html', files= files)


@app.route('/display')
def display():
    file_name = DB.get_file_name()
    data_ori,data_res,all_used_cols,res_used_cols = DB.get_table(file_name)
    ajax_df = json.dumps(data_ori.to_dict('records'))
    ajax_df_res = json.dumps(data_res.to_dict('records'))
    #res_df = data_res.to_html(index = False)
    all_used_cols = json.dumps(all_used_cols)
    res_used_cols = json.dumps(res_used_cols)
    params = DB.get_params()
    return render_template('display.html', all_used_cols=all_used_cols,res_used_cols=res_used_cols,
    ajax_df=ajax_df,ajax_df_res=ajax_df_res,file_name = file_name,indx=params['ft'],edit_col=params['gr_ft'])

@app.route('/createtable', methods=["POST"])
def createtable():
    file_name = DB.get_file_name()
    col1= post_value_with_fallback("col1")
    col2= post_value_with_fallback("col2")
    cnt_col= post_values_with_fallback("cnt_col")
    rate_col= post_values_with_fallback("rate_col")
    all_cols = list([col1]+[col2])+list(cnt_col)+list(rate_col)
    df = pd_read(file_name,used_cols=all_cols)
    DB.add_params(col1,col2,cnt_col,rate_col)
    DB.add_table(file_name,df)
    #expires = datetime.datetime.now() + datetime.timedelta(days=365)
    #response.set_cookie("col1", col1, expires=expires)
    #response.set_cookie("col2", col2, expires=expires)
    #response.set_cookie("cnt_col", cnt_col, expires=expires)
    #response.set_cookie("rate_col", rate_col, expires=expires)
    return redirect(url_for('display'))

@app.route('/update', methods=["POST"])
def update():
    #file_name = DB.get_file_name()''
    data = request.get_data()
    data = json.loads(data)
    #return jsonify(dict(redirect='display'))

    ajax_res_data,ajax_res_cols = do_update(data)
    #ajax_res_data='a'
    #ajax_res_cols='b'
    #return ajax_res_data
    return jsonify({'ajax_res_data': ajax_res_data,
                    'ajax_res_cols': ajax_res_cols})
    #                         request.form['source_language'],
    #                              request.form['dest_language'])})
    #return jsonify(dict(redirect='display'))

        #arr= request.get_json()
    #arr= request.get_json()
    #name = request.args.get('name', '')
    #age = int(request.args.get('age', '0'))
    #arr= get_json()
    #arr = json.dumps(arr)
    #return render_template('change_val.html',arr=data,inornot=inornot)
    #return redirect(url_for('.display',arr=json.dumps(data)))

def do_update(data):
    file_name = DB.get_file_name()
    #data = json.loads(data)
    ft_val,gr_ft_val = data['row_id'],data['edit']
    DB.update_table(file_name,ft_val,gr_ft_val)
    data_res,res_used_cols = DB.get_table(file_name,update=True)
    ajax_df_res = json.dumps(data_res.to_dict('records'))
    res_used_cols = json.dumps(res_used_cols)
    return ajax_df_res,res_used_cols

def pd_read(file_name,sample=None,used_cols=None):
    csvFile = os.path.join(csvfolderpath, file_name)
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile, nrows=sample,usecols=used_cols)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,engine='pyarrow',columns=used_cols)
        if sample:
            table = table.head(sample)
    return table

def get_col(file):
    if file==DEFAULT_SELECT:
        return [DEFAULT_SELECT]
    csvFile = os.path.join(csvfolderpath, file)
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile, nrows=10)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,  engine='pyarrow')
        table = table.head(10)
    cols = table.columns.tolist()
    return cols

def post_value_with_fallback(key):
    if request.form.get(key):
        return request.form.get(key)
    return DEFAULT_SELECT

def post_values_with_fallback(key):
    if request.form.getlist(key):
        return request.form.getlist(key)
    return DEFAULT_SELECT

def get_value_with_fallback(key):
    if request.args.get(key):
        return request.args.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULT_SELECT

def get_values_with_fallback(key):
    if request.args.getlist(key):
        return request.args.getlist(key)
    if request.cookies.getlist(key):
        return request.cookies.getlist(key)
    return DEFAULT_SELECT


'''

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
'''
if __name__ == '__main__':
    app.run(port=3000, debug=True)
