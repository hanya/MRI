#  Copyright 2011 Tsutomu Uchino
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import uno

from unovalues import TypeClass, TypeClassGroups
from engine import EntryBase


class ExtType2(uno.Type):
    """Extended type used normally for sequence."""
    def __init__(self, entry, engine, type_name='', type_class=None):
        if type_class != TypeClass.ANY and type_class != TypeClass.SEQUENCE:
            pass
        elif entry:
            ttype = engine.get_type(entry)
            type_name = ttype.getName()
            type_class = ttype.getTypeClass()
        
        self.typeName = type_name
        self.typeClass = type_class
        self.Name = type_name
        self.TypeClass = type_class
        if self.Name.startswith('[]'):
            # for simple type
            comp_type_class = TypeClassGroups.get_type_class(self.Name[2:])
            if not comp_type_class:
                # interface, struct, enum and ...
                comp_idl_class = engine.for_name(self.Name[2:])
                if comp_idl_class:
                    comp_type_class = comp_idl_class.getTypeClass()
            elif comp_type_class == TypeClass.ANY:
                if entry.target != None and len(entry.target) > 0:
                    comp_idl_class = engine.reflection.getType(entry.target[0])
            
            if entry and entry.target != None and isinstance(entry.target, tuple) and len(entry.target) > 0:
                elemental_entry = EntryBase(None, entry.target[0])
                self.ComponentType = ExtType2(elemental_entry, engine, self.Name[2:], comp_type_class)
            else:
                self.ComponentType = ExtType2(None, engine, self.Name[2:], comp_type_class)
        else:
            self.ComponentType = None
    
    def getName(self):
        return self.Name
    
    def getTypeClass(self):
        return self.TypeClass
    
    def getComponentType(self):
        return self.ComponentType
    
    def __repr__(self):
        return '%s %s' % (self.Name, self.TypeClass)


class ExtAnyType2(uno.Type):
    def __init__(self, entry, engine, type_name='', type_class=None):
        if engine.has_interface(entry.type, 'com.sun.star.reflection.XIdlClass'):
            pass
        elif entry:
            ttype = engine.get_type(entry)
            if ttype:
                type_name = ttype.getName()
                type_class = ttype.getTypeClass()
        
        if type_class == TypeClass.ANY and entry.target:
            vtype = engine.get_type(entry)
            type_name = vtype.getName()
            type_class = vtype.getTypeClass()
        
        self.typeName = type_name
        self.typeClass = type_class
        self.Name = type_name
        self.TypeClass = type_class
        
        if type_class == TypeClass.SEQUENCE:
            if hasattr(entry.type, 'getComponentType') and entry.type.getComponentType() and not entry.type.getComponentType().getTypeClass() == TypeClass.ANY:
                self.ComponentType = entry.type.getComponentType()
            elif entry.target != None and len(entry.target) > 0:
                comp_type = engine.reflection.getType(entry.target[0])
                elemental_entry = EntryBase(None, entry.target[0])
                try:
                    self.ComponentType = ExtAnyType2(elemental_entry, engine, comp_type.getName(), comp_type.getTypeClass())
                    self.typeName = "[]%s" % self.ComponentType.getName()
                    self.Name = self.typeName
                except Exception, e:
                    print(e)
            else:
                self.ComponentType = engine.for_name(type_name)
        else:
            self.ComponentType = None
    
    def getName(self):
        return self.Name
    
    def getTypeClass(self):
        return self.TypeClass
    
    def getComponentType(self):
        return self.ComponentType

    def __repr__(self):
        return "%s %s" % (self.Name, self.TypeClass)

