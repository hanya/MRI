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

import traceback
from mytools_Mri.generators import GeneratorBase
from mytools_Mri.unovalues import TypeClass, ParamMode
from mytools_Mri.cg import CGMode, CGType, log
from mytools_Mri.engine import Entry

class GeneratorForBasic(GeneratorBase):
    
    NAME = "OpenOffice.org Basic"
    PSEUD_PROPERTY = True
    
    INDENT = "  "
    
    OBJ_PREFIX = "oObj%s"
    THISCOMPONENT = "ThisComponent"
    HEADER = "Sub Snippet(Optional %s As Object)"
    HEADER_2 = "Sub Snippet"
    FOOTER = "End Sub"
    
    TYPE_MAP = {
        'INTERFACE': 'Variant', 'SHORT': 'Integer', 'UNSIGNED_SHORT': 'Integer', 
        'LONG': 'Long', 'UNSIGNED_LONG': 'Long', 'HYPER': 'Long', 
        'UNSIGNED_HYPER': 'Long', 'FLOAT': 'Single', 'TYPE': 'Variant', 
        'DOUBLE': 'Double', 'BYTE': 'Integer', 'BOOLEAN': 'Boolean', 
        'STRING': 'String', 'CHAR': 'String', 'SEQUENCE': 'Variant', 
        'ANY': 'Variant', 'ENUM': 'Long' }
        
    PREFIX_MAP = {
        'INTERFACE': 'o', 'SHORT': 'n', 'UNSIGNED_SHORT': 'n', 
        'LONG': 'n', 'UNSIGNED_LONG': 'n', 'HYPER': 'n', 
        'UNSIGNED_HYPER': 'n', 'FLOAT': 'n', 'TYPE': 'o', 
        'DOUBLE': 'n', 'BYTE': 'n', 'BOOLEAN': 'b', 
        'STRING': 's', 'CHAR': 's', 'SEQUENCE': 'o', 
        'STRUCT': 'a', 'ANY': 'o', 'VOID': '', 'ENUM': 'n'}
    
    REGISTERED_TYPE_CLASSES = (TypeClass.INTERFACE, TypeClass.SEQUENCE, 
            TypeClass.STRUCT, TypeClass.ANY)
    
    def __init__(self):
        GeneratorBase.__init__(self)
        self.pseud = False
        self.declarations = []
        self.lines = []
        self.declared = set()
        self.variables = {}
        
        self.current_component = False
        
        self.items = {
            CGType.METHOD: self.add_method, CGType.PROP: self.add_prop, 
            CGType.ATTR: self.add_attr, CGType.FIELD: self.add_field, 
            CGType.ELEMENT: self.add_element, 
            CGType.STRUCT: self.create_struct, CGType.SEQ: self.create_seq, CGType.PSEUD_PROP: self.add_pseud_property, 
            CGType.SERVICE: self.create_service, CGType.CONTEXT: self.get_component_context, CGType.VARIABLE: self._declare_variable
        }
    
    def get(self):
        indent = self.INDENT
        tab = "\n%s" % indent
        return "\n".join((self.header, 
            "%s%s" % (indent, tab.join(self.declarations)), 
            '',
            "%s%s" % (indent, tab.join(self.lines)), 
            self.FOOTER))
    
    def add(self, entry):
        func = self.items.get(entry.type, None)
        if func:
            try:
                func(entry)
            except Exception as e:
                print(("Error on cg#add: " + str(e)))
                traceback.print_exc()
        elif entry.type == CGType.NONE:
            key = entry.key
            value_type = entry.value_type
            if key == "current":
                self.register_variable(entry, self.THISCOMPONENT, value_type.getTypeClass())
                self.header = self.HEADER_2
            else:
                if key in ("", "none", "current", "selection"):
                    key = self.VAR_NAME
                self.register_variable(entry, key, value_type.getTypeClass())
                self.header = self.HEADER % key
    
    def ad(self, line, breakable=True, _break=False):
        self.lines.append(line)
        if _break or (breakable and len(self.lines) % 4 == 3):
            self.lines.append("")
    
    def register_variable(self, entry, var, type_class):
        #if type_class in self.registered_type_classes:
        self.variables[entry] = var
    
    def get_variable(self, entry):
        return self.variables[entry]
    
    def declare_variable(self, name, type_name, type_class, items=-1):
        """Declare variable."""
        if type_class == TypeClass.VOID: return # ignore void
        if name in self.declared: return
        
        self.declared.add(name)
        if type_class == TypeClass.STRUCT:
            if items == -1:
                declaration = "Dim %s As New %s" % (name, type_name)
            else:
                declaration = "Dim %s(%s) As New %s" % (name, items, type_name)
        else:
            d = self.TYPE_MAP.get(type_class.value, '')
            if items == -1:
                declaration = "Dim %s As %s" % (name, d)
            else:
                declaration = "Dim %s(%s) As %s" % (name, items, d)
        self.declarations.append(declaration)
    
    def make_variable(self, name, type_class):
        """Adds prefix."""
        p = self.PREFIX_MAP.get(type_class.value, '')
        if p:
            name = name.strip("[]")
            return self._make_identical("%s%s" % (p, name))
        else:
            return ""
    
    def _make_identical(self, name):
        """Modify the variable name identical."""
        if not name in self.declared:
            return name
        i = 2
        while '%s%s' % (name, i) in self.declared:
            i += 1
        return '%s%s' % (name, i)
    
    def value_to_string(self, value, type_class, param_info=None):
        """Convert value to its string notation used in the code."""
        if isinstance(value, Entry):
            var = self.get_variable(value.code_entry)
            return var
        else:
            # ToDo TYPE, CHAR
            if type_class == TypeClass.STRING:
                return '"%s"' % value
            elif type_class == TypeClass.ENUM:
                return '%s.%s' % (value.typeName, value.value)
            elif type_class == TypeClass.SEQUENCE:
                comp_type, n = self.parse_seq(param_info)
                _comp_type_class = comp_type.getTypeClass()
                str_val = [self.value_to_string(v, _comp_type_class) for v in value]
                return "Array(%s)" % ", ".join(str_val)
            elif type_class == TypeClass.VOID:
                return "Null"
            else:
                if value is None:
                    return "Null"
                return str(value)
    
    def add_method(self, entry):
        method = entry.idl
        name = method.getName()
        
        parent_var = self.get_variable(entry.parent)
        vtype = entry.value_type
        
        param_infos = method.getParameterInfos()
        if len(param_infos) == 0:
            rpart = '%s.%s()' % (parent_var, name)
        else:
            args = entry.args
            str_args = [self.value_to_string(a, p.aType.getTypeClass(), p) for a, p in zip(args, param_infos)]
            rpart = '%s.%s(%s)' % (parent_var, name, ', '.join(str_args))
        
        type_class = vtype.getTypeClass()
        type_name = vtype.getName()
        if type_class == TypeClass.VOID:
            var_name = ''
        elif (name.startswith('get') or \
            name.startswith('set')) and \
            not name.startswith('getBy'):
            var_name = self.make_variable(
                '%s%s' % (name[3].upper(), name[4:]), type_class)
        else:
            var_name = self.next_object()
        
        self.register_variable(entry, var_name, type_class)
        self.declare_variable(var_name, type_name, type_class)
        
        lpart = var_name
        if lpart:
            self.ad('%s = %s' % (lpart, rpart))
        else:
            self.ad(rpart)
    
    def add_pseud_property(self, entry):
        if self.pseud:
            self.add_prop(entry)
        else:
            self.add_method(entry)
    
    def add_prop(self, entry):
        #log("ap %s, %s, %s" % (entry.key, entry.type, entry.mode))
        name = entry.key
        if entry.type == CGType.PROP:
            key = name
            ret_type = entry.value_type
        else:
            if name.startswith('get') or name.startswith('set'):
                key = name[3:]
                if name.startswith("get"):
                    entry.mode = CGMode.GET
                else:
                    entry.mode = CGMode.SET
            else:
                key = name
            method = entry.idl
            ret_type = method.getReturnType()
        type_name = ret_type.getName()
        type_class = ret_type.getTypeClass()
        parent_var = self.get_variable(entry.parent)
        
        if entry.mode & CGMode.GET:
            var_name = self.make_variable(key, type_class)
            self.declare_variable(var_name, type_name, type_class)
            self.register_variable(entry, var_name, type_class)
            self.ad("%s = %s.%s" % (var_name, parent_var, key))
        else:
            args = entry.args
            if entry.type != CGType.PROP:
                pinfo = method.getParameterInfos()
                if len(pinfo) == 1:
                    ret_type = pinfo[0].aType
            arg = self.value_to_string(args, ret_type.getTypeClass(), ret_type)
            self.ad("%s.%s = %s" % (parent_var, key, arg))
    
    def add_attr(self, entry):
        name = entry.key
        parent_var = self.get_variable(entry.parent)
        
        vtype = entry.value_type
        type_class = vtype.getTypeClass()
        type_name = vtype.getName()
        
        if entry.mode & CGMode.GET:
            var_name = self.make_variable(name, type_class)
            self.declare_variable(var_name, type_name, type_class)
            self.register_variable(entry, var_name, type_class)
            self.ad("%s = %s.%s" % (var_name, parent_var, name))
        else:
            rpart = self.value_to_string(entry.args, vtype.getTypeClass(), vtype)
            self.ad("%s.%s = %s" % (parent_var, name, rpart))
    
    def add_element(self, entry):
        parent = entry.parent
        parent_var = self.get_variable(parent)
        value_type = entry.value_type
        if entry.mode & CGMode.GET:
            type_name = value_type.getName()
            type_class = value_type.getTypeClass()
            name = self.get_last_part(type_name)
            var_name = self.make_variable(name, type_class)
            self.declare_variable(var_name, type_name, type_class)
            self.register_variable(entry, var_name, type_class)
            self.ad("%s = %s(%s)" % (var_name, parent_var, entry.key))
        else:
            str_val = self.value_to_string(entry.args, entry.value_type.getTypeClass(), value_type)
            self.ad("%s(%s) = %s" % (parent_var, entry.key, str_val))
    
    def add_field(self, entry):
        parent_idl = entry.idl#entry.parent.idl
        name = entry.key
        
        parent_var = self.get_variable(entry.parent)
        field = parent_idl.getField(name)
        field_idl = field.getType()
        type_name = field_idl.getName()
        type_class = field_idl.getTypeClass()
        
        if entry.mode & CGMode.GET:
            var_name = self.make_variable(name, type_class)
            self.declare_variable(var_name, type_name, type_class)
            self.register_variable(entry, var_name, type_class)
            self.ad("%s = %s.%s" % (var_name, parent_var, name))
        else:
            value_str = self.value_to_string(entry.args, type_class, field_idl)
            self.ad("%s.%s = %s" % (parent_var, name, value_str))
    
    def create_seq(self, entry):
        idl = entry.idl
        comp_type, dimension = self.parse_seq(idl)
        type_name = comp_type.getName()
        type_class = comp_type.getTypeClass()
        name = self.get_last_part(type_name)
        var_name = self.make_variable(name, type_class)
        self.declare_variable(var_name, type_name, type_class, entry.args)
        self.register_variable(entry, var_name, type_class)
    
    def create_struct(self, entry):
        idl = entry.idl
        type_class = idl.getTypeClass()
        type_name = idl.getName()
        name = self.get_last_part(type_name)
        var_name = self.make_variable(name, type_class)
        # declared by Dim
        #self.ad("%s = CreateUnoStruct(\"%s\")" % (var_name, type_name))
        if entry.args:
            self.ad("With %s" % var_name)
            for arg, info in zip(entry.args, idl.getFields()):
                _idl = info.getType()
                str_arg = self.value_to_string(arg, _idl.getTypeClass(), _idl)
                self.ad("%s.%s = %s" % (self.INDENT, name, str_arg))
            self.ad("End With")
        self.declare_variable(var_name, type_name, type_class)
        self.register_variable(entry, var_name, type_class)
    
    def create_service(self, entry):
        idl = entry.idl
        type_class = idl.getTypeClass()
        service_name = entry.key
        _name = self.get_last_part(service_name)
        var_name = self.make_variable(_name, type_class)
        self.ad("%s = CreateUnoService(\"%s\")" % (var_name, service_name))
        self.declare_variable(var_name, idl.getName(), type_class)
        self.register_variable(entry, var_name, type_class)
    
    def get_component_context(self, entry):
        idl = entry.idl
        type_class = idl.getTypeClass()
        _name = self.get_last_part(entry.key)
        var_name = self.make_variable(_name, type_class)
        self.ad("%s = GetDefaultContext()" % var_name)
        self.declare_variable(var_name, idl.getName(), type_class)
        self.register_variable(entry, var_name, type_class)
    
    def _declare_variable(self, entry):
        idl = entry.idl
        _name = self.get_last_part(entry.key)
        var_name = self.make_variable(_name, idl.getTypeClass())
        self.register_variable(entry, var_name, idl.getTypeClass())
        value_str = self.value_to_string(entry.args, idl.getTypeClass(), idl)
        self.ad("%s = %s" % (var_name, value_str))

    