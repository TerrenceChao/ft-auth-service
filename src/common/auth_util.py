import os
import json
import random
from datetime import date, datetime
from typing import List
from snowflake import SnowflakeGenerator
import hashlib
import jwt

TOKEN_EXPIRE_TIME = int(os.getenv("TOKEN_EXPIRE_TIME", 60 * 60 * 24 * 30))

# TODO: asymmetric encrypt/decrypt
def get_public_key(ts):
    return "abcdefghijkl"


# TODO: asymmetric encrypt/decrypt
def decrypt_meta(meta, pubkey):
    return json.loads(meta)






"""SnowflakeGenerator group
"""
instances = 100
snowflake_generator_dict = {}
for i in range(1, instances):
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

def gen_account_data(data):
    aid = gen_snowflake_id()
    role_id = gen_snowflake_id()
    pass_salt = gen_random_string(12)
    password_data = str(data["pass"] + pass_salt).encode("utf-8")
    pass_hash = hashlib.sha224(password_data).hexdigest()

    return {
        # auth
        "email": data["email"],
        "aid": aid,
        "pass_hash": pass_hash,
        "pass_salt": pass_salt,

        # account
        # "aid": ..
        "region": data["region"],
        # "email": ..
        "email2": None,
        "is_active": True,
        "role": data["role"],
        "role_id": role_id,
    }


def match_password(pass_hash, pw, pass_salt):
    password_data = str(pw + pass_salt).encode("utf-8")
    return pass_hash == hashlib.sha224(password_data).hexdigest()


def filter_by_keys(data, ary):
    result = {}
    for field in ary:
        result[field] = data[field]
        
    if "role_id" in result:
        result["role_id"] = result["role_id"]
        
    return result


# TODO: secret??
def gen_token(data, fields: List):
    public_info = {}
    secret = ''
    for field in fields:
        val = str(data[field])
        public_info[field] = val
        secret += (field + val)
        
    exp = datetime.now().timestamp() + TOKEN_EXPIRE_TIME
    public_info.update({ "exp": exp })
    return jwt.encode(public_info, secret, algorithm="HS256")
