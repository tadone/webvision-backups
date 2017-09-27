#!/usr/bin/env bash                                                                                                                         
# Backup script for magento servers
# 2017-07-16 by Tad Swider

# Set the date format, filename and the directories where your backup files
# will be placed and which directory will be archived.
NOW=$(date +"%Y-%m-%d_%H%M")
SITENAME="magento1-52-73-17-216"
FILE="$SITENAME-$NOW.tar"
BACKUP_DIR="$HOME/backups"
WWW_DIR="$HOME/apps/magento/htdocs"
LOG_FILE="$HOME/backups/backup.log"
S3_BUCKET='s3://webvision-backups'

# MySQL database credentials
DB_USER="bn_magento"
DB_PASS="05c4ea2227"
DB_NAME="bitnami_magento"
DB_FILE="$DB_NAME-$NOW.sql"

timestamp() {
        date +"%Y/%m/%d %H:%M"
}

to_log() {
        printf "$(timestamp) - $1\n" >> "$LOG_FILE" 2>&1
}

run_it() {
        printf "$(timestamp) - " >> "${LOG_FILE}"
        $1 >> "${LOG_FILE}" 2>&1
}


# Test for backup directory
if [[ ! -d  "${BACKUP_DIR}" ]]; then
        mkdir "${BACKUP_DIR}"
        to_log "Creating backup directory"
fi

# Create the archive and the MySQL dump
printf "\n" >> "${LOG_FILE}"
to_log "######## STARTING BACKUP ########"

to_log "Backing up $(basename ${WWW_DIR}) to ${BACKUP_DIR}"
run_it "tar --exclude=var/cache --exclude=var/session -cf ${BACKUP_DIR}/${FILE} -C $(dirname ${WWW_DIR}) $(basename ${WWW_DIR})" #Site files

to_log "Backing up MySQL database: $DB_NAME"
mysqldump --user="${DB_USER}" --password="${DB_PASS}" --add-drop-table "${DB_NAME}" > /tmp/"${DB_FILE}" 2>> "${LOG_FILE}"
#mysqldump -u$DB_USER -p$DB_PASS -$DB_NAME > $BACKUP_DIR/$DB_FILE

# Append the dump to the archive, remove the dump and compress the whole archive.
to_log "Creating archive"
run_it "tar --append --file=${BACKUP_DIR}/${FILE} -C /tmp/ ${DB_FILE}"

to_log "Removing temprorary database dump file"
run_it "rm -v /tmp/${DB_FILE}"

to_log "Zipping up the archive"
run_it "gzip -9 ${BACKUP_DIR}/${FILE}"

# Upload to S3 Bucket
if [ -x "$(command -v aws)" ]; then
        to_log "Uploading ${FILE}.gz to Amazon S3 "
        run_it "aws s3 cp ${BACKUP_DIR}/${FILE}.gz ${S3_BUCKET}"
        to_log "Removing local backup file"
        run_it "rm -v ${BACKUP_DIR}/${FILE}.gz"
else
        to_log "AWS CLI is not installed. Backup file not uploaded to S3!"
fi

# Finish
to_log "######## BACKUP COMPLETE ########"
