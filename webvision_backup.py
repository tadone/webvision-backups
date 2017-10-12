#!/usr/bin/env python

import os, zipfile, logging
from subprocess import Popen, PIPE

BACKUP_WEB = '/home/tswider/Projects/webvision-backups'
BACKUP_TO = '/home/tswider/Projects/webvision-backups'
DB_USER = ''
DB_PASS = ''
DB_NAME = ''

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

def database_bkp():
    args = ['mysqldump', '-u', 'UNAME', '-pPASSWORD', '--add-drop-database', '--databases', 'DB']

def main():
    logging.basicConfig(filename='backup.log', format='%(levelname)s:%(message)s', level=logging.INFO)
    logging.info('Started')
    zipf = zipfile.ZipFile('Python.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir('/home/tswider/Projects/webvision-backups', zipf)
    zipf.close()
    logging.info('Finished')

if __name__ == '__main__':
    main()
