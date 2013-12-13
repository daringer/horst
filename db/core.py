#!/usr/bin/python
#-*- coding: utf-8 -*-

import sqlite3 as sqlite
from threading import Lock

__metaclass__ = type

class DatabaseError(Exception):
    pass

class Database(object):
    """Low-Level Object-Based Database Interface"""
    lock = Lock()
    contributed_records = []
    query_counter = 0
    
    def __init__(self, dbfile="horst.sqlite"):
        self.dbfile = dbfile

    def contribute(self, cls):
        """Every Record has to "register" here"""
        
        # handle relation fields
        from fields import ManyToOneRelation, OneToManyRelation
        for name, field in cls.base_fields.items():
            if isinstance(field, OneToManyRelation):
                field.related_record.setup_field(cls.table, ManyToOneRelation(cls))
            elif isinstance(field, ManyToOneRelation):
                field.related_record.setup_field(cls.table, OneToManyRelation(cls))                                         
        self.contributed_records += [cls]

    # FIXME: _really_ check the tables, means including fields, 
    # TODO: do some smart database updater if db-structure does not match Records
    def check_for_tables(self):
        """Check for all 'cls', if we need to create the needed table"""
        
        for rec in self.contributed_records:             
            # there is no 'show tables' sql-statement in sqlite so query sqlite_master
            q = "SELECT * FROM sqlite_master WHERE type='table' AND tbl_name='%s'" % rec.table
            res = self.query(q)

            if len(res) == 1:
                continue

            # here we haven't found the table
            q = "CREATE TABLE %s (%s)" % (rec.table, ", ".join(x.get_create() for x in rec.base_fields.values() if x.colname))
            self.query(q)
       
    def query(self, q, args=()):
        """Actually performing a query. Replace variables in 'q' with "?" and
           pass the variables in the second argument 'args' as tupel"""
        
        #print "query: %s with args %s" % (q, args)
        self.query_counter += 1
               
        with self.lock:
            self.connection = sqlite.connect(self.dbfile)
            # to return a dict for each row
            self.connection.row_factory = sqlite.Row
            # to auto-commit
            self.connection.isolation_level = None
            
            self.cursor = self.connection.cursor()
            self.cursor.execute(q, args)
            self.lastrowid = self.cursor.lastrowid

            out = self.cursor.fetchall() if q.lower().startswith("select") else True
            
        return out
           
    def save_obj(self, obj):
        """Either insert the object if "rowid" is found in table,
           or update if rowid if found in the table"""
        
        # does it already exist ?
        q = "SELECT rowid FROM %s WHERE rowid=?" % obj.table
        act = "update" if obj.rowid and self.query(q, (obj.rowid,)) else "insert"
        
        # prepare all fields to be saved using Field::pre_save()
        for attr in obj.fields:
            if not obj.fields[attr].pre_save(action=act, obj=obj):
                raise DatabaseError("Field::pre_save() for field '%s' with value '%s' failed" % (attr, getattr(obj, attr)))
     
        # collect data - virtual fields (and empty fields) will be ignored, as they don't have a sqlite_name
        attr_vals = [{"col":v.colname, "val":v.get()} for k, v in obj.fields.items() if v.colname and v.get() is not None]
        
        # replace BaseRecord descendants with their .rowid 
        from baserecord import BaseRecord
        for i in range(len(attr_vals)):
            if issubclass(attr_vals[i]["val"].__class__, BaseRecord):
                attr_vals[i]["val"] = attr_vals[i]["val"].rowid
        
        # construct the sql query              
        if act == "update":
            fields = ", ".join("%s=?" % x["col"] for x in attr_vals)
            q = "UPDATE %s SET %s WHERE rowid=%s" % (obj.table, fields, obj.rowid)      
        elif act == "insert":
            fields = ",".join(x["col"] for x in attr_vals)
            vals = ",".join(["?"]*len(attr_vals))
            q = "INSERT INTO %s (%s) VALUES (%s)" % (obj.table, fields, vals)
        
        ret = self.query(q, [x["val"] for x in attr_vals])    
        
        # postprocess fields using Field::post_save()
        for attr in obj.fields:
            if not obj.fields[attr].post_save(action=act, obj=obj):
                raise DatabaseError("Field::post_save() for field '%s' with value '%s' failed" % (attr, getattr(obj, attr)))
     
        return ret
            
    def delete_obj(self, obj):
        """Delete given object from the database"""
        q = "DELETE FROM %s WHERE rowid=?" % obj.table
        return self.query(q, (obj.rowid,))
        
    def filter(self, cls, operator="=", limit=None, order_by=None, **kw):
        """Return instances of 'cls' according to given values in 'kw' from
           the database"""
       
        # check if the passed keywords exist as field
        all_fields = cls.base_fields.keys() + ["rowid"]
        if any(not k in all_fields for k in kw):
            raise DatabaseError("filter got a non field keyword (one of: %s), instead of one of: '%s'" % (kw.keys(), ", ".join(all_fields)))
         
        # postprocess the query keywords
        from fields import ManyToOneRelation
        from baserecord import BaseRecord
        for k, v in kw.items():
            # append "_id" to key and replace value with rowid if the field is a ManyToOneRelation
            if k in cls.base_fields and isinstance(cls.base_fields[k], ManyToOneRelation):
                del kw[k]
                kw[k + "_id"] = v.rowid if v else None
              
        if kw:
            # uhu ugly-magic, actually just replacing the operator with "IS NULL" if the kw value is None
            where = " AND ".join("%s%s" % (k, (operator+"?" if v is not None else " IS NULL")) for k, v in kw.items())
            
            q = "SELECT rowid, * FROM %s WHERE %s" % (cls.table, where)
        else:
            q = "SELECT rowid, * FROM %s" % (cls.table)    
        
        if order_by:
            if any(not x.strip("+-") in all_fields for x in order_by):
                raise DatabaseError("order by contains non field keys: %s, availible are only: %s" % \
                    (", ".join(order_by), ", ".join(all_fields)))
        
            q += " ORDER BY %s" % ", ".join("%s%s" % (x[0], " DESC" if x[1].startswith("-") else "") for x in order_by)
        
        if limit:
            q += " LIMIT %s,%s" % limit
        
        vals = [x for x in kw.values() if x is not None] if kw else []      
        return [cls(**kw) for kw in self.query(q, vals)]
    
    def exclude(self, cls, **kw):
        """Return instances which DON'T match the 
           keyword -> value combination from kw"""
        return self.filter(cls, operator="<>", **kw)
    


