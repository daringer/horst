#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time
import sys

from abstract import AbstractPlugin
from utils import FancyDateTime, FancyTime, FancyFloat, FancyDate

__metaclass__ = type

class SelfKill(AbstractPlugin):
    author = "meissner"

    react_to = {"public": re.compile(r"(?P<all>.+)") } 

    provide = ["selfkill"]

    def react(self, data):
	data.chan << "Auf Wiedersehen du grauuuuusaaammmmeeee Weeeeelttt......."
	sys.exit(1)

    doc = { "selfkill": ("selfkill", "Ich werde mich sofort selbst beerdigen - bitte nicht, neeeeiiiinnnn!") }

    __doc__ = "Einfach Horst ausschalten - er kommt sicher wieder..."
