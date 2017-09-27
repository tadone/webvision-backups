#!/usr/bin/env bash
# Backup script for magento servers
# 2017-09-27 by Tad Swider
# v2

#set -e # Exit if a command fails

# Set the date format, filename and the directories where your backup files
# will be placed and which directory will be archived.
NOW=$(date +'%Y-%m-%d')
SITENAME="magento1-52-73-17-216"
FILE="$SITENAME-$NOW.tar"
BACKUP_DIR="/home/bitnami/backups"
WWW_DIR="/home/bitnami/apps/magento/htdocs"
LOG_FILE="/home/bitnami/backups/backup.log"
S3_BUCKET='s3://webvision-backups'

echo "Starting..." >> "$LOG_FILE"
# MySQL database credentials
DB_USER="CHANGE_ME"
DB_PASS="CHANGE_ME"
DB_NAME="CHANGE_ME"
DB_FILE="$DB_NAME-$NOW.sql"

timestamp() {
        date +'%Y/%m/%d %I:%M %p'
}

log_message () {
        echo -e "$1" >> "$LOG_FILE" 2>&1
}

execute() {
    eval "$1" 2>> ${LOG_FILE}
    #print_result $? "${2:-$1}"
    if [ "$?" -eq 0 ]; then
      log_message "OK: ${2:-$1}"
      return 0
    else
      log_message "ERROR: $2 Failed! Exiting..."
      exit 1
    fi
}

# Check if tools exist
if [ ! -x "$(command -v aws)" ]; then
   log_message "ERROR - AWS CLI not installed. Exiting..."
   exit 1
fi

if [ ! -x "$(command -v /opt/bitnami/mysql/bin/mysqldump)" ]; then
   log_message "ERROR - MySQLDump not found. Exiting..."
   exit 1
fi
# Test for backup directory
if [[ ! -d  "${BACKUP_DIR}" ]]; then
        execute "mkdir ${BACKUP_DIR}" "Create ${BACKUP_DIR}"
fi

log_message ""
log_message "BACKUP STARTED: $(timestamp)"
execute "tar --exclude=var/cache --exclude=var/session -cf ${BACKUP_DIR}/${FILE} -C $(dirname ${WWW_DIR}) $(basename ${WWW_DIR})" \
"Create TAR archive from ${WWW_DIR} in ${BACKUP_DIR}"
# MYSQLDUMP
execute '/opt/bitnami/mysql/bin/mysqldump --user="${DB_USER}" --password="${DB_PASS}" --add-drop-table "${DB_NAME}" > /tmp/"${DB_FILE}"' "Mysqldump to ${DB_FILE}"
log_message "OK: DB \"${DB_FILE}\" size: $(du -h /tmp/${DB_FILE} | awk '{ print $1 }')"
# Append the dump to the archive, remove the dump and compress the whole archive.
execute "tar --append --file=${BACKUP_DIR}/${FILE} -C /tmp/ ${DB_FILE}" "Append ${DB_FILE} to ${FILE}.gz"
# log_message "Removing temprorary database dump file"
execute "rm /tmp/${DB_FILE}" "Remove /tmp/${DB_FILE}"
# log_message "Zipping up the archive"
execute "gzip -f -9 ${BACKUP_DIR}/${FILE}" "Gunzip to ${FILE}.gz"
GZ_TOTAL_FILESIZE=$(du -h ${BACKUP_DIR}/"${FILE}".gz | awk '{ print $1 }')
# execute "aws s3 cp ${BACKUP_DIR}/${FILE}.gz ${S3_BUCKET}" "Upload ${FILE}.gz to ${S3_BUCKET}"
execute "aws s3 cp ${LOG_FILE} ${S3_BUCKET}" "Upload ${LOG_FILE} to ${S3_BUCKET}"
execute "rm ${BACKUP_DIR}/${FILE}.gz" "Remove local ${BACKUP_DIR}/${FILE}.gz"
# Finish
log_message "SUCCESS: $(timestamp), FILE: ${FILE}.gz, SIZE: $GZ_TOTAL_FILESIZE"
