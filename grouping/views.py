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
import boto3
import s3fs

#from grouping import app


app = Flask(__name__)
DB = DBHelper()

DEFAULT_SELECT = "Choose Here"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
csvfolderpath = os.path.join(APP_ROOT, 'OutputFolder')

# s3 dataset
with open('config.json',"r") as f:
    configs= json.load(f)
bucket_name = configs['bucket_name']
pre = configs['prefix']
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)
s3_file_names = []
for obj in bucket.objects.filter(Delimiter='/',Prefix=pre):
    f = obj.key.split('/')[-1]
    if f:
        s3_file_names.append(f)


@app.route('/')
def home():
    files = os.listdir(csvfolderpath)
    files = [file for file in files if file.endswith(".csv") or file.endswith(".parquet")]
    s3_files = [file for file in s3_file_names if file.endswith(".csv") or file.endswith(".parquet")]
    df = pd_read(files[-1],sample=20)
    return render_template('index.html', files=files, s3_files = s3_files,fileName='')

@app.route('/<name>')
def show(name):
    #csvFile = os.path.join(csvfolderpath, name)
    files = os.listdir(csvfolderpath)
    #s3 s3_files
    #table = None
    '''
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile, nrows=20)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,  engine='pyarrow')
        table = table.head(20)
    '''
    df_show=pd_read(name,sample=20)
    #if df_show.empty:
    #    return render_template('index.html', files=files, fileName='')
    if df_show is not None:
        return render_template('index.html', files=files, fileName= name, data=df_show.to_html())
    else:
        return render_template('index.html', files=files, fileName='')

@app.route('/<s3_name>')
def s3_show(s3_name):

    #s3 s3_files
    df_s3_show = pd_read(name,sample=20,src='s3')
    #if df_show.empty:
    #    return render_template('index.html', files=files, fileName='')
    if df_s3_show is not None:
        return render_template('index_s3.html', files=files, fileName= name,data_s3=df_s3_show.to_html())
    else:
        return render_template('index_s3.html', files=files, fileName='')

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
    #data_ori,data_res,all_used_cols,res_used_cols = DB.get_table(file_name)
    #DB.get_defalt(file_name)
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
    all_cols = [c.strip() for c in all_cols]
    df = pd_read(file_name,used_cols=all_cols)
    #make col1 and col2 string
    df[[col1,col2]]=df[[col1,col2]].astype(str)
    DB.drop_table('params')
    DB.drop_table('updates')
    DB.drop_table(file_name+'_record_ori')
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
    return jsonify({'ajax_res_data': ajax_res_data,
                    'ajax_res_cols': ajax_res_cols})

@app.route('/reset')
def reset():
    file_name = DB.get_file_name()
    DB.get_defalt(file_name)
    DB.drop_table('updates')
    return "reset"

@app.route('/python_code', methods=["POST"])
def python_code():
    updates = DB.get_updates()
    col1,col2 = DB.get_params()['ft'],DB.get_params()['gr_ft']
    final = {}
    for u in updates:
        if u['id_val'].isdigit():
            id_val = int(u['id_val'])
        else:
            id_val = u['id_val']
        if u['gr_val'].isdigit():
            gr_val = int(u['gr_val'])
        else:
            gr_val = u['gr_val']
        final[id_val]=gr_val
    codes = "df[raw]=df[grouping].map('+final+')"
    if not final:
        final = "no updates"
    return render_template("python_code.html",final = final, col1=json.dumps(col1),col2=json.dumps(col2))

@app.route('/pyspark_code', methods=["POST"])
def pyspark_code():
    updates = DB.get_updates()
    col1,col2 = DB.get_params()['ft'],DB.get_params()['gr_ft']
    final = {}
    for u in updates:
        if u['id_val'].isdigit():
            id_val = int(u['id_val'])
        else:
            id_val = u['id_val']
        if u['gr_val'].isdigit():
            gr_val = int(u['gr_val'])
        else:
            gr_val = u['gr_val']
        final[id_val]=gr_val
    codes = "df[raw]=df[grouping].map('+final+')"
    if not final:
        final = "no updates"
    return render_template("pyspark_code.html",final = final, col1=json.dumps(col1),col2=json.dumps(col2))

def do_update(data):
    file_name = DB.get_file_name()
    #data = json.loads(data)
    ft_val,gr_ft_val = data['row_id'],data['edit']
    DB.add_updates(ft_val,gr_ft_val) #record the updates for future use when transfer back to python/pyspark code
    DB.update_table(file_name,ft_val,gr_ft_val) #update the database table
    data_res,res_used_cols = DB.get_table(file_name,update=True)
    ajax_df_res = json.dumps(data_res.to_dict('records'))
    res_used_cols = json.dumps(res_used_cols)
    return ajax_df_res,res_used_cols

def pd_read(file_name,src='test',sample=None,used_cols=None):
    if src=='test':
        csvFile = os.path.join(csvfolderpath, file_name)
    else:
        csvFile = os.path.join('s3://',bucket,pre,f)
    table=None
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
    app.run(port=5000, debug=True,host='0.0.0.0')
