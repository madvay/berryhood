# Copyright (c) 2018 by Advay Mengle - https://github.com/madvay/berryhood
# See the LICENSE and NOTICE files in the root of this repository.

import subprocess
import re
from time import sleep, strftime, time

def vcgencmd(args):
    v = ["/opt/vc/bin/vcgencmd"]
    v.extend(args)
    proc = subprocess.run(v, stdout=subprocess.PIPE, universal_newlines=True)
    return proc.stdout

def vcgencmd_clean(args):
    return vcgencmd(args).strip()

def vcgencmd_parsed(args,meatre):
    r = vcgencmd_clean(args)
    m = re.fullmatch(meatre, r)
    if m is None:
        return None
    return m.group('val')

def temperature():
    return vcgencmd_parsed(['measure_temp'], 'temp=(?P<val>[.0-9]+).+')

def clock_freq(name):
    return vcgencmd_parsed(['measure_clock', name], '[^=]+=(?P<val>[.0-9]+)')

def throttle_state():
    h = vcgencmd_parsed(['get_throttled'], '[^=]+=0x(?P<val>.+)')
    v = int(h, 16)
    ret = ''

    # lower-case letters indicate past-tense;
    # upper-case are current states.
    
    # cpu throttling
    if v & (1 << 18):
        ret = ret + 't'
    else:
        ret = ret + '-'

    # frequency capping
    if v & (1 << 17):
        ret = ret + 'c'
    else:
        ret = ret + '-'
        
    # under-voltage
    if v & (1 << 16):
        ret = ret + 'u'
    else:
        ret = ret + '-'

    # cpu throttling
    if v & (1 << 2):
        ret = ret + 'T'
    else:
        ret = ret + '-'

    # frequency capping
    if v & (1 << 1):
        ret = ret + 'C'
    else:
        ret = ret + '-'

    # under-voltage
    if v & (1 << 0):
        ret = ret + 'U'
    else:
        ret = ret + '-'



    
    return ret

while True:
    print(temperature())
    print(clock_freq('arm'))
    print(throttle_state())
    sleep(1)