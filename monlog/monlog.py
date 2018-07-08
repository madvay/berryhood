#!/usr/bin/env python3

# Copyright (c) 2018 by Advay Mengle - https://github.com/madvay/berryhood
# See the LICENSE and NOTICE files in the root of this repository.

import subprocess
import urllib.parse
import time
import datetime
import sys
import threading
from datetime import datetime
from threading import Thread
from time import sleep
import urllib.request
import os
import re
from sense_hat import SenseHat
import logging
from logging.handlers import TimedRotatingFileHandler
import signal
import argparse

min_temp = 40
max_temp = 80
min_freq = 600000000
max_freq = 1400000000

parser = argparse.ArgumentParser(description='Monitor Logger',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-s", "--sensehat",
                    help="enables the Sense HAT LEDs, optionally",
                    action="store_true")
parser.add_argument("--sensehat_required",
                    help="fails if the Sense HAT LED cannot be loaded (requires --sensehat also)",
                    action="store_true")
parser.add_argument("-i", "--ifttt",
                    help="posts metrics to IFTTT using the key stored in env var IFTTT_TOKEN",
                    action="store_true")
parser.add_argument("--ifttt_period", help="send an IFTTT post every N executions", type=int, default=1)
parser.add_argument("-p", "--period", type=float, default=1,
                    help="seconds to sleep between monitoring")
parser.add_argument("--min_temp", type=float, default=min_temp, help="Min bar graph temperature")
parser.add_argument("--max_temp", type=float, default=max_temp, help="Max bar graph temperature")
parser.add_argument("--min_freq", type=int, default=min_freq, help="Min bar graph frequency")
parser.add_argument("--max_freq", type=int, default=max_freq, help="Max bar graph frequency")
parser.add_argument("--led_rotation", help="rotation of the Sense HAT LEDs (90deg increments)",
                    type=int, default=0)


parser.add_argument("--log", help="path to log to", type=str, default=None)
parser.add_argument("--log_days", help="days of logs to keep", type=int, default=7)
parser.add_argument("--log_period", help="print/log every N executions", type=int, default=1)

# Sets up our logs, and redirects stdout/err to those logs
def setup_logs(path, days):
    logger = logging.getLogger(__name__)
    handler = TimedRotatingFileHandler(path, when='midnight', backupCount=days)
    formatter = logging.Formatter('%(asctime)s [%(levelname)-10s] <%(name)s> %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    class LoggerStream:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level

        def write(self, msg):
            # skip the garbage
            if msg != '\n':
                self.logger.log(self.level, msg)

        def flush(_):
            # can't force a flush of the logger
            return

    sys.stderr = LoggerStream(logger, logging.ERROR)
    sys.stdout = LoggerStream(logger, logging.INFO)
    return logger


args = parser.parse_args()

if args.log:
    setup_logs(args.log, args.log_days)

min_temp = args.min_temp
max_temp = args.max_temp
min_freq = args.min_freq
max_freq = args.max_freq

MIL = 1000000

BRIGHTNESS = 64
FULLB = BRIGHTNESS

C_BLACK = (0,0,0)
C_DIM = (int(FULLB*3/4),int(FULLB*3/4),int(FULLB*3/4))

C_RED = (FULLB,0,0)
C_GREEN = (0,FULLB,0)
C_BLUE = (0,0,FULLB)


C_YELLOW = (FULLB,FULLB,0)
C_PURPLE = (FULLB,0,FULLB)
C_CYAN = (0,FULLB,FULLB)

C_WHITE = (FULLB,FULLB,FULLB)

last_blink = 0


sense = None
if args.sensehat:
    print('Attempting to load Sense HAT')
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
        sense.set_rotation(args.led_rotation)
        sense.low_light = False
    except:
        print("Failed to load Sense HAT")
        if args.sensehat_required:
            raise
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
    if not (args.ifttt and 'IFTTT_TOKEN' in os.environ):
        return

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

def drawbar(val, vmin, vmax, x, color):
    lin = (val - vmin) / (vmax - vmin)
    mlin = int(max(0,min(8,round(lin * 8,0))))
    for y in range(0, 8):
        if y < mlin:
            sense.set_pixel(x,y,color)
        else:
            sense.set_pixel(x,y,C_BLACK)
    if mlin == 0:
        sense.set_pixel(x,0,C_RED)

def display(temp, freq, state):
    global last_blink
    if not sense:
        return
    def display_impl(blink):
        if blink:
            sense.set_pixel(0,0,C_DIM)
            sense.set_pixel(0,1,C_BLACK)
        else:
            sense.set_pixel(0,0,C_BLACK)
            sense.set_pixel(0,1,C_DIM)
        drawbar(temp, min_temp, max_temp, 2, C_GREEN)
        drawbar(freq, min_freq, max_freq, 4, C_BLUE)

        sense.set_pixel(7,0,C_RED if ('U' in state) else C_BLACK)
        sense.set_pixel(7,1,C_GREEN if ('C' in state) else C_BLACK)
        sense.set_pixel(7,2,C_BLUE if ('T' in state) else C_BLACK)

        sense.set_pixel(7,5,C_RED if ('u' in state) else C_BLACK)
        sense.set_pixel(7,6,C_GREEN if ('c' in state) else C_BLACK)
        sense.set_pixel(7,7,C_BLUE if ('t' in state) else C_BLACK)

    #t = Thread(target=display_impl, args=(last_blink < 1,))
    #t.start()
    display_impl(last_blink<1)
    last_blink = 1 - last_blink

printon = 0
ifttton = 0
def oneshot():
    global printon, ifttton
    temp = float(temperature())
    freq = int(clock_freq('arm'))
    state = throttle_state()

    if printon % args.log_period == 0:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f %Z')
        print('{3}  {0:>5.1f} C   {1:>8.2f} MHz   {2:8s}'.format(temp, freq/MIL, state, ts))
    printon = printon + 1
    if ifttton % args.ifttt_period == 0:
        ifttt_report(temp, freq, state)
    ifttton = ifttton + 1
    display(temp, freq, state)


muststop = False
def stop(sig, frame):
    global muststop
    print('SIGTERM captured')
    muststop = True

signal.signal(signal.SIGTERM, stop)

def loop():
    when = time.time()
    period = args.period
    while not muststop:
        oneshot()
        when = when + period
        # Reduce sleep drift.
        s = when - time.time()
        if s > 0:
            sleep(s)
    print('Exitting')
    if sense:
        sense.clear(C_YELLOW)
        sleep(0.1)
        sense.clear(C_BLACK)

loop()
