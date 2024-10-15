import os
import json
import boto3
from pydantic import EmailStr
from botocore.exceptions import ClientError
from ...configs.exceptions import *
from ...configs.conf import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class Email:
    def __init__(self):
        self.ses = boto3.client('ses', region_name=LOCAL_REGION)

    async def send_contact(self, recipient: EmailStr, subject: str, body: str) -> None:
        log.debug(f'send email: {recipient}, subject: {subject}, body: {body}')
        try:
            response = self.ses.send_email(
                Source=EMAIL_SENDER,
                Destination={
                    'ToAddresses': [recipient],
                },
                Message={
                    'Subject': {'Data': f'{subject}'},
                    'Body': {
                        'Text': {'Data': f'{body}'},
                    },
                }
            )
            log.info(f"Email sent. Message ID: {response['MessageId']}")

        except ClientError as e:
            log.error(f"SES ClientError sending email: {e}")
            raise ServerException(msg='email_send_contact_error')

        except Exception as e:
            log.error(f"Error sending email: {e}")
            raise ServerException(msg='email_send_contact_error')


    async def send_conform_code(self, email: str, confirm_code: str) -> None:
        log.debug(f'send email: {email}, code: {confirm_code}')
        try:
            html_template = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Verification Code</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            background-color: #f4f4f4;
                            color: #333;
                            line-height: 1.6;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 20px auto;
                            padding: 20px;
                            background: #fff;
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        }}
                        .verification-code {{
                            font-size: 24px;
                            color: #007bff;
                            font-weight: bold;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Your Verification Code</h2>
                        <p>You are performing an important operation. Please enter the following verification code in the form to complete the process:</p>
                        <p class="verification-code">{confirm_code}</p>
                        <p>Please note that this verification code will expire in 5 minutes.</p>
                    </div>
                </body>
                </html>
            '''
            response = self.ses.send_email(
                Source=EMAIL_SENDER,
                Destination={
                    'ToAddresses': [email],
                },
                Message={
                    'Subject': {'Data': f'ForeignTeacher - Verification Code: {confirm_code}'},
                    'Body': {
                        'Text': {'Data': f'Your Code is: {confirm_code}'},
                        'Html': {'Data': html_template},
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
            raise ServerException(msg='email_send_conform_code_error')

        except Exception as e:
            log.error(f'Error sending email: {e}')
            raise ServerException(msg='email_send_conform_code_error')


    async def send_reset_password_comfirm_email(self, email: str, token: str) -> None:
        log.debug(f'send email: {email}, code: {token}')
        log.debug(f'{FRONTEND_RESET_PASSWORD_URL}{token}')
        try:
            html_template = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Password Reset</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; color: #333; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: 20px auto; padding: 20px; background: #fff; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }}
                        .button {{ display: inline-block; padding: 10px 20px; margin-top: 20px; background-color: #007bff; color: #fff; text-decoration: none; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>Password Reset Request</h2>
                        <p>You recently requested to reset your password for your account. Click the button below to reset it.</p>
                        <a href="{FRONTEND_RESET_PASSWORD_URL}{token}" class="button">Reset Your Password</a>
                        <p>If you did not request a password reset, please ignore this email or contact support if you have questions.</p>
                        <p>Thank you!</p>
                    </div>
                </body>
                </html>
            '''
            response = self.ses.send_email(
                Source=EMAIL_SENDER,
                Destination={
                    'ToAddresses': [email],
                },
                Message={
                    'Subject': {'Data': f'ForeignTeacher - Reset Password'},
                    'Body': {
                        'Text': {'Data': f'Reset Your Password'},
                        'Html': {'Data': html_template},
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
            raise ServerException(msg='email_send_reset_password_error')

        except Exception as e:
            log.error(f'Error sending email: {e}')
            raise ServerException(msg='email_send_reset_password_error')
