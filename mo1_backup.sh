#!/usr/bin/env bash
# Backup script for magento servers
# 2017-09-27 by Tad Swider

set -e # Exit if a command fails

# Check if tools exist
if [ ! -x "$(command -v aws)" ]; then
   log_message "ERROR - AWS CLI not installed. Exiting..."
   exit 1
fi

if [ ! -x "$(command -v aws)" ]; then
   log_message "ERROR - MySQLDump not found. Exiting..."
   exit 1
fi

# Set the date format, filename and the directories where your backup files
# will be placed and which directory will be archived.
NOW=$(date +"%Y-%m-%d")
SITENAME="magento1-52-73-17-216"
FILE="$SITENAME-$NOW.tar"
BACKUP_DIR="/home/bitnami/backups"
WWW_DIR="/home/bitnami/apps/magento/htdocs"
LOG_FILE="/home/bitnami/backups/backup.log"
S3_BUCKET='s3://webvision-backups'

# MySQL database credentials


timestamp() {
        date +"%Y/%m/%d %H:%M"
}

log_message () {
        echo -e "$1\n" >> "$LOG_FILE" 2>&1
}

execute() {
        $1 >> "${LOG_FILE}" 2>&1
}


# Test for backup directory
if [[ ! -d  "${BACKUP_DIR}" ]]; then
        mkdir "${BACKUP_DIR}"
        log_message "Creating backup directory"
fi

# Create the archive and the MySQL dump
log_message ""
log_message "######## BACKUP START: $(timestamp) ########"

log_message "- Backing up $(basename ${WWW_DIR}) to ${BACKUP_DIR}"
execute "tar --exclude=var/cache --exclude=var/session -cf ${BACKUP_DIR}/${FILE} -C $(dirname ${WWW_DIR}) $(basename ${WWW_DIR})" #Site files

log_message "Backing up MySQL database: $DB_NAME"
mysqldump --user="${DB_USER}" --password="${DB_PASS}" --add-drop-table "${DB_NAME}" > /tmp/"${DB_FILE}" 2>> "${LOG_FILE}"
#mysqldump -u$DB_USER -p$DB_PASS -$DB_NAME > $BACKUP_DIR/$DB_FILE

# Append the dump to the archive, remove the dump and compress the whole archive.
log_message "Creating archive"
execute "tar --append --file=${BACKUP_DIR}/${FILE} -C /tmp/ ${DB_FILE}"

log_message "Removing temprorary database dump file"
execute "rm -v /tmp/${DB_FILE}"

log_message "Zipping up the archive"
execute "gzip -9 ${BACKUP_DIR}/${FILE}"

# Upload to S3 Bucket
if [ -x "$(command -v aws)" ]; then
        log_message "Uploading ${FILE}.gz to Amazon S3 "
        execute "aws s3 cp ${BACKUP_DIR}/${FILE}.gz ${S3_BUCKET}"
        log_message "Removing local backup file"
        execute "rm -v ${BACKUP_DIR}/${FILE}.gz"
else
        log_message "AWS CLI is not installed. Backup file not uploaded to S3!"
fi

# Finish
log_message "######## BACKUP COMPLETE ########"
