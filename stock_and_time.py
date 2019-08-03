#!/usr/bin/env python
import ZeroSeg.led as led
import time
from datetime import datetime
import requests
import alpha_vantage
import json
import urllib

def clock(device, deviceId, seconds):

    for _ in xrange(seconds):
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        second = now.second
        dot = second % 2 == 0                # calculate blinking dot
        # Set hours
        device.letter(deviceId, 7, int(hour / 10))     # Tens
        device.letter(deviceId, 6, hour % 10)     # Ones
        device.letter(deviceId, 5, "-")
        # Set minutes
        device.letter(deviceId, 4, int(minute / 10))   # Tens
        device.letter(deviceId, 3, minute % 10, dot)        # Ones
        time.sleep(1)

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
        output_filtered = output[:2]
        device.write_text(1, " ZEN " + output_filtered)

device = led.sevensegment(cascaded=2)
device.clear()

while True:
    stock()
    time.sleep(10)
    device.clear()
    clock(device, 1, seconds=10)
    time.sleep(10)
    device.clear()
