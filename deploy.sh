#!/bin/bash

ENV_FILE=".env" # default env
SERVERLESS_FILE="serverless.yml"
BACKUP_ENV="UNKNOW_ENV"  # must be specified
BACKUP_FILE="serverless.$BACKUP_ENV.yml"
REGION=$(aws configure get region)

# parse cmd options
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -e|--env) ENV_FILE="$ENV_FILE.$2"; BACKUP_ENV="$2"; BACKUP_FILE="serverless.$BACKUP_ENV.yml"; shift ;;  # rename .env & backup yml
        -r|--region) REGION="$2"; shift ;;  # specify region
        *) echo "Unknow options: $1"; exit 1 ;;
    esac
    shift
done

if [ ! -f "$ENV_FILE" ]; then
    echo "$ENV_FILE isn't exist"
    exit 1
fi

cp $SERVERLESS_FILE $BACKUP_FILE

# replace ${env:STAGE} and ${env:THE_REGION}
sed -i.bak "s|\${env:STAGE}|$BACKUP_ENV|g" "$BACKUP_FILE"  # replace env
sed -i.bak "s|\${env:THE_REGION}|$REGION|g" "$BACKUP_FILE"  # replace region

# read .env file and replace variables in serverless.yml
while IFS='=' read -r key value; do
    # skip space and annotations
    if [[ ! -z "$key" && ! "$key" =~ ^# ]]; then
        # replace variables in serverless.yml
        sed -i.bak "s|\${env:$key}|$value|g" "$BACKUP_FILE"
    fi
done < "$ENV_FILE"

rm "$BACKUP_FILE.bak"
echo "The replacement of backup file: $BACKUP_FILE is done"


# deploy
sls print --config $BACKUP_FILE --region $REGION --stage $BACKUP_ENV  # show & check backup yml
sls deploy --config $BACKUP_FILE --region $REGION --stage $BACKUP_ENV  # apply region & env
rm "$BACKUP_FILE"
