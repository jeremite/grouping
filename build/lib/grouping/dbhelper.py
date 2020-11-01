import pymongo
from bson.objectid import ObjectId
import numpy as np
import pandas as pd
import sys
import os
DATABASE = "grouping"

class DBHelper:

    def __init__(self):
        if "DB_PORT_27017_TCP_ADDR" in os.environ:
            HOSTIP = os.environ["DB_PORT_27017_TCP_ADDR"]
        else:
            HOSTIP = "localhost"
        client = pymongo.MongoClient(HOSTIP, 27017)
        #client = pymongo.MongoClient(os.environ["DB_PORT_27017_TCP_ADDR"], 27017)
        self.db = client[DATABASE]

    def add_file_name(self,file_name):
        return self.db.files.insert_one({'file':file_name})

    def get_file_name(self):
        return list(self.db.files.find().sort('_id',-1))[0]['file']


    def add_params(self,ft,gr_ft,cnt_ft,avg_ft):
        return self.db.params.insert_one({'ft':ft,'gr_ft':gr_ft,'cnt_ft':cnt_ft,'avg_ft':avg_ft})

    def get_params(self):
        return list(self.db.params.find().sort('_id',-1))[0]

    def add_updates(self,id_val,gr_val):
        return self.db.updates.insert_one({'id_val':id_val,'gr_val':gr_val})

    def get_updates(self):
        return list(self.db.updates.find())

    def add_table(self,file_name,df):
        #if file_name in self.db.list_collection_names():
        #    print('has already')
        #    return
        if file_name in self.db.list_collection_names():
            self.drop_table(file_name)
        db_table = self.db[file_name]
        #db_table_res = self.db[file_name+"_res"]
        params = self.get_params()
        # get the data with smaller size then save into DB to decrease further I/O time
        df = self.helper_agg(df,list([params['ft']]+[params['gr_ft']]),params['cnt_ft'],params['avg_ft'])
        #df_res = self.helper_agg(df,params['gr_ft'],params['cnt_ft']+['cnt'],params['avg_ft'],True)
        #print('df before insert',df)

        db_table.insert_many(df.to_dict('records'))

        # do a backup in order to reset
        if not file_name+'_record_ori' in self.db.list_collection_names():
            db_ori = self.db[file_name+'_record_ori']
            #db_cal = self.db[file_name+'_record_cal']
            #db_col = self.db[file_name+'_cols']
            db_ori.insert_many(df.to_dict('records'))
            #db_cal.insert_many(df_cal.to_dict('records'))
            #db_col.insert_one({'all_used_cols':all_used_cols,'res_used_cols':res_used_cols})
        #db_table_res.insert_many(df_res.to_dict('records'))

    def update_table(self,file_name,ft_val,gr_ft_val):
        db_table = self.db[file_name]
        #db_res = self.db[file_name+"_res"]
        params = self.get_params()

        '''
        #extract old values
        myquery = {params["ft"]:ft_val}
        find_doc = list(db_table.find(myquery))[0]
        ori_grp, ori_cnt_val, ori_avg_val = find_doc[params['gr_ft']],\
                                                [find_doc[f] for f in params['cnt_ft']],\
                                                [find_doc[f] for f in params['avg_ft']]
        '''
        #update new values
        db_table.update_one({params["ft"]: ft_val}, {"$set": {params["gr_ft"]:gr_ft_val}})

    def helper_cal(self,df,cnt_ft,avg_ft,round_n=2):
        #df[cnt_ft]=df[cnt].apply(lambda x:x/df['cnt'])
        for f in cnt_ft:
            df[f+'_count']=df[f].apply(len)
            df.drop(columns=f,inplace=True)
        for ft in avg_ft:
            df[ft+'_rate']=(df[ft]/df['cnt']).round(round_n)
            df.drop(columns=ft,inplace=True)

        df.drop(columns='cnt',inplace=True)
        return df
    def get_table_one(self,file_name):
        return list(self.db[file_name].find_one())
    def get_table(self,file_name,update=False):
        params = self.get_params()
        #'ft':ft,'gr_ft':gr_ft,'cnt_ft':cnt_ft,'avg_ft':avg_ft = params
        db_table = self.db[file_name]
        df = pd.DataFrame(db_table.find())
        df.drop(columns='_id',inplace=True)
        #print(df.head())
        # get resulats table
        df_res = self.helper_agg(df.copy(),params['gr_ft'],params['cnt_ft'],params['avg_ft']+['cnt'],True)

        #get two tables
        df_cal = self.helper_cal(df_res.copy(),params['cnt_ft'],params['avg_ft'])
        res_used_cols = df_cal.columns.tolist()

        if not update:
            df_ori = self.helper_cal(df.copy(),params['cnt_ft'],params['avg_ft'])
            all_used_cols = df_ori.columns.tolist()
            return df_ori,df_cal,all_used_cols,res_used_cols

        return df_cal,res_used_cols
        # get columns for table_out used in ajax data


    def get_defalt(self,file_name):
        # drop current updated collection
        if file_name+'_record_ori' in self.db.list_collection_names():
            self.drop_table(file_name)
            # get the presaved default table
            db_ori = self.db[file_name+'_record_ori']
            df_ori = pd.DataFrame(db_ori.find())
            # write into the file_name collection
            db_table = self.db[file_name]
            db_table.insert_many(df_ori.to_dict('records'))
        else:
            return


    def drop_table(self,file_name):
        if file_name in self.db.list_collection_names():
            self.db[file_name].drop()

    def helper_agg(self,df,g_col,cnt_col,rate_col,if_res=False):#,round_n=2):
        def m(col):
            return list(set(sum(col,[])))
        if if_res: #for the result table
            cal_cnt = {cnt:lambda x:m(x) for cnt in cnt_col}
        else: #for the original table
            cal_cnt = {cnt:lambda x:list(set(x)) for cnt in cnt_col}

        cal_rt = {rt:np.sum for rt in rate_col}
        cal_all = {**cal_cnt,**cal_rt}
        df_out = df.groupby(g_col).agg(cal_all)#.round(round_n)
        if not if_res:
            all_cnts = df.groupby(g_col).size()
            all_cnts.name = 'cnt'
            df_out = df_out.join(all_cnts)
        df_out=df_out.reset_index()
        df_out.drop_duplicates(subset=g_col,inplace=True)
        return df_out

    def helper_rename(self,df,dedup_col):
        df.columns = ["_".join(x) for x in df.columns.ravel()]
        df.reset_index(inplace=True)
        #ensure no duplicates in the index
        df.drop_duplicates(subset=dedup_col,inplace=True)
        return df
