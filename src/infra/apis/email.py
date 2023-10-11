import os
import json
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class Email:
    def __init__(self):
        pass

    async def send_conform_code(self, email: str, confirm_code: str) -> None:
        log.debug(f'send email: {email}, code: {confirm_code}')
        pass
