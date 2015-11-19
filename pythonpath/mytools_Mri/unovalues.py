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

class MethodConcept(object):
    from com.sun.star.beans.MethodConcept import ALL, PROPERTY

class PropertyConcept(object):
    from com.sun.star.beans.PropertyConcept import ALL, PROPERTYSET, ATTRIBUTES, METHODS

class FieldAccessMode(object):
    from com.sun.star.reflection.FieldAccessMode import READWRITE, READONLY, WRITEONLY
    
    modes = {READONLY.value: '[Read Only]', 
            #READWRITE.value: '[ReadWrite]', 
            READWRITE.value: '', 
            WRITEONLY.value: '[WriteOnly]'}

class ParamMode(object):
    from com.sun.star.reflection.ParamMode import IN, OUT, INOUT
    
    modes = {IN.value: '[in]', 
            OUT.value: '[out]', 
            INOUT.value: '[inout]'}

class PropertyAttribute(object):
    from com.sun.star.beans.PropertyAttribute import \
        MAYBEVOID, BOUND, CONSTRAINED, TRANSIENT, READONLY, \
        MAYBEAMBIGUOUS, MAYBEDEFAULT, REMOVEABLE, OPTIONAL
    
    modes = {MAYBEVOID: 'Maybevoid', 
            BOUND: 'Bound', 
            CONSTRAINED: 'Constrained', 
            TRANSIENT: 'Transient', 
            READONLY: 'Read_Only', 
            MAYBEAMBIGUOUS: 'Maybeambiguous', 
            MAYBEDEFAULT: 'Maybedefault', 
            REMOVEABLE: 'Removeable', 
            OPTIONAL: 'Optional'}

class TypeClass(object):
    from com.sun.star.uno.TypeClass import \
        SEQUENCE, ARRAY, VOID, BYTE, SHORT, UNSIGNED_SHORT, \
        LONG, UNSIGNED_LONG, HYPER, UNSIGNED_HYPER, FLOAT, \
        DOUBLE, BOOLEAN, CHAR, STRING, STRUCT, INTERFACE, \
        TYPE, ANY, ENUM, EXCEPTION

class TypeClassGroups(object):
    INT = [TypeClass.SHORT, TypeClass.UNSIGNED_SHORT, 
        TypeClass.LONG, TypeClass.UNSIGNED_LONG, 
        TypeClass.HYPER, TypeClass.UNSIGNED_HYPER]
    FLOATING = [TypeClass.FLOAT, TypeClass.DOUBLE]
    NUMERIC = INT + FLOATING
    STR = TypeClass.STRING
    SEQ = [TypeClass.SEQUENCE, TypeClass.ARRAY]
    OBJECT = TypeClass.INTERFACE
    STRUCTS = (TypeClass.STRUCT, TypeClass.EXCEPTION)
    
    COMPATIBLE = NUMERIC + [
        TypeClass.STRING, TypeClass.BOOLEAN, TypeClass.ENUM, 
        TypeClass.INTERFACE, TypeClass.STRUCT, TypeClass.TYPE]
    
    ALL = {getattr(TypeClass, k).value: getattr(TypeClass, k) 
            for k in dir(TypeClass) if hasattr(getattr(TypeClass, k), 'value')}
    
    @classmethod
    def get_type_class(cls, type_name):
        return cls.ALL.get(type_name.upper(), None)

