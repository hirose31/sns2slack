#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vi: set ft=python fenc=utf-8 ff=unix :

from base64 import b64decode
import json
import logging
import os
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import (
    Request,
    urlopen,
)

import boto3

HOOK_URL = os.getenv('HOOK_URL', None)
if not HOOK_URL:
    # The base-64 encoded, encrypted key (CiphertextBlob) stored in the kmsEncryptedHookUrl environment variable
    ENCRYPTED_HOOK_URL = os.environ['KMS_ENCRYPTED_HOOK_URL']
    HOOK_URL = boto3.client('kms').decrypt(
        CiphertextBlob=b64decode(ENCRYPTED_HOOK_URL),
        EncryptionContext={
            'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME'],
        }
    )['Plaintext'].decode('utf-8')

if not HOOK_URL.startswith('http'):
    HOOK_URL = 'https://' + HOOK_URL

# The Slack channel to send a message to stored in the slackChannel environment variable
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def processCloudWatch(message):
    alarm_name = message['AlarmName']
    #old_state = message['OldStateValue']
    new_state = message['NewStateValue']
    reason = message['NewStateReason']

    slack_message = {
        'text': f"[*CloudWatch*] {alarm_name} state is now {new_state}: {reason}",
    }

    return slack_message


# https://docs.aws.amazon.com/ja_jp/ses/latest/DeveloperGuide/notification-contents.html
def processSES(message):

    mail_from = ', '.join(message['mail']['commonHeaders']['from'])
    mail_to = ', '.join(message['mail']['commonHeaders']['to'])
    mail_subject = message['mail']['commonHeaders']['subject']
    detail = ''
    if 'bounce' in message:
        detail = '\n'.join([
            f"Bounce Type: {message['bounce']['bounceType']}",
            f"Bounce Sub Type: {message['bounce']['bounceSubType']}",
            'Bounce Recipients: ' + '\n  '.join(
                [f"{b['emailAddress']} (status: {b['status']} action: {b['action']})"
                 for b in message['bounce']['bouncedRecipients']]),
        ])
    elif 'complaint' in message:
        detail = '\n'.join([
            f"Complaint Feedback Type: {message['complaint']['complaintFeedbackType']}",
            'Complained Recipients: ' + '\n  '.join(
                [f"{b['emailAddress']}"
                 for b in message['complaint']['complaintRecipients']]),
        ])

    slack_message = {
        'text': f"[*SES*] {message['notificationType']}\nFrom: {mail_from}\nTo: {mail_to}\nSubject: {mail_subject}\n{detail}",
    }

    return slack_message


def lambda_handler(event, context):
    logger.info("Event: " + str(event))
    message = json.loads(event['Records'][0]['Sns']['Message'])
    logger.info("Message: " + str(message))

    # https://api.slack.com/reference/messaging/payload
    if 'AlarmName' in message:
        slack_message = processCloudWatch(message)
    elif 'mail' in message:
        slack_message = processSES(message)
    else:
        slack_message = {
            'text': f'unknown event: {json.dumps(message)}',
        }

    slack_message['channel'] = SLACK_CHANNEL

    req = Request(HOOK_URL, json.dumps(slack_message).encode('utf-8'))
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slack_message['channel'])
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)


# Local Variables:
# mode: python
# eval: (autopep8-mode)
# End:
