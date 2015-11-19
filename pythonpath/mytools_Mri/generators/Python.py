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
from mytools_Mri.unovalues import TypeClass
from mytools_Mri.cg import CGMode, CGType, log
from mytools_Mri.engine import Entry

class GeneratorForPython(GeneratorBase):
    
    NAME = "Python"
    PSEUD_PROPERTY = True
    
    INDENT = " " * 4
    
    OBJ_PREFIX = "obj%s"
    HEADER = 'def snippet(ctx, %s):'
    DOC_STRING = '"""  """'
    
    PREFIX_MAP = {
        'INTERFACE': 'o', 'SHORT': 'n', 'UNSIGNED_SHORT': 'n', 
        'LONG': 'n', 'UNSIGNED_LONG': 'n', 'HYPER': 'n', 
        'UNSIGNED_HYPER': 'n', 'FLOAT': 'n', 'TYPE': 'o', 
        'DOUBLE': 'n', 'BYTE': 'n', 'BOOLEAN': 'b', 
        'STRING': 's', 'CHAR': 's', 'SEQUENCE': 'o', 
        'STRUCT': 'a', 'ANY': 'o', 'VOID': '', 'ENUM': 'n'}
    
    def __init__(self, type_cast=False):
        GeneratorBase.__init__(self)
        self.pseud = False
        self.declarations = []
        self.variables = {}
        self.all_variables = set()
        self.lines = []
        self.exceptions = {}
        self.imported = set()
        
        self.counter = 0
        self.get_property_exceptions_added = False
        self.set_property_exceptions_added = False
        self.service_manager_registered = False
        
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
        
        if len(self.exceptions) > 0:
            body_indent = "%s%s" % (tab, indent)
            excepts = []
            aexcepts = excepts.append
            
            for e in self.exceptions.items():
                aexcepts('%sexcept %s as e:' % (indent, self.get_last_part(e[0]) ))
                aexcepts('%s# %s' % (indent *2, ', '.join(e[1])) )
                aexcepts('%sprint(e)' % (indent *2))
            
            return ''.join(
                ('\n'.join(self.declarations), '\n\n', 
                self.header, "\n", 
                "%s%s" % (indent, self.DOC_STRING), "\n", 
                '%stry:\n%s' % (indent, indent *2),
                    body_indent.join(self.lines), 
                '\n',
                '\n'.join(excepts),
                ))
        else:
            return "\n".join(('', 
                "\n".join(self.declarations), 
                "\n", 
                self.header,
                "%s%s" % (indent, self.DOC_STRING), 
                "%s%s" % (indent, tab.join(self.lines))
                ))
    
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
            if key in ("", "none", "current", "selection"):
                key = self.VAR_NAME
            self.variables[entry] = key
            self.header = self.HEADER % key
    
    def ad(self, line, breakable=True, _break=False):
        self.lines.append(line)
        if _break or (breakable and len(self.lines) % 4 == 3):
            self.lines.append("")
    
    def add_import(self, name, as_name=None):
        """Make import declaration."""
        if not name in self.imported:
            self.imported.add(name)
            suffix = self.get_last_part(name)
            prefix = name[0:-len(suffix)-1] # remove last dot
            if as_name:
            #   upper_chars = [c for c in suffix if c.isupper()]
                self.declarations.append("from %s import %s as %s" % (prefix, suffix, as_name))
            else:
                self.declarations.append('from %s import %s' % (prefix, suffix))
            self.declarations.sort()
    
    def add_exception(self, name, method_name):
        methods = self.exceptions.get(name, [])
        if not method_name in methods:
            methods.append(method_name)
        self.exceptions[name] = methods
        self.add_import(name)
    
    def register_variable(self, entry, var, type_class):
        self.variables[entry] = var
    
    def get_variable(self, entry):
        return self.variables[entry]
    
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
        if not name in self.all_variables:
            return name
        i = 2
        while '%s%s' % (name, i) in self.all_variables:
            i += 1
        return '%s%s' % (name, i)
    
    def add_variable(self, name):
        """Add to the variable list."""
        self.all_variables.add(name)
    
    # ToDo other values, sequence defined as a list to tuple
    def value_to_string(self, value, type_class, param_info=None):
        """Convert value to its string notation used in the code."""
        if isinstance(value, Entry):
            var = self.get_variable(value.code_entry)
            if isinstance(value.target, list):
                return "tuple(%s)" % var
            return var
        else:
            if type_class == TypeClass.STRING:
                return '"%s"' % value
            elif type_class == TypeClass.ENUM:
                name = value.typeName
                suffix = self.get_last_part(name)
                upper_chars = [c for c in suffix if c.isupper()]
                as_name = "%s_%s" % ("".join(upper_chars), value.value)
                self.add_import('%s.%s' % (value.typeName, value.value), as_name)
                #return value.value
                return as_name
            elif type_class == TypeClass.CHAR:
                return "uno.Char(\"%s\")" % value.value
            elif type_class == TypeClass.SEQUENCE:
                comp_type, n = self.parse_seq(param_info)
                _comp_type_class = comp_type.getTypeClass()
                str_val = [self.value_to_string(v, _comp_type_class) for v in value]
                return "(%s)" % ", ".join(str_val)
            else:
                return str(value)
    
    def add_method(self, entry):
        parent_var = self.get_variable(entry.parent)
        name = entry.key
        method = entry.idl
        vtype = entry.value_type
        param_infos = method.getParameterInfos()
        out_params = None
        if len(param_infos) == 0:
            rpart = "%s.%s()" % (parent_var, name)
        else:
            out_params = self.get_out_param_index(method)
            args = entry.args
            str_args = [self.value_to_string(arg, p.aType.getTypeClass(), p) for arg, p in zip(args, param_infos)]
            rpart = "%s.%s(%s)" % (parent_var, name, ', '.join(str_args))
        type_class = vtype.getTypeClass()
        type_name = vtype.getName()
        if type_class == TypeClass.VOID:
            var_name = ''
        elif (name.startswith('get') or name.startswith('set')) and not name.startswith('getBy'):
            var_name = self.make_variable(
                '%s%s' % (name[3].upper(), name[4:]), type_class)
        else:
            var_name = self.next_object()
        
        self.register_variable(entry, var_name, type_class)
        #self.add_variable(var_name)
        lpart = var_name
        if out_params:
            out_vars = [var_name]
            for out_param in out_params:
                #var = self.make_variable(
                var = self.next_object()
                self.add_variable(var)
                out_vars.append(var)
            lpart = ", ".join(out_vars)
        if lpart:
            self.ad('%s = %s' % (lpart, rpart))
        else:
            self.ad(rpart)
        
        exceptions = method.getExceptionTypes()
        if len(exceptions) > 0:
            for e in exceptions:
                self.add_exception(e.getName(), name)
    
    def add_pseud_property(self, entry):
        if self.pseud:
            self.add_prop(entry)
        else:
            self.add_method(entry)
    
    def add_prop(self, entry):
        if entry.type == CGType.PROP:
            key = entry.key
            vtype = entry.value_type
            type_class = vtype.getTypeClass()
            type_name = vtype.getName()
            if entry.mode & CGMode.GET:
                if not self.get_property_exceptions_added:
                    self.add_exception(
                        'com.sun.star.beans.UnknownPropertyException', 'getPropertyValue')
                    self.add_exception(
                        'com.sun.star.lang.WrappedTargetException', 'getPropertyValue')
                    self.get_property_exceptions_added = True
            else:
                if not self.set_property_exceptions_added:
                    self.add_exception(
                        'com.sun.star.beans.UnknownPropertyException', 'setPropertyValue')
                    self.add_exception(
                        'com.sun.star.lang.WrappedTargetException', 'setPropertyValue')
                    self.add_exception(
                        'com.sun.star.beans.PropertyVetoException', 'setPropertyValue')
                    self.add_exception(
                        'com.sun.star.lang.IllegalArgumentException', 'setPropertyValue')
                    self.set_property_exceptions_added = True
        else:
            key = entry.key
            if key.startswith('get') or key.startswith('set'):
                key = entry.key[3:]
                if key.startswith("get"):
                    entry.mode = CGMode.GET
                else:
                    entry.mode = CGMode.SET
                #var_name = self.make_variable(
                #'%s%s' % (name[3].upper(), name[4:]), type_class)
            else:
                key = entry.key
                #var_name = self.next_object()
            method = entry.idl
            ret_type = method.getReturnType()
            vtype = entry.value_type
            
            type_class = ret_type.getTypeClass()
            type_name = ret_type.getName()
        parent_var = self.get_variable(entry.parent)
        
        if entry.mode & CGMode.GET:
            var_name = self.make_variable(key, type_class)
            self.register_variable(entry, var_name, type_class)
            self.add_variable(var_name)
            self.ad("%s = %s.%s" % (var_name, parent_var, key))
        else:
            args = entry.args
            if entry.type != CGType.PROP:
                method = entry.idl
                pinfo = method.getParameterInfos()
                if len(pinfo) == 1:
                    vtype = pinfo[0].aType
            
            arg = self.value_to_string(args, vtype.getTypeClass(), vtype)
            self.ad("%s.%s = %s" % (parent_var, key, arg))
    
    def add_attr(self, entry):
        name = entry.key
        parent_var = self.get_variable(entry.parent)
        
        vtype = entry.value_type
        type_class = vtype.getTypeClass()
        type_name = vtype.getName()
        
        if entry.mode & CGMode.GET:
            var_name = self.make_variable(name, type_class)
            self.register_variable(entry, var_name, type_class)
            self.ad("%s = %s.%s" % (var_name, parent_var, name))
        else:
            rpart = self.value_to_string(entry.args, vtype.getTypeClass(), vtype)
            self.ad("%s.%s = %s" % (parent_var, name, rpart))
    
    # ToDo append
    def add_element(self, entry):
        parent = entry.parent
        parent_var = self.get_variable(parent)
        value_type = entry.value_type
        if entry.mode & CGMode.GET:
            type_name = value_type.getName()
            type_class = value_type.getTypeClass()
            name = self.get_last_part(type_name)
            var_name = self.make_variable(name, type_class)
            self.register_variable(entry, var_name, type_class)
            self.ad("%s = %s[%s]" % (var_name, parent_var, entry.key))
        else:
            str_value = self.value_to_string(entry.args, entry.value_type.getTypeClass(), value_type)
            if entry.misc:
                self.ad("%s.append(%s)" % (parent_var, str_value))
            else:
                self.ad("%s[%s] = %s" % (parent_var, entry.key, str_value))
    
    def add_field(self, entry):
        parent_idl = entry.idl
        name = entry.key
        
        parent_var = self.get_variable(entry.parent)
        field = parent_idl.getField(name)
        field_idl = field.getType()
        type_name = field_idl.getName()
        type_class = field_idl.getTypeClass()
        
        if entry.mode & CGMode.GET:
            var_name = self.make_variable(name, type_class)
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
        self.ad("%s = []" % var_name)
        self.register_variable(entry, var_name, type_class)
    
    def create_struct(self, entry):
        idl = entry.idl
        type_name = idl.getName()
        type_class = idl.getTypeClass()
        self.add_import(type_name)
        name = self.get_last_part(type_name)
        var_name = self.make_variable(name, type_class)
        self.register_variable(entry, var_name, type_class)
        if entry.args:
            param_infos = [info.getType() for info in idl.getFields()]
            str_args = [self.value_to_string(arg, param_info.getTypeClass(), param_info) 
                            for arg, param_info in zip(entry.args, param_infos)]
            self.ad("%s = %s(%s)" % (var_name, name, ", ".join(str_args)))
        else:
            self.ad("%s = %s()" % (var_name, name))
    
    def create_service(self, entry):
        idl = entry.idl
        type_class = idl.getTypeClass()
        if not self.service_manager_registered:
            self.ad("smgr = ctx.getServiceManager()")
            self.service_manager_registered = True
        name = entry.key
        var_name = self.make_variable(self.get_last_part(name), type_class)
        self.register_variable(entry, var_name, type_class)
        self.ad("%s = smgr.createInstanceWithContext(" % var_name, breakable=False)
        self.ad("%s%s, ctx)" % (self.INDENT, name))
    
    def get_component_context(self, entry):
        self.register_variable(entry, "ctx", entry.idl.getTypeClass())
    
    def _declare_variable(self, entry):
        idl = entry.idl
        _name = self.get_last_part(entry.key)
        var_name = self.make_variable(_name, idl.getTypeClass())
        self.register_variable(entry, var_name, idl.getTypeClass())
        value_str = self.value_to_string(entry.args, idl.getTypeClass(), idl)
        self.ad("%s = %s" % (var_name, value_str))

    