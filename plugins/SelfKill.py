#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys, os

from abstract import AbstractPlugin

__metaclass__ = type

class SelfKill(AbstractPlugin):
    author = "meissner"

    react_to = {"public": re.compile(r"(?P<all>.+)") } 

    provide = ["selfkill"]

    def react(self, data):
	data.chan << "Auf Wiedersehen du grauuuuusaaammmmeeee Weeeeelttt......."
	os.system("killall python")

    doc = { "selfkill": ("selfkill", "Ich werde mich sofort selbst beerdigen - bitte nicht, neeeeiiiinnnn!") }

    __doc__ = "Einfach Horst ausschalten - er kommt sicher wieder..."
