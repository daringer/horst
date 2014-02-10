#!/usr/bin/python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from utils import Channel, User, Data

__metaclass__ = type

class AbstractPlugin:
    """
    Available properties for a plugin:
      "provide"        -> a list of commands provided by this plugin
      "react_to"       -> has to be a dict with keys out of these:
                          ["private", "public", "dcc", "join", "leave",
                          "server_connect", "enter_channel", "nick_change", "leave_channel",
                          "public_command"]

                          The values must be a compiled regular expression
                          like returned from re.compile(). Use (?:\s+) to
                          match whitespaces and use named groups so the resulting
                          dict will be passed to react(). An example:
                          re.compile("(?P<command>foo)(?:\s+)(?P<option>do|not|yes)(?:\s+)(?P<value>.+)") 

      "timer"          -> list of 2-tuples, register the provided method(s) for a timer based execution.
                          You may register the method as string or as a callable object!
                          [("methodname", timeout_in_seconds), (method_object, timeout_in_seconds)]

      "config"         -> a dict providing configuration data for this plugin
      "needed_configs" -> a list of mandatory configuration items to be found inside the config-dict

      "author"         -> The plugin author
      "doc"            -> a dictionary containing 2-tuples with the command as
                          key to show help.  only if plugin contains commands, all items from
                          self.provide must be availible as keys here.
      "__doc__"        -> regular docstring to shortly describe the plugin's features
    """

    __metaclass__ = ABCMeta
 
    author = ""
    react_to = {}
    provide = None

    timer = None
    
    config = {}
    needed_configs = None
    
    doc = None
    __doc__ = None
   
    # this has to be implemented by the new plugin
    @abstractmethod
    def react(self, data):
        pass

    ## those two are not intended to be overloaded
    ## if you need to overload __init__ DON'T FORGET to super(MyPlugin, self).__init__(*v, **kw)
    ## but actually there is absolutly no need, so DON'T DO IT!
    def __init__(self, horst_obj, *v, **kw):
        # inherit various properties from bot
        self.horst_obj = horst_obj
	self.config = self.horst_obj.config.plugin_configs.get(self.__class__.__name__) or {}
        self.command_prefix = self.cp = horst_obj.command_prefix

        # check if plugin fulfills conventions (react_to consistency)
        assert isinstance(self.react_to, dict)
        for key, val in self.react_to.items():
            assert key in ["private", "public", "dcc", "join", "leave",
                           "server_connect", "enter_channel", "nick_change", "leave_channel",
                           "public_command"], key
            assert val.search, "The value of react_to must be an obj from re.compile()"

        # check for correct timer contents, if applicable
        if self.timer is not None:
            assert isinstance(self.timer, list), "The timer attribute must be a list!"
            for obj in self.timer: 
                assert isinstance(obj, tuple) and len(obj) == 2,\
                    "The timer attribute may only \
                     contain tuples inside the list with the length of 2!"
                func, timeout = obj
                assert isinstance(func, str) or callable(func),\
                    "The first item inside the tuple must be \
                     either a string naming the method, or a callable object!"
                assert isinstance(timeout, (int, long)), \
                    "The second item inside the tuple must be an integer/long!"

	# check for author and __doc__ attribute
        assert isinstance(self.author, str), \
		"No author was set inside {0}".format(self.__class__.__name__)
	assert isinstance(self.__doc__, str), \
		"No info attribute was set inside {0}".format(self.__class__.__name__)
        
        # make sure all entries inside provide-list have an entry inside the doc-dict
        if self.provide is not None:
            assert all((cmd if not cmd.startswith("_") else cmd[1:]) in self.doc for cmd in self.provide), \
                "Not documented Plugin - commands: %s" % ", ".join(self.provide)

	# check if config-dict contains all items from needed_config-list
	if self.needed_configs is not None:
            assert all(k in self.config.keys() for k in self.needed_configs), \
                "Not all required config parameters for plugins provided!"

        # append timer(s) to appropriate dict
	if self.timer is not None:
		for func, timeout in self.timer:
			if isinstance(func, str):
				func = getattr(self, func)
				assert callable(func), "There is no method called: {}".format(func) 
		    	horst_obj.timers.append( (func, timeout, timeout) )

    def handle_input(self, data):
        assert isinstance(data, Data)
        
        for r_type, regexp in self.react_to.items():
            if data.reaction_type != r_type:
                continue
            match = regexp.search(data.line_raw)
            if match:
                data.line = match.groupdict()
                
                # strip whitespaces here, good place? (don't if data.line[k] is not str, means is equal None)
                for k in data.line:
                    data.line[k] = data.line[k].strip() if isinstance(data.line[k], str) else data.line[k]
                        
                self.react(data)
            elif data.reaction_type in ["public_command", "private"]:
                data.chan << "Das Plugin konnte nix mit deinen Argumenten anfangen, rtfm !help"

