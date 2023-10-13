import time

def shift_decimal(number, places):
    return number * (10 ** places)

def gen_timestamp():
    return int(shift_decimal(time.time(), 3))