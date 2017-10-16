#!/usr/bin/env python

import os, sys, zipfile, logging, subprocess

# BACKUP_WEB = '/home/tswider/Projects/webvision-backups'
# BACKUP_TO = '/home/tswider/Projects/webvision-backups'
# DB_USER = ''
# DB_PASS = ''
# DB_NAME = ''
DB_FILE = input('Enter db backup file name: ')

def read_creds(cred_file):
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
        logging.error('File ' + cred_file + ' not found!')

def zipdir(path, ziph):
    # ziph is zipfile handle
    for path, dirs, files in os.walk(path):
        if 'cache' in dirs:
            dirs.remove('cache')
        elif 'session' in dirs:
            dirs.remove('session')
        ziph.write(dirname)
        for file in files:
            ziph.write(os.path.join(path, file))

def test_path(path):
    for path, dirs, files in os.walk(path):
        if ''

def database_bkp(dbuser, dbpass, dbname, dbfile):
    logging.warning('MySQLDump DB: ' + dbname)
    try:
        with open(dbfile, 'wb', 0) as f, open('backup.log', 'a') as e:
            subprocess.call(['mysqldump', '-u', dbuser, '-p' + dbpass, '--add-drop-database', '--databases', dbname], stdout=f, stderr=e)
    except Exception as err:
        logging.error('MySQLDump encounter critical error: ' + str(err))
        sys.exit('MySQLDump encounter critical error! Exiting...')
        # raise
def main():
    logging.basicConfig(filename='backup.log', format='%(levelname)s:%(message)s', level=logging.INFO)
    logging.info('Started')
    # zipf = zipfile.ZipFile('Python.zip', 'w', zipfile.ZIP_DEFLATED)
    # zipdir('/home/tswider/Projects/webvision-backups', zipf)
    # zipf.close()
    read_creds("credentials.txt")
    logging.warning('credentials info: DB:' + DB_NAME + ', User: ' + DB_USER +  ', Password: ' + DB_PASS)
    database_bkp(DB_USER, DB_PASS, DB_NAME, DB_FILE)
    logging.info('Finished')

if __name__ == '__main__':
    main()
