horst
=====

Horst is a flexibe, plugin-driven, easily extendable IRC-bot written in Python
Plugins drive every feature of this bot - they are easy to develop, to debug and to exchange!

Quickstart
----------

* clone the repository: ```git clone https://github.com/daringer/horst.git```
* change into the horst directory: ```cd horst```
* edit config.py.tmpl: ```vim config.py.tmpl```, at least:
  - used_plugins
  - server
  - port 
  - nick 
  - chans

* and save/copy it as/to config.py: ```cp config.py.tmpl config.py```
* run it and have fun: ```python2 horst.py```
* inside the IRC-channel start with ```!helpindex```
* CONTRIBUTE A PLUGIN ...



