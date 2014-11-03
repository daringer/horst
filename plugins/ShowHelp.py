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
        plugins = sorted(self.horst_obj.name2pobj.values(), key=lambda x: x.__class__.__name__)
        aliases = self.horst_obj.known_aliases

        ### show all available (public) commands 
        if data.command == "helpindex":
            data.chan << ", ".join("{}=>{}".format(x, aliases[x]) \
                    if x in aliases else x for x in sorted(all_cmds.keys()))

        ### show all active plugins
        elif data.command == "showplugins":
            data.chan << "Zeige alle aktiven Plugins:" 
            for plugin in plugins:
                data.chan << "{} -> {}". \
                        format(plugin.__class__.__name__, plugin.__doc__)

        ### show help for one specific command
        elif data.line["help"]:
            cmd = data.line["help"]
            if cmd in all_cmds:
                data.chan << ["Hilfe für: {} {}".format(
                    all_cmds[cmd].doc[cmd][0],all_cmds[cmd].doc[cmd][1])]
            else:
                data.chan << "Buuuh, keine Doks für {} gefunden".format(cmd)
                data.chan << "... das geht doch gar nicht!?"

        ### show generic - full help overview
        else:
            data.chan << "Ich kann schon helfen, das ist doch mal was:" 
            data.chan << "-------- öffentliche --------"
            private_list, alias_list = [], []
            for cmd, plugin in all_cmds.items():
                private = "_{}".format(cmd) in plugin.provide 
                if not private and cmd not in aliases:
                    data.chan << self.command_prefix + plugin.doc[cmd][0] 
                elif cmd in aliases:
                    alias_list.append("{} => {}".format(cmd, aliases[cmd]))
                else:
                    private_list.append(plugin.doc[cmd][0])
                    
            data.chan << "-------- privat --------"
            data.chan << private_list
            data.chan << "-------- alias --------"
            data.chan << (", ".join(alias_list))

    doc = {"help"        : ("help [command]", "Zeigt dir alle commands, wenn ohne Argument, sonst Details zum 'command'"),
           "helpindex"   : ("helpindex",      "Zeige eine Liste aller verfügbaren Befehle an, inklusive Aliase...."),
           "showplugins" : ("showplugins",    "Zeige eine Liste aller aktiven Plugins an")}

    __doc__ = "Provides the help and show active plugins functionality"
