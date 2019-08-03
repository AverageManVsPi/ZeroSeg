#!/usr/bin/env python
import ZeroSeg.led as led
import time
from datetime import datetime
import requests
import alpha_vantage
import json
import urllib

device = led.sevensegment(cascaded=2)
device.clear()

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

stock()
