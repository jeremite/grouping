import os
import pkg_resources
import sys
#from config import configs
import argparse
import json

def change_config(bkt,pre):
    with open('config.json',"r") as f:
        data = json.load(f)
    data['bucket_name']=bkt
    data['prefix']=pre if pre[-1]=='/' else pre+'/'
    with open('config.json', 'w') as outfile:
        json.dump(data, outfile)


def main():
    parser = argparse.ArgumentParser(description='get s3 info.')
    parser.add_argument('-b', '--bucket',help='input bucket name.')
    parser.add_argument('-p', '--prefix',help='input prefix.')

    res = vars(parser.parse_args())
    print('check:',(res['bucket'],res['prefix']))
    change_config(res['bucket'],res['prefix'])

    #os.chdir(os.path.join(pkg_resources.get_distribution("grouping").location,"grouping"))
    os.system('docker-compose up')# --build')

if __name__=='__main__':
    main()
