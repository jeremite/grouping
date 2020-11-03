import os
import pkg_resources
import sys
#from config import configs
#import argparse
import click
import json

def change_config(bkt,pre):
    my_file = pkg_resources.resource_filename('grouping', 'config.json')
    with open(my_file,"r") as f:
        data = json.load(f)
    data['bucket_name']=bkt
    data['prefix']=pre if pre[-1]=='/' else pre+'/'
    with open(my_file, 'w') as outfile:
        json.dump(data, outfile)

@click.command()
@click.option('-b', '--bucket',prompt="bucket name",default='va-vdas-workspace-prod')
@click.option('-p', '--prefix',prompt="path after bucket",default='<i-number>/<project>')
def main(bucket,prefix):
    #parser = argparse.ArgumentParser(description='get s3 info.')
    #parser.add_argument('-b', '--bucket',help='input bucket name.')
    #parser.add_argument('-p', '--prefix',help='input prefix.')

    #res = vars(parser.parse_args())
    os.chdir(os.path.join(pkg_resources.get_distribution("grouping").location,"grouping"))
    #print('check:',(bucket,prefix))
    change_config(bucket,prefix)

    #os.chdir(os.path.join(pkg_resources.get_distribution("grouping").location,"grouping"))
    #os.system('docker-compose up')# --build')
    os.system('bash run_docker.sh')# --build')

if __name__=='__main__':
    main()
