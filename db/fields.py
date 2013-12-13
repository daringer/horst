#!/usr/bin/python
#-*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty
import time

from core import DatabaseError
from baserecord import BaseRecord

__metaclass__ = type

# fancier use of properties
Property = lambda func: property(**func()) 

class AbstractField(object):
    """Every Field class should be a derivate from this class"""
    __metaclass__ = ABCMeta
    
    sqlite_name = None
    default_value = None
    accepted_keywords = []
    general_keywords = ["default"]
   
    @Property
    def name():
        def fget(self):
            return self._name
        def fset(self, val):
            self._name = val
        return locals()
    
    @Property
    def colname():
        def fget(self):
            if issubclass(self.__class__, ManyToOneRelation):
                return self.name + "_id"
            elif self.sqlite_name:
                return self.name
            else:
                return None  
        return locals()
        
    def __init__(self, **kw):
        # check if kw contains only legal keywords
        wrong = [k for k in kw if not k in (self.accepted_keywords + self.general_keywords)]
        if len(wrong) != 0:
            raise DatabaseError("Keyword(s): %s not supported by this Field: %s" % (", ".join(wrong), self.__class__.__name__))
        
        for k, v in kw.items():
            setattr(self, k, v) 

        self._value = self.default_value if not "default" in kw else kw["default"]
        self.parent = None
        self.passed_kw = kw

    # don't raise exception on non-existing attribute, just return None
    def __getattr__(self, key):
        return None

    def clone(self):
        """Mainly internal use - returnes a clone (copy) of the AbstractField"""
        return self.__class__(name=self.name, **self.passed_kw)

    def get_create(self):
        """Get line to add in a CREATE or ALTER statement"""
        out = "%s %s" % (self.colname, self.sqlite_name)
        if self.length:
            out += "(%s)" % self.length
        if self.unique:
            out += " UNIQUE"
        return out

    def set(self, v):
        """Set field value to 'v'"""
        self._value = v

    def get(self):
        """Get field value"""
        return self._value

    def pre_save(self, action="insert", obj=None):
        """This is called directly before saving the object"""
        return True
        
    def post_save(self, action="insert", obj=None):
        """This is called directly after the object was saved"""
        return True    

class IntegerField(AbstractField):
    sqlite_name = "INT"
    default_value = 0
    accepted_keywords = ["unique", "name"]

class BooleanField(IntegerField):
    accepted_keywords = ["name"]
    
    def __init__(self, **kw):
        if "default" in kw:
            assert kw["default"] in [True, False, 0, 1]
             
        super(BooleanField, self).__init__(**kw)
    

class DateTimeField(IntegerField):
    accepted_keywords = ["name", "auto_now", "auto_now_add", "unique"]
  
    def pre_save(self, action="insert", obj=None):
        if (action == "insert" and (self.auto_now_add or self.auto_now)) or \
           (action == "update" and self.auto_now):
            self.set(int(time.time()))
        return True
      
class FloatField(IntegerField):
    sqlite_name = "FLOAT"
    default_value = 0.0    
    accepted_keywords = ["name"]
    
class StringField(AbstractField):
    default_value = ""
    accepted_keywords = ["unique", "name", "length"]
    
    def __init__(self, **kw):
        super(StringField, self).__init__(**kw)
        if self.length > 250:
            self.sqlite_name = "TEXT"
        else:
            self.sqlite_name = "VARCHAR"
    
    def pre_save(self, action="insert", obj=None):
        self.set(self._value.strip())
        return True

class OptionField(StringField):
    accepted_keywords = ["options", "name"]
    sqlite_man = "VARCHAR"
    
    def __init__(self, options, **kw):
        # options must be a regular list of strings, iterable is ok
        assert hasattr(options, "__iter__") and len(options) > 1
        self.options = options
        kw.update({"options":options})
    
        # the default value defualts to first item of options if not specified
        if "default" in kw:
            assert kw["default"] in options
            default = kw["default"]
        else:
            default = options[0]
        kw.update({"default": default})            
            
        super(OptionField, self).__init__(**kw)
        
    def pre_save(self, action="insert", obj=None):
        if not self.get() in self.options:
            return False
        return True
      
class AbstractRelationField(AbstractField):
    accepted_keywords = ["name", "related_record"]
    
    def __init__(self, related_record, **kw):
        assert issubclass(related_record, BaseRecord)
        self.related_record = related_record
        
        kw.update({"related_record" : related_record})
        super(AbstractRelationField, self).__init__(**kw)
  
class OneToManyRelation(AbstractRelationField):
    default_value = []
    
    def get_related_col(self):
        for f in self.related_record.base_fields.values():
            if f.related_record:
                if self.name in f.related_record.base_fields:
                    col = f.related_record.table
                    return col
    
    def get(self):
        from core import DataManager
        return DataManager(self.related_record, pre_filter={self.get_related_col():self.parent})
            
    def set(self, val):
        # save parent or we can't save the related entities
        if not self.parent.rowid:
            self.parent.save()
        
        # directly saving all relations seems not the smartest way to get what we want    
        if hasattr(val, '__iter__'):
            for item in val:
                item.fields[self.get_related_col()].set(self.parent)
                item.save()   
        else:
            raise DatabaseError("passed argument must be an iterable not: %s" % type(val))
            
class ManyToOneRelation(AbstractRelationField):
    sqlite_name = "INT"
    default_value = 0
    
    def get(self):
        return self._value
        
    def set(self, val):
        if val is not None:
            assert issubclass(val.__class__, BaseRecord)
        self._value = val
        
        
        
#class ManyToManyRelation(RelationField):
#    pass
    