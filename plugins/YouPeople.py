#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from abstract import AbstractPlugin
from utils import FancyDateTime, FancyTime, FancyFloat, FancyDate

__metaclass__ = type

class YouPeople(AbstractPlugin):
    author = "Markus Meissner"
    react_to = {"public": re.compile(r"(?P<all>(i|I)hr(\s|\,|\.)*(L|l)eut(s?))")}

    provide = []

    def react(self, data):
        data.chan << ", ".join(u.name for u in data.chan.users)
        return True

    doc = {}
    __doc__ = "Da werd ich doch sofort mal alle die da sind anschreien, wenn du es mir befiehlst"
