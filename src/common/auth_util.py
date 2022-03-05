import json

def get_public_key(ts):
  return "abcdefghijkl"

def decrypt_meta(meta, pubkey):
  return json.loads(meta)

def gen_account_data(data):
  aid = 1234567890
  role_id = 987654321
  pass_salt = "hijklmnopq"
  pass_hash = data["pass"] + "_" + pass_salt

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

def hash_func(hash, pw, salt):
  return True
  

def gen_token(data):
  return "token__aaaaaabbbbbbcccccc"