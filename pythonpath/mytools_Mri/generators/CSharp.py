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

class GeneratorForCSharp(GeneratorBase):
    
    NAME = "C# CLI"
    PSEUD_PROPERTY = False
    
    INDENT = "\t" * 1
    
    OBJ_PREFIX = "oObj%s"
    COMPONENT_CONTEXT_VAR = "xContext"
    #HEADER = "public class Snippet {\n" + \
    #   "public void snippet(%s)\n{"
    HEADER = "public class Snippet {\n" + \
            "public void snippet(XComponentContext %s, %%s)\n{" % COMPONENT_CONTEXT_VAR
    FOOTER = "}\n}"
    
    
    TYPE_CLASS_MAP2 = {
        'INTERFACE': '', 'SHORT': 'Int16', 'UNSIGNED_SHORT': 'UInt16', 
        'LONG': 'Int32', 'UNSIGNED_LONG': 'UInt32', 'HYPER': 'Int64', 
        'UNSIGNED_HYPER': 'UInt64', 'FLOAT': 'Single', 'TYPE': 'Type', 
        'DOUBLE': 'Double', 'BYTE': 'Byte', 'BOOLEAN': 'Boolean', 
        'STRING': 'String', 'CHAR': 'Char', 'SEQUENCE': '', 
        'ANY': 'uno.Any', 'ENUM': 'Enum', 'STRUCT': '', 'Void': 'void'}
    TYPE_CLASS_MAP = {
        'INTERFACE': '', 'SHORT': 'short', 'UNSIGNED_SHORT': 'ushort', 
        'LONG': 'int', 'UNSIGNED_LONG': 'uint', 'HYPER': 'long', 
        'UNSIGNED_HYPER': 'ulong', 'FLOAT': 'float', 'TYPE': 'Type', 
        'DOUBLE': 'double', 'BYTE': 'byte', 'BOOLEAN': 'bool', 
        'STRING': 'String', 'CHAR': 'char', 'SEQUENCE': '', 
        'ANY': 'uno.Any', 'ENUM': 'Enum', 'STRUCT': '', 'Void': 'void'}
    
    PREFIX_MAP = {
        'INTERFACE': 'x', 'SHORT': 'n', 'UNSIGNED_SHORT': 'n',
        'LONG': 'n', 'UNSIGNED_LONG': 'n', 'HYPER': 'n',
        'UNSIGNED_HYPER': 'n', 'FLOAT': 'f', 'TYPE': 't',
        'DOUBLE': 'f', 'BYTE': 'n', 'BOOLEAN': 'b',
        'STRING': 's', 'CHAR': 'c', 'SEQUENCE': '',
        'ANY': 'o', 'STRUCT': 'a', 'ENUM': 'n'}
    
    def __init__(self, type_cast=False):
        GeneratorBase.__init__(self)
        
        self.lines = []
        #self.imported = set()
        self.variables = {}
        self.all_variables = set()
        self.namespace = set()
        self.exceptions = {}
        
        self.items = {
            CGType.METHOD: self.add_method, CGType.PROP: self.add_prop, 
            CGType.ATTR: self.add_attr, CGType.FIELD: self.add_field, 
            CGType.ELEMENT: self.add_element, 
            CGType.STRUCT: self.create_struct, CGType.SEQ: self.create_seq, CGType.PSEUD_PROP: self.add_method, 
            CGType.SERVICE: self.create_service, CGType.CONTEXT: self.get_component_context, CGType.VARIABLE: self.declare_variable
        }
        
        #self.propertyset_imported = False
        self.get_property_exceptions_added = False
        self.set_property_exceptions_added = False
        self.mcf_declared = False
        
        self.add_namespace('System', unoidl=False)
        self.add_namespace('com.sun.star.uno')
    
    def get(self):
        namespaces = ["using %s;" % i for i in self.namespace]
        namespaces.sort()
        
        if len(self.exceptions) > 0:
            indent = self.INDENT
            indent_1 = '\n%s' % indent
            body_indent = '\n%s' % (indent * 2)
            
            catched = []
            for e in self.exceptions.items():
                catched.append('catch (%s e)' % self.get_last_part(e[0]))
                catched.append('{')
                catched.append('%s// %s' % (indent, ', '.join(e[1])) )
                catched.append('%sConsole.WriteLine(e.Message);' % indent)
                catched.append('}')
            
            return "\n".join((
                "\n".join(namespaces), '', 
                self.header, 
                "%stry\n%s{" % (indent, indent), 
                "%s%s" % (indent * 2, body_indent.join(self.lines)), 
                "%s}" % indent, 
                "%s%s" % (indent, indent_1.join(catched)), 
                self.FOOTER))
        else:
            tab = "\n%s" % self.INDENT
            return "\n".join((
                "\n".join(namespaces), '', 
                self.header, 
                "%s%s" % (self.INDENT, tab.join(self.lines)), 
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
            key_word = entry.key
            if key_word in ("", "none", "current", "selection"):
                key_word = self.VAR_NAME
            value_type = entry.value_type
            self.register_variable(entry, key_word, value_type.getTypeClass(), value_type.getName())
            type_class = value_type.getTypeClass()
            type_name = value_type.getName()
            args = ''
            if type_class == TypeClass.INTERFACE:
                args = "%s %s" % ('object', key_word)
            elif type_class == TypeClass.STRUCT:
                #self.add_import(type_name)
                args = "%s %s" % (self.get_last_part(type_name), key_word)
            elif type_class == TypeClass.ANY:
                #self.add_import('com.sun.star.uno.Any', kind='hxx')
                args = "uno.Any %s" % (key_word)
            elif type_class == TypeClass.SEQUENCE:
                content = "%s" % ""
                args = "%s[]" % content
            else:
                args = "uno.Any %s" % (key_word)
            self.header = self.HEADER % args
    
    def ad(self, line, breakable=True, _break=False):
        self.lines.append(line)
        if _break or (breakable and len(self.lines) % 4 == 3):
            self.lines.append("")
    
    def add_namespace(self, name, split=False, unoidl=True):
        if split:
            name = name[0:name.rfind('.')]
        name = name.strip('[]')
        if unoidl:
            rname = 'unoidl.' + name
        else:
            rname = name
        #rname = ('unoidl.' if unoidl else '') + name
        if not rname in self.namespace:
            self.namespace.add(rname)
    
    def add_exception(self, name, method_name):
        methods = self.exceptions.get(name, [])
        if not method_name in methods:
            methods.append(method_name)
        self.exceptions[name] = methods
        self.add_namespace(name[0:name.rfind('.')])
    
    def register_variable(self, entry, name, type_class, type_name):
        """name: variable_name, type_name: name of the type
        XPropertySet: variable name of the XPropertySet interface
        interfaces: queried interfaces
        interface name: variable name
        """
        #if type_class in self.registered_type_classes:
        interfaces = {}
        if type_class == TypeClass.INTERFACE:
            interfaces[type_name] = name
        self.variables[entry] = {'name': name, 'type_name': type_name, 
                'XPropertySet': "", 'interfaces': interfaces}
    
    def get_variable(self, entry):
        return self.variables[entry]
    
    def update_variable(self, index, v):
        """update the type of the variable."""
        self.variables[index] = v
    
    def make_identical(self, name):
        """Modify the variable name identical."""
        if not name in self.all_variables:
            return name
        i = 2
        while '%s_%s' % (name, i) in self.all_variables:
            i += 1
        return '%s_%s' % (name, i)
    
    def add_variable(self, name):
        if not name in self.all_variables:
            # Set
            self.all_variables.add(name)
    
    def make_variable(self, name, idl_class):
        """Make variable name and get type name."""
        var_name, var_type = self._make_variable(name, idl_class)
        
        vname = self.make_identical(var_name)
        self.add_variable(vname)
        return vname, var_type
    
    def _make_variable(self, name, idl_class):
        """Make a variable name from XIdlClass."""
        seq = False
        name = name.strip("[]")
        type_class = idl_class.getTypeClass()
        type_name = idl_class.getName()
        
        if type_class == TypeClass.SEQUENCE:
            cmp_idl_class = idl_class.getComponentType()
            cmp_type_class = cmp_idl_class.getTypeClass()
            
            if cmp_type_class == TypeClass.SEQUENCE:
                name, vtype = self._make_variable(name, cmp_idl_class)
                return name, "%s[]" % vtype
            else:
                type_class = cmp_type_class
                seq = True
        if type_class == TypeClass.INTERFACE:
            if type_name == 'com.sun.star.uno.XInterface':
                vname = self.next_object()
                suffix = "object"
            else:
                suffix = self.get_last_part(type_name)
                vname = '%s%s' % (self.PREFIX_MAP.get(type_class.value, ""), suffix[1:])
            vtype = suffix
        elif type_class in (TypeClass.STRUCT, TypeClass.ENUM):
            #typeName = idlclass.getName()
            suffix = self.get_last_part(type_name)
            vname = '%s%s' % (self.PREFIX_MAP.get(type_class.value, ""), suffix)
            vtype = suffix
        else:
            vname = '%s%s' % (self.PREFIX_MAP.get(type_class.value, ""), name)
            vtype = self.TYPE_CLASS_MAP.get(type_class.value, "")
        
        if seq:
            return (vname, "%s[]" % vtype)
        else:
            return vname, vtype
    
    def any_conv(self, obj, type_class, vtype):
        if type_class == TypeClass.INTERFACE:
            self.add_namespace(vtype, split=True)
            name = self.get_last_part(vtype)
            return '(%s) %s.Value' % (name, obj)
        elif type_class in (TypeClass.STRUCT, TypeClass.ENUM, TypeClass.SEQUENCE):
            if type_class == TypeClass.SEQUENCE:
                name = self.get_last_part(vtype).strip("[]") + ("[]" * vtype.count("[]"))
                # needs more info for component of the sequence
                if self.TYPE_CLASS_MAP.get(vtype.strip("[]").upper(), '') == '':
                    self.add_namespace(vtype, split=True)
            else:
                self.add_namespace(vtype, split=True)
                name = self.get_last_part(vtype)
            return '(%s) %s.Value' % (name, obj)
        elif type_class == TypeClass.ANY:
            return obj
        else:
            value_type = self.TYPE_CLASS_MAP[type_class.value]
            return '(%s) %s.Value' % (value_type, obj)
    
    # ToDo Any
    def value_to_string(self, value, type_class, param_info=None):
        """Convert value to its string notation used in the code."""
        if isinstance(value, Entry):
            var = self.get_variable(value.code_entry)
            if type_class == TypeClass.INTERFACE:
                type_name = param_info.getName()
                var_name = var["interfaces"].get(type_name, None)
                if var_name is None:
                    self.add_namespace(type_name)
                    _type_name = self.get_last_part(type_name)
                    return "(%s)%s" % (_type_name, var["name"])
                else:
                    return var_name
            return var["name"]
        else:
            if type_class == TypeClass.STRING:
                return '"%s"' % value
            elif type_class == TypeClass.BOOLEAN:
                return str(value).lower()
            elif type_class == TypeClass.ENUM:
                return 'unoidl.%s.%s' % (value.typeName, value.value)
            elif type_class == TypeClass.SEQUENCE:
                comp_type, n = self.parse_seq(param_info)
                _comp_type_class = comp_type.getTypeClass()
                _comp_type = self.TYPE_CLASS_MAP.get(_comp_type_class.value)
                str_val = [self.value_to_string(v, _comp_type_class) for v in value]
                return "new %s%s{%s}" % (comp_type.getName(), "[]" * n, ", ".join(str_val))
            elif type_class == TypeClass.INTERFACE:
                return "null" # ToDo
            else:
                if type_class in (TypeClass.BYTE, TypeClass.SHORT, TypeClass.UNSIGNED_SHORT, TypeClass.UNSIGNED_LONG, TypeClass.HYPER, TypeClass.UNSIGNED_HYPER, TypeClass.DOUBLE):
                    type_name = self.TYPE_CLASS_MAP[type_class.value]
                    return '(%s) %s' % (type_name, str(value))
                else:
                    return str(value)
    
    def to_any(self, obj, type_class, type_name=None):
        var = None
        if isinstance(obj, Entry):
            var = self.get_variable(obj.code_entry)["name"]
            obj = obj.target
        if type_class == TypeClass.INTERFACE:
            return "new uno.Any(typeof(%s), %s)" % (type_name, var)
        elif type_class == TypeClass.ENUM:
            type_name = obj.typeName
            #self.add_namespace(type_name[0:type_name.rfind('.')])
            self.add_namespace(type_name)
            name = self.get_last_part(type_name)
            if var:
                return "new uno.Any(typeof(%s), %s)" % (name, var)
            else:
                return 'new uno.Any(typeof(%s) %s.%s)' % (name, name, obj.value)
        else:
            value_type = self.TYPE_CLASS_MAP[type_class.value]
            if var:
                return "new uno.Any(typof(%s), %s)" % (value_type, var)
            else:
                return 'new uno.Any(typeof(%s), %s)' % (value_type, self.value_to_string(obj, type_class))
    
    def get_out_param_index(self, idl):
        """ Returns list of out param indexes. out """
        params = idl.getParameterInfos()
        if params:
            return [i for i, info in enumerate(params) if info.aMode == ParamMode.OUT]
        else:
            return None
    
    def get_inout_param_index(self, idl):
        """ Returns list of inout param indexes. ref """
        params = idl.getParameterInfos()
        if params:
            return [i for i, info in enumerate(params) if info.aMode == ParamMode.INOUT]
        else:
            return None
    
    def add_method(self, entry):
        method = entry.idl
        method_name = method.getName()
        
        value_type_info = entry.value_type
        declaring_class = method.getDeclaringClass()
        param_infos = method.getParameterInfos()
        return_info = method.getReturnType()
        exception_infos = method.getExceptionTypes()
        
        declaring_class_name = declaring_class.getName()
        declaring_class_suffix = self.get_last_part(declaring_class_name)
        
        parent_var = self.get_variable(entry.parent)
        parent_type_name = parent_var["type_name"]
        parent_types = parent_var["interfaces"]
        
        if declaring_class_name == parent_type_name:
            parent_var_name = parent_var["name"]
        else:
            self.add_namespace(declaring_class_name, split=True)
            if declaring_class_name in parent_types:
                parent_var_name = parent_types[declaring_class_name]
            else:
                var_name = "%s%s" % (declaring_class_suffix[0].lower(), declaring_class_suffix[1:])
                parent_var_name = self.make_identical(var_name)
                self.add_variable(parent_var_name)
                parent_types[declaring_class_name] = parent_var_name
                temp_name = self.get_last_part(declaring_class_name)
                self.ad("%s %s = (%s) %s;" % (temp_name, parent_var_name, temp_name, parent_var["name"]))
        out_params = None
        if len(param_infos) == 0:
            r_part = "%s.%s()" % (parent_var_name, method_name)
        else:
            args = entry.args
            out_params = self.get_out_param_index(method)
            inout_params = self.get_inout_param_index(method)
            str_args = []
            for i, (arg, param_info) in enumerate(zip(args, param_infos)):
                var = self.value_to_string(arg, param_info.aType.getTypeClass(), param_info.aType)
                if out_params and i in out_params:
                    str_args.append("out %s" % var)
                elif inout_params and i in inout_params:
                    str_args.append("ref %s" % var)
                else:
                    str_args.append(var)
            
            r_part = "%s.%s(%s)" % (parent_var_name, method_name, ", ".join(str_args))
        
        ret_type_class = value_type_info.getTypeClass()
        ret_type_name = value_type_info.getName()
        if ret_type_class == TypeClass.VOID:
            l_part = None
        elif ret_type_class == TypeClass.INTERFACE:
            var_name, var_type = self.make_variable(self.get_last_part(ret_type_name), value_type_info)
            l_part = "%s %s" % (var_type, var_name)
        else:
            if (method_name.startswith("get") or \
                method_name.startswith("set")) and \
                not method_name.startswith("getBy"):
                var_name, var_type = self.make_variable("%s%s" % (method_name[3].upper(), method_name[4:]), value_type_info)
                if var_type:
                    l_part = "%s %s" % (var_type, var_name)
                else:
                    l_part = None
            else:
                if method_name.startswith("getBy"):
                    var_name, var_type = self.make_variable("Object", value_type_info)
                else:
                    var_name, var_type = self.make_variable(method_name, value_type_info)
                l_part = "%s %s" % (var_type, var_name)
        _break = True
        if out_params:
            _break = False
        if l_part:
            self.register_variable(entry, var_name, ret_type_class, ret_type_name)
            if return_info.getTypeClass() == TypeClass.ANY:
                if ret_type_class == TypeClass.INTERFACE:
                    obj = self.any_conv(r_part, ret_type_class, ret_type_name)
                    self.ad("%s = %s;" % (l_part, obj))
                    self.add_namespace(ret_type_name, split=True)
                else:
                    obj = self.any_conv(r_part, ret_type_class, var_type)
                    self.ad("%s = %s;" % (l_part, obj), _break=_break)
            else:
                self.ad("%s = %s;" % (l_part, r_part), _break=_break)
        else:
            self.ad("%s;" % r_part, _break=True)
        
        for e in exception_infos:
            self.add_exception(e.getName(), method_name)
    
    def add_prop(self, entry):
        name = entry.key
        parent_var = self.get_variable(entry.parent)
        parent_var_name = parent_var["name"]
        parent_type_name = parent_var["type_name"]
        parent_types = parent_var["interfaces"]
        propset = parent_var["XPropertySet"]
        if propset:
            propset_var = propset
        else:
            propset_var = self.make_identical("xPropSet")
            self.add_variable(propset_var)
            parent_var["XPropertySet"] = propset_var
            self.update_variable(entry.parent, parent_var)
            self.ad("XPropertySet %s = (XPropertySet)%s;" % (propset_var, parent_var_name))
        #if not self.propertyset_imported:
            #self.add_import("com.sun.star.beans.XPropertySet")
        #   self.propertyset_imported = True
        if entry.mode & CGMode.GET:
            if not self.get_property_exceptions_added:
                self.add_exception(
                    'com.sun.star.beans.UnknownPropertyException', 'getPropertyValue')
                self.add_exception(
                    'com.sun.star.lang.WrappedTargetException', 'getPropertyValue')
                self.get_property_exceptions_added = True
            ret_type = entry.value_type
            ret_type_name = ret_type.getName()
            ret_type_class = ret_type.getTypeClass()
            var_name, var_type = self.make_variable(name, ret_type)
            obj = "%s.getPropertyValue(\"%s\")" % (propset_var, name)
            r_part = self.any_conv(obj, ret_type_class, ret_type_name)
            self.ad("%s %s = %s;" % (var_type, var_name, r_part), _break=True)
            self.register_variable(entry, var_name, ret_type_class, ret_type_name)
        else:
            if not self.set_property_exceptions_added:
                self.add_exception(
                    "com.sun.star.beans.UnknownPropertyException", "setPropertyValue")
                self.add_exception(
                    "com.sun.star.lang.WrappedTargetException", "setPropertyValue")
                self.add_exception(
                    "com.sun.star.beans.PropertyVetoException", "setPropertyValue")
                self.add_exception(
                    "com.sun.star.lang.IllegalArgumentException", "setPropertyValue")
                self.set_property_exceptions_added = True
            value_type = entry.value_type
            value_type_class = value_type.getTypeClass()
            #arg = self.make_new_value(entry.args, value_type_class)
            #var_type = self.TYPE_CLASS_MAP.get(value_type_class.value)
            arg = self.value_to_string(entry.args, value_type_class, entry.idl)
            val = self.to_any(entry.args, value_type_class)
            self.ad("%s.setPropertyValue(\"%s\", %s);" % (propset_var, name, val))
    
    def add_attr(self, entry):
        method = entry.value_type
        declaring_class_name = entry.idl
        declaring_class_suffix = self.get_last_part(declaring_class_name)
        
        parent_var = self.get_variable(entry.parent)
        parent_type_name = parent_var["type_name"]
        parent_types = parent_var["interfaces"]
        
        if declaring_class_name == parent_type_name:
            parent_var_name = parent_var["name"]
        else:
            #self.add_import(declaring_class_name)
            self.add_namespace(declaring_class_name, split=True)
            if declaring_class_name in parent_types:
                parent_var_name = parent_types[declaring_class_name]
            else:
                var_name = "%s%s" % (declaring_class_suffix[0].lower(), declaring_class_suffix[1:])
                parent_var_name = self.make_identical(var_name)
                self.add_variable(parent_var_name)
                parent_types[declaring_class_name] = parent_var_name
                temp_name = self.get_last_part(declaring_class_name)
                self.ad("%s %s = (%s)%s;" % (temp_name, parent_var_name, temp_name, parent_var["name"]))
        
        attr_name = entry.key
        if entry.mode & CGMode.GET:
            value_type = entry.value_type
            var_name, var_type = self.make_variable(attr_name, value_type)
            self.register_variable(entry, var_name, value_type.getTypeClass(), value_type.getName())
            self.ad("%s %s = %s.%s;" % (var_type, var_name, parent_var_name, attr_name))
        else:
            # ToDo
            value_type_class = entry.value_type.getTypeClass()
            arg = self.value_to_string(entry.args, value_type_class, entry.value_type)
            self.ad("%s.%s = %s;" % (parent_var_name, attr_name, arg))
    
    def add_element(self, entry):
        parent = entry.parent
        parent_var = self.get_variable(parent)
        if entry.mode & CGMode.GET:
            value_type = entry.value_type
            var_name, var_type = self.make_variable(value_type.getName(), value_type)
            self.ad("%s %s = %s[%s];" % (var_type, var_name, parent_var["name"], entry.key))
            self.register_variable(entry, var_name, value_type.getTypeClass(), var_type)
        else:
            arg = self.value_to_string(entry.args, entry.value_type.getTypeClass(), entry.value_type)
            self.ad("%s[%s] = %s;" % (parent_var["name"], entry.key, arg))
    
    def add_field(self, entry):
        parent_idl = entry.idl
        field_name = entry.key
        field = parent_idl.getField(field_name)
        field_idl = field.getType()
        var = self.get_variable(entry.parent)
        if entry.mode & CGMode.GET:
            if field_idl.getTypeClass() == TypeClass.ANY:
                field_idl = entry.value_type
                var_name, var_type = self.make_variable(field_name, field_idl)
                self.ad("%s %s = %s;" % (var_type, var_name, self.any_conv("%s.%s" % (var["name"], field_name), field_idl.getTypeClass(), var_type)))
            else:
                var_name, var_type = self.make_variable(field_name, field_idl)
                self.ad("%s %s = %s.%s;" % (var_type, var_name, var["name"], field_name))
            self.register_variable(entry, var_name, field_idl.getTypeClass(), var_type)
        else:
            value_str = self.value_to_string(entry.args, field_idl.getTypeClass(), field_idl)
            self.ad("%s.%s = %s;" % (var["name"], field_name, value_str))
    
    def create_seq(self, entry):
        idl = entry.idl
        comp_type, dimension = self.parse_seq(idl)
        type_name = comp_type.getName()
        name = self.get_last_part(type_name)
        var_name, var_type = self.make_variable(name, idl)
        if entry.misc:
            var_name = self.make_identical(entry.misc)
        var_type = var_type.strip("[]")
        self.register_variable(entry, var_name, idl.getTypeClass(), idl.getName())
        self.ad("%s%s %s = new %s[%s];" % (var_type, "[]" * dimension, var_name, var_type, entry.args))
    
    def create_struct(self, entry):
        idl = entry.idl
        type_name = idl.getName()
        #self.add_import(type_name)
        name = self.get_last_part(type_name)
        var_name, type_name = self.make_variable(name, idl)
        self.register_variable(entry, var_name, idl.getTypeClass(), idl.getName())
        if entry.args:
            param_infos = [info.getType() for info in idl.getFields()]
            str_args = [self.value_to_string(arg, param_info.getTypeClass(), param_info) for arg, param_info in zip(entry.args, param_infos)]
            #print(str_args)
            self.ad("%s %s = new %s(%s);" % (name, var_name, name, 
                ", ".join(str_args)))
        else:
            self.ad("%s %s = new %s();" % (name, var_name, name))
    
    def create_service(self, entry):
        if not self.mcf_declared:
            self.mcf_declared = True
            #self.register_variable("xMultiServiceFactory")
            self.ad("XMultiComponentFactory xMultiComponentFactory = %s.getServiceManager();" % self.COMPONENT_CONTEXT_VAR)
        service_name = entry.key
        _name = self.get_last_part(service_name)
        var_name, var_type = self.make_variable(_name, entry.idl)
        self.ad("object %s = xMultiComponentFactory.createInstanceWithContext(" % var_name, breakable=False)
        self.ad("%s\"%s\", %s);" % (self.INDENT, service_name, self.COMPONENT_CONTEXT_VAR))
        idl = entry.idl
        self.register_variable(entry, var_name, idl.getTypeClass(), idl.getName())
    
    def get_component_context(self, entry):
        idl = entry.idl
        self.register_variable(entry, self.COMPONENT_CONTEXT_VAR, idl.getTypeClass(), idl.getName())
    
    def declare_variable(self, entry):
        idl = entry.idl
        _name = self.get_last_part(entry.key)
        var_name, var_type = self.make_variable(_name, idl)
        self.register_variable(entry, var_name, idl.getTypeClass(), idl.getName())
        value_str = self.value_to_string(entry.args, idl.getTypeClass(), idl)
        self.ad("%s %s = %s;" % (var_type, var_name, value_str))

