import pymongo
from bson.objectid import ObjectId
DATABASE = "grouping"

class DBHelper:

    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client[DATABASE]

    def add_params(self,ft,gr_ft,cnt_ft,avg_ft):
        return self.db.params.insert_one({'ft':ft,'gr_ft':gr_ft,'cnt_ft':cnt_ft,'avg_ft':avg_ft})

    def get_params(self):
        return list(self.db.params.find().sort('_id',-1))[0]

    def add_table(self,file_name,df):
        if file_name in self.db.list_collection_names():
            print('has already')
            return
        db_table = self.db[file_name]
        #db_table_res = self.db[file_name+"_res"]
        params = self.get_params()

        # get the data with smaller size then save into DB to decrease further I/O time
        df = self.helper_agg(df,list([params['ft']]+[params['gr_ft']]),params['cnt_ft'],params['avg_ft'])
        #df_res = self.helper_agg(df,params['gr_ft'],params['cnt_ft']+['cnt'],params['avg_ft'],True)
        print('get table')
        db_table.insert_many(df.to_dict('records'))
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
    def get_table(self,file_name):
        params = self.get_params()
        #'ft':ft,'gr_ft':gr_ft,'cnt_ft':cnt_ft,'avg_ft':avg_ft = params
        db_table = self.db[file_name]
        df = pd.DataFrame(db_table.find())
        df.drop(columns='_id',inplace=True)

        # get resulats table
        df_res = self.helper_agg(df.copy(),params['gr_ft'],params['cnt_ft'],params['avg_ft']+['cnt'],True)

        #get two tables
        df_ori = self.helper_cal(df,params['cnt_ft'],params['avg_ft'])
        df_cal = self.helper_cal(df_res,params['cnt_ft'],params['avg_ft'])

        # get columns for table_out used in ajax data
        all_used_cols = df_ori.columns.tolist()
        return df_ori,df_cal,all_used_cols

    def drop_table(self,file_name):
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