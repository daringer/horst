#!/usr/bin/python
#-*- coding: utf-8 -*-

import time

from baserecord import BaseRecord
from fields import StringField, IntegerField, DateTimeField, OneToManyRelation, FloatField, OptionField
from core import Database


class Konto(BaseRecord):
    nr = IntegerField(unique=True)
    dispot = IntegerField()
    guthaben = FloatField()
    art = OptionField(["Giro", "Sparbuch", "Firma", "Aktiendepot"])
    
class Kunde(BaseRecord):
    name = StringField(length=100, unique=True)
    seit = DateTimeField(auto_now_add=True)
    letzter_besuch = DateTimeField(auto_now=True)
    kontos = OneToManyRelation(Konto)
    anschrift = StringField(length=500)    


fn = "horst.sqlite"
import os
if os.path.exists(fn):
    os.unlink(fn)

Database().check_for_tables()

###############################

meissna = Kunde(name="Markus Meissner", anschrift="Bla Hanau")
meissna.save()

k1 = Konto(nr=61093, dispot=1000, guthaben=-500, art="Firma", kunde=meissna)
k2 = Konto(nr=100344290, dispot=1000, guthaben=-500, art="Giro", kunde=meissna)

k1.save()
k2.save()

print "Orginal Kontobjekte - Meissna-Kunde:"
print k1
print k2
print meissna

###############################

k3 = Konto(nr=123421, dispot=400, guthaben=300, art="Giro")
k3.save()

andieh = Kunde(name="Andreas Fuertig", anschrift="Bla Frankfurt", kontos=[k3])
andieh.save()

print 
print "Orginal Kontobjekt - Andieh-Kunde:"
print k3
print andieh

###############################

k4 = Konto(nr=87234, dispot=5000, guthaben=2504.32,  art="Sparbuch")
k4.save()

mustermann = Kunde(name="Max Mustermann")
mustermann.anschrift = "Bla Musterhausen"
mustermann.save()

mustermann = Kunde.objects.get(name="Max Mustermann")
mustermann.kontos = [k4]
mustermann.kontos[0].guthaben -= 2000
mustermann.save()

print
print "Bezogenes Objekt vom Mustermann" 
print mustermann
print mustermann.kontos[0]


k = Konto.objects.all()[0]
print k.kunde.name
print k.kunde.kontos[0].kunde.name

print
print "Teeesting.... DataManager"
print Konto.objects[0]


print
print "Testing.... DataManager verketten"
print Kunde.objects.get(name="Markus Meissner").kontos.filter(art="Giro")

 
