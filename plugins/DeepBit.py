#!/usr/bin/python
# -*- coding: utf-8 -*-

from abstract import AbstractPlugin
import re
import datetime
import time
import json, urllib

__metaclass__ = type

class DeepBit(AbstractPlugin):
    author = "meissna"

    react_to = {"public_command": re.compile(r"")}

    provide = ["btc"]
 
    needed_configs = ["api_key"]

    def react(self, data):
        API_KEY = self.config["api_key"] 
        API_BASE = 'http://deepbit.net/api/'
        url = API_BASE + API_KEY
        try:
            tmp = json.load(urllib.urlopen(url))
            result = "Rate: {0}Mh/s Reward: {1}btc".format(tmp["hashrate"], tmp["confirmed_reward"])
        except:
            result = "Could not get data..."
        data.chan << result

        return True

    doc = { "btc": ("btc", "Show DeepBit miner status") }

    __doc__ = "This plugin shows a DeepBit miner status"
