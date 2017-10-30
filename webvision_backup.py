#!/usr/bin/env python
'''Backup Script'''

import os
import sys
import zipfile
import logging
import subprocess
import datetime

WEB_DIR = '/home/bitnami/apps/magento/htdocs'
EXCLUDE_DIRS = ['session', 'cache'] # Directories to exclude
SITE_NAME = 'magento1-52-73-17-216'
DB_FILE = SITE_NAME +'.sql'
ZIP_FILE = SITE_NAME + '_' + datetime.datetime.now().strftime("%y%m%d_%H%M") + '.zip'
CREDENTIALS_FILE = '/home/bitnami/credentials.txt'
logging.basicConfig(filename='backup.log', format='%(levelname)s:%(message)s', level=logging.INFO)

def read_creds(cred_file):
    '''Read credentials'''
    try:
        with open(cred_file, 'r') as f:
            credentials = [x.strip().split(':') for x in f.readlines()]
        for value1, value2 in credentials:
            if value1 == 'DB_USER':
                global DB_USER
                DB_USER = value2
            elif value1 == 'DB_PASS':
                global DB_PASS
                DB_PASS = value2
            elif value1 == 'DB_NAME':
                global DB_NAME
                DB_NAME = value2
            else:
                logging.error('Coorrect values not supplied!')
                sys.exit('Correct values not supplied! Exiting...')
    except FileNotFoundError:
        logging.error('File %s not found!', cred_file)

def zipdir(path, ziph, exclude):
    '''Zip up the directory excluding some subdirs'''
    # ziph is zipfile handle
    for dirname, subdirs, files in os.walk(path):
        subdirs[:] = [d for d in subdirs if d not in exclude]
        for file in files:
            ziph.write(os.path.join(dirname, file))

def database_bkp(dbuser, dbpass, dbname, dbfile):
    '''Backup Database'''
    logging.warning('MySQLDump DB: %s', dbname)
    try:
        with open(dbfile, 'wb', 0) as f, open('backup.log', 'a') as e:
            subprocess.call(['mysqldump', '-u', dbuser, '-p' + dbpass, '--add-drop-database', \
            '--databases', dbname], stdout=f, stderr=e)
    except Exception as err:
        logging.error('MySQLDump encounter critical error: ' + str(err))
        sys.exit('MySQLDump encounter critical error! Exiting...')
        # raise

def main():
    '''Main script'''
    logging.info('Backup started: ' + datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p"))
    # Read Credentials
    read_creds(CREDENTIALS_FILE)

    logging.info('MySQLDump to %s', DB_NAME)
    logging.info('Credentials info: DB: %s, User: %s, Password: %s', DB_NAME, DB_USER, DB_PASS)
    # Backup Database
    database_bkp(DB_USER, DB_PASS, DB_NAME, DB_FILE)

    logging.info('Create zip archive from %s and %s', WEB_DIR, DB_FILE)
    # Archive web directory
    zipf = zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED)
    zipdir(WEB_DIR, zipf, EXCLUDE_DIRS)
    zipf.write(DB_FILE)
    zipf.close()

    logging.info('Success ' + datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p"))

if __name__ == '__main__':
    main()
