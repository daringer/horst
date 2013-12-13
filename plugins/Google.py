#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib
import json

from abstract import AbstractPlugin

__metaclass__ = type

class Google(AbstractPlugin):
    author = "meissna"
    react_to = {"public_command" : re.compile("(?P<query>(.+))")}
    provide = ["google"]
    
    def react(self, data):
        raw_split = data.line["query"].split(" ")
        
        start_idx, end_idx = 0, 1
        if len(raw_split) > 1 and raw_split[0].startswith("#"):
            query = urllib.urlencode({"q": raw_split[1:]})
            splitted = raw_split[0].split(":")

            idx = [int(x) for x in splitted[0][1:].split(":")]
        
            start_idx = idx[0] if idx[0] != "" else 0
            end_idx = (idx[1] + 1) if len(idx) > 1 else (start_idx + 5)            
        else:
            query = urllib.urlencode({"q": data.line["query"]})
        
        url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&{0}".format(query)
        search_results = urllib.urlopen(url)
        google_data = json.loads(search_results.read())
        
        all_results = google_data["responseData"]["results"]
        for i, res in enumerate(all_results):
            if i >= start_idx and i < end_idx:
                num_desc =  "[{0}]".format(i)
                data.chan << re.sub(r"<[^>]*?>", "", res["title"]) + num_desc
                data.chan << res["unescapedUrl"]
                data.chan << re.sub(r"<[^>]*?>", "", res["content"]) 
        
        if len(all_results) == 0:
            data.chan << "Keine Ergebnisse zu dem Query!" 


    doc = {"google": ("google <query>", "Ich google was für dich")}
    __doc__ = "Suchen und Finden mit Google"
