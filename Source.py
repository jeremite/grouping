from flask import Flask , render_template, request
import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq
import datetime
from flask import make_response,redirect,url_for,jsonify
import json
import numpy as np

app = Flask(__name__)
DEFAULT_SELECT = "Choose Here"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
csvfolderpath = os.path.join(APP_ROOT, 'OutputFolder')

@app.route('/')
def home():
    files = os.listdir(csvfolderpath)
    return render_template('index.html', files=files, fileName='')

@app.route('/display',methods=["GET","POST"])
def display():
    global new_data
    new_data = ""
    if not new_data:
    #file_name = get_value_with_fallback("file_name")
        file_name=get_value_with_fallback('file_name')
        col1= post_values_with_fallback("col1")
        col2= post_values_with_fallback("col2")
        cnt_col= post_values_with_fallback("cnt_col")
        rate_col= post_values_with_fallback("rate_col")
        print('col1',col1)
        print('col2',col2)
        if isinstance(col1,str):
            col1 = list(col1)
        if isinstance(col2,str):
            col2 = list(col2)
        all_used_cols = col1+col2+list(cnt_col)+list(rate_col)
        ajax_df,res_df,all_used_cols,res_old = get_ajax(file_name,col1,col2,cnt_col,rate_col)
        ajax_df = json.dumps(ajax_df)
        all_used_cols = json.dumps(all_used_cols)
        indx = json.dumps(col1[0])
    else:
        new_data = json.loads(new_data)
        [col_change,val_change],(col_idx,val1) = new_data.values()
        res_old.loc[res_old[col_idx]==val1,col_change]=val_change
        res_old = helper_agg(res_old,col2,cnt_col,rate_col)
        res_df =  helper_rename(res_out,col2)
        #res_df.loc[res_df['main_category']=='Dance','country_nunique']
    return render_template('display.html', all_used_cols=all_used_cols,
    ajax_df=ajax_df,res_df=res_df,file_name = file_name,indx=indx,col1=col1,col2=col2)

@app.route('/change_val',methods=["POST"])
def change_val():
    '''
    {
    {
  "state_nunique": "6",
  "row_id": "3D Printing"
}
  "country_nunique": "2237",
  "row_id": "3D Printing"
    }
    '''
    inornot = 'nonono'
    arr='abc'
    #arr= get_value_with_fallback('data')
    data = request.get_json()
    print('received: %s'%data)
    if data:
        return "success",200
    else:
        return "error", 400
        #arr= request.get_json()
    #arr= request.get_json()
    #name = request.args.get('name', '')
    #age = int(request.args.get('age', '0'))
    #arr= get_json()
    #arr = json.dumps(arr)
    #return render_template('change_val.html',arr=data,inornot=inornot)
    #return redirect(url_for('.display',arr=json.dumps(data)))

def get_json():
    if request.get_json():
        return request.get_json()
    return DEFAULT_SELECT


def get_ajax(file_name,col1,col2,cnt_col,rate_col,new_data=None):
    cols = list(col1)+list(col2)+list(cnt_col)+list(rate_col)
    table = pd_read(file_name,used_cols=cols)
    # do the calculation
    table_out = helper_agg(table,list(col1)+list(col2),cnt_col,rate_col)
    # get results
    res_out = table_out.copy()
    res_out.columns = res_out.columns.droplevel(1)
    res_out.reset_index(inplace=True)
    res_old = res_out.copy()
    res_out = helper_agg(res_out,col2,cnt_col,rate_col)
    # get two tables
    table_out = helper_rename(table_out,col1)
    res_out =  helper_rename(res_out,col2)

    # get columns for table_out used in ajax data
    all_used_cols = table_out.columns.tolist()
    return table_out.to_dict('records'),res_out.to_html(index = False),all_used_cols,res_old

def helper_agg(df,g_col,cnt_col,rate_col,round_n=2):
    cal_cnt = {cnt:[pd.Series.nunique] for cnt in cnt_col}
    cal_rt = {rt:[np.mean] for rt in rate_col}
    cal_all = {**cal_cnt,**cal_rt}
    df_out = df.groupby(g_col).agg(cal_all).round(round_n)
    return df_out

def helper_rename(df,dedup_col):
    df.columns = ["_".join(x) for x in df.columns.ravel()]
    df.reset_index(inplace=True)
    #ensure no duplicates in the index
    df.drop_duplicates(subset=dedup_col,inplace=True)
    return df

def pd_read(file_name,sample=None,used_cols=None):
    csvFile = os.path.join(csvfolderpath, file_name)
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile, nrows=sample,usecols=used_cols)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,engine='pyarrow',columns=used_cols)
        if sample:
            table = table.head(sample)
    return table



@app.route('/Login')
def Login():
    return render_template('login.html')

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
    used_cols= post_values_with_fallback("used_cols")
    target_cols= post_values_with_fallback("target_cols")
    relations,cols = rel_col(file_name,used_cols,target_cols)

    response = make_response(render_template("selection.html",
      files=files,
      file_name=file_name,
      used_cols=used_cols,
      target_cols=target_cols,
      cols=sorted(cols)))
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("file_name", file_name, expires=expires)
    #response.set_cookie("used_cols", used_cols, expires=expires)
    #response.set_cookie("target_cols", target_cols, expires=expires)
    return response
    #return render_template('selection.html', files= files)

def post_value_with_fallback(key):
    if request.form.get(key):
        return request.form.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return DEFAULT_SELECT

def post_values_with_fallback(key):
    if request.form.getlist(key):
        return request.form.getlist(key)
    if request.cookies.getlist(key):
        return request.cookies.getlist(key)
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




def rel_col(file,col1,col2):
    if file==DEFAULT_SELECT:
        return None,[None]
    csvFile = os.path.join(csvfolderpath, file)
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile, nrows=20)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,  engine='pyarrow')
        table = table.head(20)
    cols = table.columns.tolist()
    return None,cols
'''
def rel_col(cols):
    if file=='None':
        cols = ['None']
    else:
        csvFile = os.path.join(csvfolderpath, file)
        if '.csv' in csvFile:
            table = pd.read_csv(csvFile, nrows=20)
        if '.parquet' in csvFile:
            table = pd.read_parquet(csvFile,  engine='pyarrow')
            table = table.head(20)
        cols = table.columns.tolist()
    return cols
'''
'''
@app.route('/selection/<string:name>')
def selection(name):
    csvFile = os.path.join(csvfolderpath, name)
    #files = os.listdir(csvfolderpath)
    if '.csv' in csvFile:
        table = pd.read_csv(csvFile, nrows=20)
    if '.parquet' in csvFile:
        table = pd.read_parquet(csvFile,  engine='pyarrow')
        table = table.head(20)
    cols = table.columns.tolist()
    return render_template('selection.html', fileName= name, cols=cols)
'''

if __name__ == '__main__':
    app.run(port=5000, debug=True)#÷≥headline
