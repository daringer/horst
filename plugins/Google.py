#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import urllib
import json

from abstract import AbstractPlugin

from config import Config

__metaclass__ = type

class Google(AbstractPlugin):
    author = "meissna"
    react_to = {"public_command" : re.compile(
        "(:(?P<key>[^ ]+)\s*(?P<val>.+)?)|((?P<query>([^#]+))(#(?P<results>[^ ]*))?)")}

    provide = ["google", "gset"]
    aliases = {"g": "google"}

    # private var sets the (google-) language
    lang = "en_US"
    
    def react(self, data):
        # querying the google search
        if data.line["query"] is not None:
            raw_split = data.line["query"].split(" ")
            query = urllib.urlencode({
                  "q": data.line["query"].encode(Config.encoding),
                  "hl": self.lang 
            })
        
            start_idx, end_idx = 0, 1
            if data.line["results"] is not None:
                try:
                    lr = data.line["results"].split(":")
                    start_idx = int(lr[0])
                    if len(lr) > 1:
                        end_idx = int(lr[1])
                    else:
                        end_idx = start_idx + 1
                except ValueError as e:
                    data.chan << "Musst schon anständige indizes übergeben - start: {} end: {}". \
                        format(start_idx, end_idx)
                    return

            url = "http://ajax.googleapis.com/ajax/services/search/web?v=1.0&{0}". \
                    format(query)

            search_results = urllib.urlopen(url)
            google_data = json.loads(search_results.read())
        
            all_results = google_data["responseData"]["results"]
            for i, res in enumerate(all_results):
                if i >= start_idx and i < end_idx:
                    
                    data.chan << "[{}] {}".format(i, re.sub("<[^>]*?>", "", \
                            res["title"].encode("utf-8")))
                    data.chan << "[{}] {}".format(i, \
                            res["unescapedUrl"].encode("utf-8"))
                    data.chan << "[{}] {}".format(i, re.sub("<[^>]*?>", "", \
                            res["content"].encode("utf-8")))

        
            if len(all_results) == 0:
                data.chan << "Keine Ergebnisse zu dem Query - buuuuuh!" 

        elif data.line["key"] is not None:
            if data.line["key"] == "lang":
                if data.line["val"] is not None:
                    self.lang = data.line["val"]
                    data.chan << "Plugin Google - Setze '{}' auf '{}'". \
                            format(data.line["key"], data.line["val"])
                else:
                    data.chan << "Plugin Google - Variable: {} Inhalt: {}". \
                            format(data.line["key"], self.lang)
            else:
                data.chan << "Du willst eine Variable setzen die es nicht gibt: {}". \
                        format(data.line["key"])
                data.chan << "ähm jaaa ist 'erledigt'..."

        else:
            data.chan << "Versteh die Argumente von dir nicht..."

    doc = {"google": ("google <query> [#start_idx[:end_idx]]", "Googele mal <query> und zeige results 'start_idx' bis 'end_idx' - defaults: start_idx=0, end_idx=1"),
           "gset":   ("gset :<var_key> [value]", "Setzte variable: <var_key> wenn [value] vorhanden. Ohne [value] gebe ich den Inhalt aus.")}
    __doc__ = "Google services und stuff..."
