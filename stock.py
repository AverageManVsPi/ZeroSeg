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
device.brightness(level)

# check Zendesk stock price
def stock():
    API_URL = "https://www.alphavantage.co/query"
    symbols = ['ZEN']
    for symbol in symbols:
        data = { "function": "GLOBAL_QUOTE",
                 "symbol": symbol,
                 "datatype": "json",
                 "apikey": "YOUR_API_KEY" }
        response = requests.get(API_URL, data)
        data = response.json()
        output = data["Global Quote"]["05. price"]
        output_filtered = output[:6]
        device.write_text(1, "-" + output_filtered + "-")

stock()
