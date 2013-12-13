#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from random import choice

from abstract import AbstractPlugin

__metaclass__ = type

class YourMother(AbstractPlugin):
    author = "toby"
    react_to = {"public": re.compile(r"muddi|mutter|mama|mudder|mum", re.IGNORECASE)}
    mother = ["{0}, meine Muddi is so fett, die hat ihre eigene Postleitzahl!", \
                "{0}, meine Muddi is so fett, die gibt im Winter warm und im Sommer Schatten!", \
                "{0}, meine Muddi is wie die Titanik, bis heute weiss keiner, wieviele drauf waren!", \
                "{0}, meine Muddi is so hässlich, dein Vater nimmt sie mit zur Arbeit, damit er ihr keinen Abschiedskuss geben muss!", \
                "{0}, meine Muddi is so fett, die geht ins Kino und sitzt neben jedem!", \
                "{0}, meine Muddi is so fett, wenn die nen Regenmantel anzieht rufen alle \"Taxi!\"!", \
                "{0}, meine Muddi is so fett, die musste im Schwimmbad getauft werden!", \
                "{0}, meine Muddi is so fett, die hat Laufmaschen in ihren _JEANS_ !", \
                "{0}, meine Muddi is so fett, die einzigen Bilder von ihr gibts bei Google Earth!", \
                "{0}, meine Muddi hat Gürtelgrösse Äquator!", \
                "{0}, meine Muddi is so fett, die braucht nen Boomerang, um sich nen Gürtel anzuziehen!", \
                "{0}, meine Muddi ist so dumm, die könnte über ein schnurloses Telefon fallen!", \
                "{0}, meine Muddi ist so dumm, die ordnet M&M's in alphabetischer Reihenfolge!", \
                "{0}, meine Muddi bellt wenns klingelt!", \
                "{0}, meine Muddi trägt 20 Zoll-Felgen als Ohrringe!", \
                "{0}, meine Muddi hängt mal wieder bei Aldi im Drehkreuz fest!", \
                "{0}, meine Muddi hängt mal wieder bei McD in der Kinderrutsche fest!", \
                "{0}, meine Muddi hat homezone auf der Reeperbahn!", \
                "{0}, meine Muddi bläst für Hartgeld!", \
                "{0}, meine Muddi mach hinterm Penny Armdrücken um Flaschengeld!", \
                "{0}, meine Muddi ist so fett, die sitzt in der Kirche neben Gott!", \
                "{0}, meine Muddi ist Türsteher bei McD!", \
                "{0}, meine Muddi ist die haarigste im Zoo!", \
                "{0}, meine Muddi zerreisst Telefonbücher auf DSF!", \
                "{0}, meine Muddi schnitzt Möbel für IKEA!", \
                "{0}, meine Muddi ist Statist und spielt den Todesstern bei StarWars!", \
                "{0}, meine Muddi zockt bei Saturn PlayStation!", \
                "{0}, meine Muddi sortiert den Wühltisch bei KiK!", \
                "{0}, meine Muddi ist wie ein Billardtisch, jeder darf einlochen!", \
                "{0}, meine Muddi hat ne Glatze und ist die Stärkste im Knast!", \
                "{0}, meine Muddi schuppst kleine Kinder vom Fahrrad und riecht am Sattel!", \
                "{0}, meine Muddi zockt CounterStrike mit nem Lenkrad!", \
                "{0}, meine Muddi ist wie ne Packung Böller: 1 Euro für 5x knallen!", \
                "{0}, meine Muddi ist so fett, die wird nicht in kg sondern in m³ gemessen", \
                "{0}, meine Muddi kackt vorm Aldi weil \"drücken\" auf der Tür steht", \
                "{0}, meine Muddi ist so fett, wenn die aufm Bauch liegt kriegt sie Höhenangst!", \
                "{0}, meine Muddi hat mehr Dreier gemacht als BMW!", \
                "{0}, meine Muddi ist so fett, wenn die in die Luft springt bleibt sie stecken!", \
                "{0}, meine Muddi heisst Vincent und redet mit Raben!", \
                "{0}, meine Muddi verbiegt Löffel auf Pro7!", \
                "{0}, für meine Mutter ist Bratensauce ein Erfrischungsgetränk!"]
    
    def react(self, data):
        data.chan << choice(self.mother).format(data.user.name)
