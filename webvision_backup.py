#!/usr/bin/env python
'''Backup Script'''

import os
import sys
import zipfile
import logging
import subprocess
import datetime
import getopt

# Variable definitions

# SITE_NAME = 'magento1-52-73-17-216'

# CREDENTIALS_FILE = '/home/bitnami/credentials.txt'




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
            elif value1 == 'SITE_NAME':
                global SITE_NAME
                SITE_NAME = value2
            else:
                logging.error('Coorrect values not supplied!')
                sys.exit('Correct values not supplied! Exiting...')
    except FileNotFoundError:
        logging.error('File %s not found!', cred_file)

def zipdir(path, ziph, exclude):
    '''Zip up the directory excluding some subdirs'''
    logging.info('Create zip archive from %s and %s', WEB_DIR, DB_FILE)
    # ziph is zipfile handle
    for dirname, subdirs, files in os.walk(path):
        subdirs[:] = [d for d in subdirs if d not in exclude]
        for file in files:
            ziph.write(os.path.join(dirname, file))

def database_bkp(dbuser, dbpass, dbname, dbfile):
    '''Backup Database'''
    logging.info('MySQLDump DB: %s', dbname)
    logging.info('Credentials info: DB: %s, User: %s, Password: %s', DB_NAME, DB_USER, DB_PASS)
    try:
        with open(dbfile, 'wb', 0) as f, open('backup.log', 'a') as e:
            subprocess.call(['mysqldump', '-u', dbuser, '-p' + dbpass, '--add-drop-database', \
            '--databases', dbname], stdout=f, stderr=e)
    except Exception as err:
        logging.error('MySQLDump encounter critical error: ' + str(err) + '\nExiting...')
        sys.exit('MySQLDump encounter critical error! Exiting...')
        # raise

def s3_upload(s3file, s3bucket):
    '''Upload to S3'''
    logging.info('Upload %s to S3', s3file)
    try:
        with open('backup.log', 'a') as f:
            subprocess.call(['aws', 's3', 'cp', s3file, s3bucket], stdout=f, stderr=f)
    except Exception as err:
        logging.error('AWS CLI encounter critical error: ' + str(err) + '\nExiting...')
        sys.exit('AWS CLI encounter critical error! Exiting...')

def rm_local(rm_file):
    '''Remove local file'''
    logging.info('Removing local backup fil %s', rm_file)
    try:
        os.remove(rm_file)
    except FileNotFoundError as fnf:
        logging.error('The %s file was not found. Exiting...', rm_file)
        sys.exit(fnf)

def usage():
    '''Print Usage'''
    print('backup.py --site-name=magento1 --credentials-file=credentials.txt')
    print('backup.py -s magento1 -c credentials.txt')

def main(argv):
    '''Main script'''
    logging.info('### Backup started: ' + datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p") \
    + ' ###')
    # Parse variables from command line
    try:
        opts, args = getopt.getopt(argv, "hs:c:", ["help", "site-name=", "credentials-file="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-s", "--site-name"):
            SITE_NAME = arg
        elif opt in ("-c", "--credentials-file"):
            CREDENTIALS_FILE = arg

    WEB_DIR = '/home/bitnami/apps/magento/htdocs'
    EXCLUDE_DIRS = ['session', 'cache'] # Directories to exclude
    DB_FILE = SITE_NAME +'.sql'
    ZIP_FILE = SITE_NAME + '_' + datetime.datetime.now().strftime("%y%m%d_%H%M") + '.zip'
    S3_BUCKET = 's3://webvision-backups'
    logging.basicConfig(filename='backup.log', format='%(levelname)s:%(message)s', level=logging.INFO)
    # Read Credentials
    read_creds(CREDENTIALS_FILE)

    # Backup Database
    database_bkp(DB_USER, DB_PASS, DB_NAME, DB_FILE)

    # Archive web directory
    zipf = zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED)
    zipdir(WEB_DIR, zipf, EXCLUDE_DIRS)
    zipf.write(DB_FILE)
    zipf.close()

    # Upload to S3
    s3_upload(ZIP_FILE, S3_BUCKET)

    # Remove local file
    rm_local('test.file')
    logging.info('Success ' + datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p"))

if __name__ == '__main__':
    main(sys.argv[1:])
