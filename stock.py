#!/usr/bin/env python
import ZeroSeg.led as led
import time
from datetime import datetime
import requests
import alpha_vantage
import json
import urllib
import RPi.GPIO as GPIO

# setup buttons
button1 = 17
button2 = 26
GPIO.setmode(GPIO.BCM) # Use BCM GPIO numbers
GPIO.setup(button1, GPIO.IN)
GPIO.setup(button2, GPIO.IN)

# cleanup before run
device = led.sevensegment(cascaded=2)
device.clear()

# set brightness to minimal
level = 1

# check Zendesk stock price
def stock():
    API_URL = "https://www.alphavantage.co/query"
    symbols = ['ZEN']
    for symbol in symbols:
        data = { "function": "GLOBAL_QUOTE",
                 "symbol": symbol,
                 "datatype": "json",
                 "apikey": "YOUR_API_KEY_HERE" }
        response = requests.get(API_URL, data)
        data = response.json()
        output = data["Global Quote"]["05. price"]
        output_filtered = output[:4]
        device.write_text(1, "ZEN "+ output_filtered)

while True:
    device.brightness(level)
    if not GPIO.input(button1):
        if level == 1:
            print "MIN"
            time.sleep(0.5)
        if level >= 2:
            level = level -1
            print "-1 ", level
            time.sleep(0.5)

    elif not GPIO.input(button2):
        if level == 15:
            print "MAX"
            time.sleep(0.5)
        if level <= 14:
            level = level +1
            print "+1 ", level
            time.sleep(0.5)
    stock()