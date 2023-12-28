import os
import json
import boto3
from botocore.exceptions import ClientError
from ...configs.conf import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class Email:
    def __init__(self):
        self.ses = boto3.client('ses', region_name=LOCAL_REGION)

    async def send_conform_code(self, email: str, confirm_code: str) -> None:
        log.debug(f'send email: {email}, code: {confirm_code}')
        try:
            response = self.ses.send_email(
                Source=EMAIL_SENDER,
                Destination={
                    'ToAddresses': [email],
                },
                Message={
                    'Subject': {'Data': f'ForeignTeacher: Verification Code: {confirm_code}'},
                    'Body': {
                        'Text': {'Data': f'Your code is: {confirm_code}'},
                        'Html': {'Data': f'<html> <body> <h1>Your Verification Code</h1> <p>Your code is: {confirm_code}</p> </body> </html>'},
                    },
                }
            )
            # response = self.ses.send_templated_email(
            #     Source=EMAIL_SENDER,
            #     Destination={
            #         'ToAddresses': [email],
            #     },
            #     Template=EMAIL_VERIFY_CODE_TEMPLATE,
            #     TemplateData=f'{"verification_code":"{confirm_code}"}'
            # )
            log.info(f"Email sent. Message ID: {response['MessageId']}")

        except ClientError as e:
            log.error(f"Error sending email: {e}")


    async def send_reset_password_comfirm_email(self, email: str, token: str) -> None:
        log.debug(f'send email: {email}, code: {token}')
        log.debug(f'{FRONTEND_RESET_PASSWORD_URL}{token}')
        try:
            htmp_template = f'<!DOCTYPE html> <html> <head> <title>Password Reset</title> <style> body { font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; line-height: 1.6; } .container { max-width: 600px; margin: 20px auto; padding: 20px; background: #fff; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); } .button { display: inline-block; padding: 10px 20px; margin-top: 20px; background-color: #007bff; color: #fff; text-decoration: none; border-radius: 5px; } </style> </head> <body> <div class="container"> <h2>Password Reset Request</h2> <p>You recently requested to reset your password for your account. Click the button below to reset it.</p> <a href="{FRONTEND_RESET_PASSWORD_URL}{token}" class="button">Reset Your Password</a> <p>If you did not request a password reset, please ignore this email or contact support if you have questions.</p> <p>Thank you!</p> </div> </body> </html>'
            response = self.ses.send_email(
                Source=EMAIL_SENDER,
                Destination={
                    'ToAddresses': [email],
                },
                Message={
                    'Subject': {'Data': f'ForeignTeacher: Reset Password'},
                    'Body': {
                        'Text': {'Data': f'Reset Your Password'},
                        'Html': {'Data': htmp_template},
                    },
                }
            )
            # response = self.ses.send_templated_email(
            #     Source=EMAIL_SENDER,
            #     Destination={
            #         'ToAddresses': [email],
            #     },
            #     Template=EMAIL_RESET_PASSWORD_TEMPLATE,
            #     TemplateData=f'{"reset_password_url":"{FRONTEND_RESET_PASSWORD_URL}","token":"{token}"}'
            # )
            log.info(f"Email sent. Message ID: {response['MessageId']}")

        except ClientError as e:
            log.error(f"Error sending email: {e}") 
