#!/usr/bin/env python
'''Backup Script'''

import os
import sys
import zipfile
import logging
import subprocess
import datetime
import getopt

# Global Variables
WEB_DIR = '/home/bitnami/apps/magento/htdocs'
EXCLUDE_DIRS = ['session', 'cache'] # Directories to exclude
S3_BUCKET = 's3://webvision-backups'

# Function Definitions
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

def usage():
    '''Print Usage'''
    print('backup.py --site-name=magento1 --credentials-file=credentials.txt')
    print('backup.py -s magento1 -c credentials.txt')

def my_opts():
    '''Get command line options'''
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:c:", ["help", "site-name=", "credentials-file="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    cmd_opts = dict()
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-s", "--site-name"):
            cmd_opts['site'] = arg
        elif opt in ("-c", "--credentials-file"):
            cmd_opts['creds'] = arg
    return cmd_opts

def zipdir(path, ziph, exclude):
    '''Zip up the directory excluding some subdirs'''
    logging.info('Create zip archive from %s excluding %s', path, exclude)
    # ziph is zipfile handle
    for dirname, subdirs, files in os.walk(path):
        subdirs[:] = [d for d in subdirs if d not in exclude]
        for file in files:
            ziph.write(os.path.join(dirname, file))

def database_bkp(dbuser, dbpass, dbname, dbfile):
    '''Backup Database'''
    logging.info('MySQLDump DB: %s', dbname)
    logging.info('Credentials info: DB: %s, User: %s, Password: %s', dbname, dbuser, dbpass)
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
    logging.info('Uploading %s to AWS S3', s3file)
    try:
        with open('backup.log', 'a') as f:
            subprocess.call(['aws', 's3', 'cp', s3file, s3bucket], stdout=f, stderr=f)
    except Exception as err:
        logging.error('AWS CLI encounter critical error: ' + str(err) + '\nExiting...')
        sys.exit('AWS CLI encounter critical error! Exiting...')

def cleanup(*args):
    '''Remove local file'''
    try:
        for arg in args:
            logging.info('Removing local file: %s', arg)
            os.remove(arg)
    except FileNotFoundError as err:
        logging.error('The %s file was not found. Exiting...', args)
        sys.exit(err)

def main():
    '''Main script'''
    opts = my_opts()
    credentials_file = opts['creds']
    site_name = opts['site']
    backup_log = site_name + '.backup.log'
    logging.basicConfig(filename=backup_log, format='%(levelname)s:%(message)s', level=logging.INFO)
    logging.info('\n### Backup started: ' + datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p") \
    + ' ###')

    db_file = site_name +'.sql'
    zip_file = site_name + '_' + datetime.datetime.now().strftime("%Y%m%d_%H%M") + '.zip'
    read_creds(credentials_file)

    # Backup Database
    database_bkp(DB_USER, DB_PASS, DB_NAME, db_file)

    # Archive web directory
    zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
    zipdir(WEB_DIR, zipf, EXCLUDE_DIRS)
    logging.info('Appending %s database to zip file', db_file)
    zipf.write(db_file)
    zipf.close()
    total_size = int(os.path.getsize(zip_file)) / 1000000
    s3_upload(zip_file, S3_BUCKET) # Upload zip file to S3
    s3_upload(backup_log, S3_BUCKET) # Upload log to S3
    cleanup(zip_file, db_file) # Remove local files
    logging.info('Total file size: %s MB', total_size)
    logging.info('Success ' + datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p"))

if __name__ == '__main__':
    main()
