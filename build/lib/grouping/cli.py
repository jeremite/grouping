import os
import pkg_resources

def main():
    os.chdir(os.path.join(pkg_resources.get_distribution("grouping").location,"grouping"))
    os.system('docker-compose up --build')

#if __name__=='__main__':
#    main()
