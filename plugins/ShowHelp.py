#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from abstract import AbstractPlugin

__metaclass__ = type

class ShowHelp(AbstractPlugin):
    author = "andieh"
    react_to = {"public_command": re.compile(r"(?P<help>(.*))")}
    provide = ["help", "helpindex", "showplugins"]


    def react(self, data):

        all_cmds = self.horst_obj.known_commands
        plugins = self.horst_obj.plugins

        if data.command == "helpindex":
            data.chan << ", ".join(all_cmds.keys())

        elif data.command == "showplugins":
            data.chan << "Showing all active plugins:" 
            for plugin in plugins:
                data.chan << "{0} -> {1}".format(plugin.__class__.__name__, plugin.__doc__)

        elif data.line["help"]:
            cmd = data.line["help"]
            if cmd in all_cmds:
                data.chan << ["Hilfe für: " + all_cmds[cmd].doc[cmd][0], all_cmds[cmd].doc[cmd][1]]
            else:
                data.chan << "Buuuh, keine doku für %s gefunden, gibts das überhaupt???" % cmd  
        else:
            data.chan << "Ich kann schon helfen, das ist doch mal was:" 
            private_list = []
            data.chan << "Public Commands:"
            for cmd, plugin in all_cmds.items():
                private = "_%s" % cmd in plugin.provide
                if not private:
                    data.chan << self.command_prefix + plugin.doc[cmd][0] 
                else:
                    private_list += [plugin.doc[cmd][0]]
            data.chan << "Private Commands:"
            data.chan << private_list

    doc = {"help"        : ("help [command]", "Zeigt dir alle commands, wenn ohne Argument, sonst Details zum 'command'"),
           "helpindex"   : ("helpindex", "Zeige eine Liste aller verfügbaren Befehle an"),
           "showplugins" : ("showplugins", "Zeige eine Liste aller aktiven Plugins an")}
    __doc__ = "Provides the help and show active plugins functionality"