class DataManager(object):
    """Object managing class placed as AnyRecord.objects"""
    def __init__(self, rec, pre_filter={}, order_by=None, limit=None):
        self.record = rec
        self.pre_filter = pre_filter
        # order_by must be a tuple of fieldnames with a leading "+" or "-", no operator implies "+"
        self.order_by = order_by
        # limit must be a tuple of 2 elements
        self.limit = limit

    def __repr__(self):
        return "<%s DataManager>" % self.record.__name__

    def __getitem__(self, key):
        """Behave like a list of objects, 'key' is a non-database-related up counting index"""
        return self.record.database.filter(self.record, limit=(key,1))[0]
        
    def all(self):
        """Return all Record objects from the database"""
        return self.record.database.filter(self.record)

    def filter(self, **kw):
        """This is the access method to all rows aka objects from the database.
           use like this: 
           MyRecord.objects.filter(some_field="bar", other_field="foo")
           """
        kw.update(self.pre_filter)
        return self.record.database.filter(self.record, **kw)

    def get(self, **kw):
        """Returns exactly one object if found or None. 
           raises an DatabaseError if more than one is found"""
        ret = self.filter(**kw)
        if len(ret) == 1:
            return ret[0]
        elif len(ret) > 1:
            raise DatabaseError("Got more than one row from: %s" % kw)
        else:
            return None

    def exclude(self, **kw):
        """Exclude the objects with match the keyword -> value combination passed"""
        return self.record.database.exclude(self.record, **kw)

    def create_or_get(self, **kw):
        """'kw' requires at least one table-unique column/keyword.
           returns the found object if it is found, or
           returns a fresh created (and saved) object with given data"""
        
        # if no unique keyword is given, raise exception
        if not any(self.record.base_fields[k].unique for k in kw if k in self.record.base_fields):
            raise DatabaseError("The keyword-dict does not contain a unique key")
        
        # get unique keywords and use them to self.objects.get() an object  
        unique_kw = dict((k, v) for k,v in kw.items() if k in self.record.base_fields and self.record.base_fields[k].unique)
        
        # create or get data-object for unique_fields
        u = self.record.objects.get(**unique_kw)
        if not u:
            u = self.record(**kw)
            u.save()

        return u



