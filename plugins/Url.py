#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time 
from urllib2 import urlopen 
from random import choice

from db.fields import BaseRecord, IntegerField, StringField, FloatField, DateTimeField, BooleanField
from abstract import AbstractPlugin
from utils import FancyDateTime, FancyTime, FancyFloat, FancyDate

__metaclass__ = type

class UrlRecord(BaseRecord):
    url = StringField(size=20000, unique=True)
    title = StringField(size=20000)
    pub_date = DateTimeField(auto_now_add=True)

class Url(AbstractPlugin):
    author = "meissna"

    react_to = {"public": re.compile("(?P<url>((?P<protocol>(http(?:s)?\:\/\/)?)[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,6}(?:\/?|(?:\/[\w\-]+)*)(?:\/?|\/\w+\.[a-zA-Z]{2,4}(?:\?[\w]+\=[\w\-]+)?)?(?:\&[\w]+\=[\w\-]+)*)([^ ]*))"),
                 "public_command": re.compile(r"(?P<query>.*)") } 

    provide = ["url"]

    title_pat = re.compile("<title>([^<]*)</title>")

    def react(self, data):
        
        if data.reaction_type == "public":
            myurl = data.line["url"]
            if not myurl.startswith("http"):
                myurl = "http://{}".format(myurl)

            content = urlopen(myurl).read()
            title = self.title_pat.findall(content)
            if isinstance(title, (list, tuple)):
                title = title[0]

            u = UrlRecord.objects.get(url=myurl)
            if u is not None:
                data.chan << "Pffff, laaaangweilig, die URL hab ich schon gesehn, vor laaaanger Zeit: {}".\
                        format(FancyDateTime(u.pub_date).get())
            else:

                data.chan << "URL gefunne: {}".format(myurl)
                data.chan << "Titel: {}".format(title)

                o = UrlRecord(url=myurl, title=title)
                o.save()

        elif data.reaction_type == "public_command":
            if data.line["query"] is not None:
                data.chan << "Kann nocht nicht suchen ... n00b!"

            objs = UrlRecord.objects.all()
            if objs is not None:
                out = choice(objs)
                data.chan << "Gugge ma da: {}".format(out.url)
                data.chan << "so halt: {}".format(out.title)

    doc = { "url": ("url [query]", "Wenn [query] nicht gesetzt ist gebe ich eine beliebige url aus, sonst suche ich nach [query]")}
    __doc__ = "Schön artig zuhören bis ich eine URL finde, die besuche ich dann und merk sie mir, dann kannst du mich fragen später..."
