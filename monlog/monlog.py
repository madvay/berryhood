# Copyright (c) 2018 by Advay Mengle - https://github.com/madvay/berryhood
# See the LICENSE and NOTICE files in the root of this repository.

import subprocess
import urllib.parse
import time
from threading import Thread
import urllib.request
import os
import re
from sense_hat import SenseHat
from time import sleep, strftime, time

MIL = 1000000

C_RED = (255,0,0)
C_BLACK = (0,0,0)
C_BLUE = (0,0,255)
C_GREEN = (0,255,0)
C_WHITE = (255,255,255)

sense = None
try:
    sense = SenseHat()
    sense.clear(C_BLACK)
    sleep(0.25)
    sense.clear(C_RED)
    sleep(0.25)
    sense.clear(C_GREEN)
    sleep(0.25)
    sense.clear(C_BLUE)
    sleep(0.25)
    sense.clear(C_WHITE)
    sleep(0.25)
    sense.clear(C_BLACK)
except:
    sense = None

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

def ifttt_report(v1, v2, v3):

    def ifttt_report_impl():
        url = 'https://maker.ifttt.com/trigger/berry_metrics/with/key/' + os.environ['IFTTT_TOKEN']
        values = {'value1' : v1,
                'value2' : v2,
                'value3' : v3 }
        form = urllib.parse.urlencode(values)
        data = form.encode('utf-8')
        req = urllib.request.Request(url, data)
        with urllib.request.urlopen(req) as resp:
            _ = resp.read()

    t = Thread(target=ifttt_report_impl, args=())
    t.start()

def display(temp, freq, state):
    if not sense:
        return
    def display_impl():
        sense.set_pixel(0,0,C_RED)
        sense.set_pixel(0,1,C_RED)
        sleep(0.25)
        sense.set_pixel(0,0,C_BLACK)
        sense.set_pixel(0,1,C_BLACK)

    t = Thread(target=display_impl, args=())
    t.start()

while True:
    temp = float(temperature())
    freq = int(clock_freq('arm'))
    state = throttle_state()

    print('{0:>5.1f} C   {1:>8.2f} MHz   {2:8s}'.format(temp, freq/MIL, state))
    ifttt_report(temp, freq, state)
    display(temp, freq, state)
    sleep(10)
