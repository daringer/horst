#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

available_plugins = [p.replace(".py","") for p in os.listdir("plugins") if not p.startswith("__") and p.endswith(".py")]
