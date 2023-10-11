import os
import json
import random
import time
from datetime import date, datetime
from typing import List
from snowflake import SnowflakeGenerator
import hashlib
from ...configs.exceptions import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


# TODO: asymmetric encrypt/decrypt
def get_public_key(ts):
    return 'abcdefghijkl'



'''SnowflakeGenerator group
'''
instances = 100
snowflake_generator_dict = {}
for i in range(instances):
    snowflake_generator_dict[i] = SnowflakeGenerator(i)


def gen_snowflake_id():
    millisecs = datetime.now().timestamp()
    i = int(millisecs * 100000) % instances
    gen = snowflake_generator_dict[i]
    num = next(gen)
    return int(num / 1000)


letters = '0123456789abcdefghijklmnopqrstuvwxyz'


def gen_random_string(length):
    # choose from all lowercase letter
    return ''.join(random.choice(letters) for i in range(length))


def shift_decimal(number, places):
    return number * (10 ** places)

def gen_pass_salt():
    return gen_random_string(12)

def gen_password_hash(pw: str, pass_salt: str):
    password_data = str(pw + pass_salt).encode('utf-8')
    return hashlib.sha224(password_data).hexdigest()


def gen_account_data(data: dict, account_type: str):
    aid = gen_snowflake_id()
    role_id = gen_snowflake_id()
    pass_salt = gen_pass_salt()
    pass_hash = gen_password_hash(pw=data['pass'], pass_salt=pass_salt)
    created_at = int(shift_decimal(time.time(), 3))

    return {
        # auth
        'email': data['email'],
        'aid': aid,
        'pass_hash': pass_hash,
        'pass_salt': pass_salt,

        # account
        # 'aid': ..
        'type': account_type,
        'region': data['region'],
        # 'email': ..
        'email2': None,
        'is_active': True,
        'role': data['role'],
        'role_id': role_id,
        'created_at': created_at,
    }


def match_password(pass_hash: str, pw: str, pass_salt: str):
    return pass_hash == gen_password_hash(pw=pw, pass_salt=pass_salt)


def filter_by_keys(data, ary):
    result = {}
    for field in ary:
        result[field] = data[field]

    return result
