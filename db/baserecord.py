#!/usr/bin/python
#-*- coding: utf-8 -*-

from core import DatabaseError, DataManager, Database

__metaclass__ = type

class MetaBaseRecord(type):
    """The MetaClass used to accomplish the dynamic generated Record classes"""
    def __init__(cls, name, bases, dct):
        
        # exclude the base class from this behaviour
        if not name == "BaseRecord":                
            cls.table = name.lower()
            
            # move all "*Fields" to self.fields and init attributes to None
            cls.base_fields = {}
            for att in cls.__dict__.keys()[:]:
                if len(att) < 2:
                    raise DatabaseError("For _reasons unknown_ fieldnames must have at least 2 characters")
                field = getattr(cls, att)
                from fields import AbstractField
                if issubclass(field.__class__, AbstractField):
                    cls.setup_field(att, field)
                    
            cls.database = Database()
            cls.database.contribute(cls)
            
            cls.objects = DataManager(cls)

class BaseRecord(object):
    """Every Record Class has to derive from this Class"""
    __metaclass__ = MetaBaseRecord
    
    @classmethod
    def setup_field(cls, name, field):
        """Only for internal use, don't mess with it!"""
        field.name = name
        cls.base_fields[name] = field
        
        if hasattr(cls, name):
            delattr(cls, name)

    def __init__(self, **kw):
        # special 'rowid' handling
        if "rowid" in kw:
            self.rowid = kw["rowid"]
            del kw["rowid"]
        else:
            self.rowid = None

        # copy class base_fields to instance
        self.fields = {}
        for name, field in self.__class__.base_fields.items():
            self.fields[name] = field.clone()

        # check for _id and cut them away (this will lead to naming restrictions, 
        # but who uses "_id" in an object driven database-abstraction anyway)
        kw = dict(((k, v) if not k.endswith("_id") else (k[:-3], v)) for k, v in kw.items())        

        # if there is some keyword-argument, that is not handled by the record, throw exception
        for key in kw:
            if not key in self.fields:
                raise DatabaseError("The field/keyword: '%s' was not found in the record" % key)

        # set this obj as parent for all fields
        for name, field in self.fields.items():
            field.parent = self
        
        # process keywords -> values passed
        from fields import ManyToOneRelation, OneToManyRelation
        for k, v in kw.items():
            field = self.fields[k]
            if issubclass(field.__class__, OneToManyRelation):
                field.set(v)
            elif issubclass(field.__class__, ManyToOneRelation):
                rid = v if isinstance(v, int) else v.rowid
                field.set(field.related_record.objects.get(rowid=rid))
            else:
                field.set(v)

    # yes save... means WHAT? save all containing items, too???                
    def save(self):
        """Save object in database"""
        ret = self.database.save_obj(self)
        if self.database.lastrowid:
            self.rowid = self.database.lastrowid
        return ret

    def destroy(self):
        """Destroy (delete) object and row in database"""
        return self.database.delete_obj(self)

    def __iter__(self):
        """Iterator that returns (colname, value) for this object"""
        for f in ["rowid"] + self.fields.keys():
            yield (f, getattr(self, f))

    def __repr__(self):
        data = [(k,v) if not isinstance(v, list) else (k, ("<%s rowids=[%s]>" % (v and v[0].__class__.__name__, ", ".join(str(x.rowid) for x in v)))) for k, v in self]
        return "<%s %s>" % (self.__class__.__name__, " ".join(("%s=%s" % f) for f in data))

    # to access the fields in the record as they were regular attributes
    def __getattr__(self, key):
        if key in self.__class__.base_fields:
            return self.fields[key].get()
        raise AttributeError("The attribute with the name: %s does not exist" % key)
        
    def __setattr__(self, key, val):
        if key in self.base_fields:
            self.fields[key].set(val)
            return 
        object.__setattr__(self, key, val)
   