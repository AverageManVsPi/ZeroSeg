#!/usr/bin/env python

import time, requests, alpha_vantage, json, urllib
import ZeroSeg.led as led
from datetime import datetime

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
        output_filtered = output[:4]
        device.write_text(1, " " + output_filtered)

def how_rich_am_i(output_filtered):
    number_of_stocks_total = XXX # change XXX to your total number of owned stocks
    richness = number_of_stocks_total * output_filtered
    device.write_text(1, richness)

while True:
    stock()
    time.sleep(10)
    how_rich_am_i()
    time.sleep(10)