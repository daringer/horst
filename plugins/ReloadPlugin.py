#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import datetime
import time

from abstract import AbstractPlugin

__metaclass__ = type

class ReloadPlugin(AbstractPlugin):
    author = "meissna"
    react_to = {"public_command": re.compile(r"(?P<plugin_name>.*)") }

    provide = ["reload"]
    aliases = {"rl": "reload"}

    def react(self, data):
        name = data.line["plugin_name"]

        if name in self.horst_obj.name2pobj:
            try:
                self.horst_obj.init_plugin(name, relo=True)
                data.chan << "Wohoo, Plugin/Modul ({}) neu geladen, bam!".format(name)
            except Exception as e:
                data.chan << "FUUUUCK -> {} Fehlerdinges waerend dem relaod, fies - gogo fix das!". \
                        format(e.__class__.__name__)
                data.chan <<  e, e.message
        else:
            data.chan << "Konnte plugin: '{}' nicht finden!". \
                    format(data.line["plugin_name"])

    doc = { "reload": ("reload <plugin_name>", "Reloade das plugin: <plugin_name>") }

    __doc__ = "Dieses plugin ermöglicht das reloaden von spezifischen Plugins!"
