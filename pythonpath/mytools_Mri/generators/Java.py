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

class GeneratorForJava(GeneratorBase):
    
    NAME = "Java"
    PSEUD_PROPERTY = False
    
    INDENT = "\t" * 1
    
    COMPONENT_CONTEXT_VAR = "xComponentContext"
    OBJ_PREFIX = "oObj%s"
    HEADER = "public static void snippet(XComponentContext %s, Object %%s)\n{" % COMPONENT_CONTEXT_VAR
    FOOTER = "}"
    
    TYPE_MAP = {
        "INTERFACE": "Object", "SHORT": "short", "UNSIGNED_SHORT": "short", 
        "LONG": "int", "UNSIGNED_LONG": "int", "HYPER": "long", 
        "UNSIGNED_HYPER": "long", "FLOAT": "float", 
        "TYPE": "com.sun.star.uno.Type", "DOUBLE": "double", "BYTE": "byte", 
        "BOOLEAN": "boolean", "STRING": "String", "CHAR": "char", 
        "SEQUENCE": "Object", "ANY": "Object", "VOID": ""}
    
    TYPE_CLASS_MAP = {
        "INTERFACE": "Object", "SHORT": "Short", "UNSIGNED_SHORT": "Short", 
        "LONG": "Integer", "UNSIGNED_LONG": "Integer", "HYPER": "Long", 
        "UNSIGNED_HYPER": "Long", "FLOAT": "Float", "TYPE": "com.sun.star.uno.Type", 
        "DOUBLE": "Double", "BYTE": "Byte", "BOOLEAN": "Boolean", 
        "STRING": "String", "CHAR": "Char", "SEQUENCE": "Sequence", 
        "ANY": "Object", "ENUM": "Enum", "STRUCT": "Struct"}
    
    ANY_CONV_MAP = {
        "INTERFACE": "Object", "SHORT": "Short", "UNSIGNED_SHORT": "Short", 
        "LONG": "Int", "UNSIGNED_LONG": "Int", "HYPER": "Long", 
        "UNSIGNED_HYPER": "Long", "FLOAT": "Float", "TYPE": "Type", 
        "DOUBLE": "Double", "BYTE": "Byte", "BOOLEAN": "Boolean", 
        "STRING": "String", "CHAR": "Char", "SEQUENCE": "Sequence", 
        "ANY": "Object", "Void": "Void", "ENUM": "Enum", "STRUCT": "Struct"}
    
    PREFIX_MAP = {
        "INTERFACE": "x", "SHORT": "n", "UNSIGNED_SHORT": "n",
        "LONG": "n", "UNSIGNED_LONG": "n", "HYPER": "n",
        "UNSIGNED_HYPER": "n", "FLOAT": "f", "TYPE": "t",
        "DOUBLE": "f", "BYTE": "n", "BOOLEAN": "b",
        "STRING": "s", "CHAR": "c", "SEQUENCE": "a",
        "ANY": "o", "STRUCT": "a", "ENUM": "o"}
    
    REGISTERED_TYPE_CLASSES = (TypeClass.INTERFACE, TypeClass.SEQUENCE, 
            TypeClass.STRUCT, TypeClass.ANY)
    
    def __init__(self, type_cast=False):
        GeneratorBase.__init__(self)
        
        self.type_cast = type_cast
        self.declarations = []
        self.lines = []
        self.imported = set()
        self.variables = {}
        self.all_variables = set()
        self.exceptions = {} # {name: [list of method names], ..}
        
        self.any_conv_imported = False
        self.propertyset_imported = False
        self.get_property_exceptions_added = False
        self.set_property_exceptions_added = False
        
        self.add_import("com.sun.star.uno.UnoRuntime")
        self.add_import("com.sun.star.uno.XComponentContext")
        
        self.items = {
            CGType.METHOD: self.add_method, CGType.PROP: self.add_prop, 
            CGType.ATTR: self.add_attr, CGType.FIELD: self.add_field, 
            CGType.ELEMENT: self.add_element, 
            CGType.STRUCT: self.create_struct, CGType.SEQ: self.create_seq, CGType.PSEUD_PROP: self.add_method, 
            CGType.SERVICE: self.create_service, CGType.CONTEXT: self.get_component_context, CGType.VARIABLE: self.declare_variable
        }
    
    def get(self):
        indent = self.INDENT
        if len(self.exceptions) > 0:
            indent_1 = "\n%s" % indent
            body_indent = "\n%s" % (indent * 2)
            # ToDo
            catched = []
            for i, e in enumerate(self.exceptions.items()):
                n = i +1
                catched.append("catch (%s e%s)" % (self.get_last_part(e[0]), n))
                catched.append("{")
                catched.append("%s// %s" % (indent, ", ".join(e[1])))
                catched.append("%se%s.printStackTrace();" % (indent, n))
                catched.append("}")
            
            return "\n".join((
                "\n".join(self.declarations), "", 
                self.header, 
                "%stry\n%s{" % (indent, indent), 
                "%s%s" % (indent * 2, body_indent.join(self.lines)), 
                "%s}" % indent, 
                "%s%s" % (self.INDENT, indent_1.join(catched)), 
                self.FOOTER))
        else:
            tab = "\n%s" % self.INDENT
            return "\n".join((
                "\n".join(self.declarations), '', 
                self.header, 
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
            # initial target
            key = entry.key
            if key in ("", "none", "current", "selection"):
                key = self.VAR_NAME
            value_type = entry.value_type
            self.register_variable(entry, key, 
                value_type.getTypeClass(), value_type.getName())
            self.header = self.HEADER % key
    
    def ad(self, line, breakable=True, _break=False):
        self.lines.append(line)
        if _break or (breakable and len(self.lines) % 4 == 3):
            self.lines.append("")
    
    def add_import(self, name):
        """ Add to import. """
        _name = name.strip("[]")
        if not _name in self.imported:
            type_name = _name
            self.imported.add(type_name)
            self.declarations.append("import %s;" % type_name)
            self.declarations.sort()
            return True
        return False
    
    def add_exception(self, name, method_name):
        """ Add to exceptions. """
        methods = self.exceptions.get(name, [])
        if not method_name in methods:
            methods.append(method_name)
        self.exceptions[name] = methods
        self.add_import(name)
    
    def make_identical(self, name):
        if not name in self.all_variables:
            return name
        i = 2
        while "%s%s" % (name, i) in self.all_variables:
            i += 1
        return "%s%s" % (name, i)
    
    def get_type_name(self, type_class):
        return self.TYPE_MAP.get(type_class.value, "")
    
    def get_prefix(self, type_class):
        return self.PREFIX_MAP.get(type_class.value, "")
    
    def get_any_conv(self, type_class):
        return self.ANY_CONV_MAP.get(type_class.value, "")
    
    # ToDo hash to class instance
    def register_variable(self, entry, name, type_class, type_name):
        #if type_class in Java.REGISTERED_TYPE_CLASSES:
        interfaces = None
        if type_class == TypeClass.INTERFACE:
            interfaces = {}
            interfaces[type_name] = name
        self.variables[entry] = {
                "name": name, "type_name": type_name, 
                "XPropertySet": "", "interfaces": interfaces}
    
    def get_variable(self, entry):
        return self.variables[entry]
    
    def update_variable(self, index, value):
        self.variables[index] = value
    
    def add_variable(self, name):
        if not name in self.all_variables:
            self.all_variables.add(name)
    
    def make_variable(self, name, idl):
        """ Returns variable name and type name. """
        _var_name, var_type = self._make_variable(name, idl)
        var_name = self.make_identical(_var_name)
        self.add_variable(var_name)
        return var_name, var_type
    
    def _make_variable(self, name, idl):
        seq = False
        name = name.strip("[]")
        type_class = idl.getTypeClass()
        type_name = idl.getName()
        if type_class == TypeClass.SEQUENCE:
            comp_idl = idl.getComponentType()
            comp_type_class = comp_idl.getTypeClass()
            if comp_type_class == TypeClass.SEQUENCE:
                name, var_type = self._make_variable(name, comp_idl)
                return name, "%s[]" % var_type
            else:
                type_class = comp_type_class
                seq = True
        
        if type_class == TypeClass.INTERFACE or \
            type_class == TypeClass.STRUCT or \
            type_class == TypeClass.ENUM:
            self.add_import(type_name)
            suffix = self.get_last_part(type_name)
            if type_class == TypeClass.INTERFACE:
                if type_name == "com.sun.star.uno.XInterface":
                    # like a service
                    var_name = "o%s" % name
                else:
                    var_name = "%s%s" % (self.get_prefix(type_class), suffix[1:])
            else:
                var_name = "%s%s" % (self.get_prefix(type_class), suffix)
            var_type = suffix
        else:
            var_name = "%s%s" % (self.get_prefix(type_class), name)
            var_type = self.get_type_name(type_class)
        if seq:
            return (var_name, "%s[]" % var_type)
        else:
            return var_name, var_type
    
    #def new_value(self, value, type_class):
    
    def any_conv(self, obj_name, type_class, var_type):
        if not self.any_conv_imported:
            self.add_import("com.sun.star.uno.AnyConverter")
            self.add_exception("com.sun.star.lang.IllegalArgumentException", '')
        if type_class == TypeClass.SEQUENCE or \
            type_class == TypeClass.STRUCT or \
            type_class == TypeClass.ENUM:
            return "(%s) AnyConverter.toObject(%s.class, %s)" % \
                        (var_type, var_type, obj_name)
        elif type_class == TypeClass.INTERFACE:
            if self.type_cast:
                return "(%s) UnoRuntime.queryInterface(%s.class, %s)" % (var_type, var_type, obj_name)
            else:
                return "UnoRuntime.queryInterface(%s.class, %s)" % (var_type, obj_name)
        else:
            return "AnyConverter.to%s(%s)" % (self.get_any_conv(type_class), obj_name)
    
    # ToDo allows to get all variables from entry
    def value_to_string(self, value, type_class, param_info=None):
        if isinstance(value, Entry):
            var = self.get_variable(value.code_entry)
            if type_class == TypeClass.INTERFACE:
                type_name = param_info.getName()
                var_name = var["interfaces"].get(type_name, None)
                if var_name is None:
                    self.add_import(type_name)
                    _type_name = self.get_last_part(type_name)
                    return "UnoRuntime.queryInterface(%s.class, %s)" % (_type_name, var["name"])
                else:
                    return var_name
            return var["name"]
        else:
            if type_class == TypeClass.STRING:
                return '"%s"' % value
            elif type_class == TypeClass.BOOLEAN:
                return str(value).lower()
            elif type_class == TypeClass.ENUM:
                return '%s.%s' % (value.typeName, value.value)
            elif type_class == TypeClass.TYPE:
                return "new com.sun.star.uno.Type(\"%s\")" % value.typeName
            elif type_class == TypeClass.CHAR:
                return "'%s'" % value.value
            elif type_class == TypeClass.LONG or type_class == TypeClass.UNSIGNED_LONG:
                return str(value)
            elif type_class == TypeClass.SEQUENCE:
                comp_type, n = self.parse_seq(param_info)
                _comp_type_class = comp_type.getTypeClass()
                _comp_type = self.TYPE_CLASS_MAP.get(_comp_type_class.value)
                str_val = [self.value_to_string(v, _comp_type_class) for v in value]
                return "new %s%s{%s}" % (_comp_type, "[]" * n, ", ".join(str_val))
            elif type_class == TypeClass.INTERFACE:
                return "null" # ToDo how about non-null values?
            else:
                if param_info:
                    value_type_class = param_info.getTypeClass()
                    cast_type = self.TYPE_MAP.get(value_type_class.value, "")
                    if cast_type:
                        return "(%s) %s" % (cast_type, str(value))
                return str(value)
    
    def make_new_value(self, value, type_class):
        class_name = self.TYPE_CLASS_MAP.get(type_class.value, "")
        if class_name == 'String':
            return 'new %s("%s")' % (class_name, value)
        elif class_name == 'Boolean':
            return 'new %s(%s)' % (class_name, str(value).lower())
        elif class_name == 'Enum':
            self.add_import(value.typeName) # import enum
            name = self.get_last_part(value.typeName)
            return '%s.%s' % (name, value.value)
        elif class_name == 'Char':
            return 'new %s(\'%s\')' % (class_name, value.value)
        else:
            return 'new %s(%s)' % (class_name, value)
    
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
            self.add_import(declaring_class_name)
            if declaring_class_name in parent_types:
                parent_var_name = parent_types[declaring_class_name]
            else:
                var_name = "%s%s" % (declaring_class_suffix[0].lower(), declaring_class_suffix[1:])
                parent_var_name = self.make_identical(var_name)
                self.add_variable(parent_var_name)
                parent_types[declaring_class_name] = parent_var_name
                #self.update_variable(entry.parent, parent_var)
                temp_name = self.get_last_part(declaring_class_name)
                if self.type_cast:
                    self.ad("%s %s = (%s) UnoRuntime.queryInterface(" % (temp_name, parent_var_name, temp_name), breakable=False)
                else:
                    self.ad("%s %s = UnoRuntime.queryInterface(" % (temp_name, parent_var_name), breakable=False)
                self.ad("%s%s.class, %s);" % (self.INDENT, temp_name, parent_var["name"]))
        out_params = None
        if len(param_infos) == 0:
            r_part = "%s.%s()" % (parent_var_name, method_name)
        else:
            out_params = self.get_out_param_index(method)
            args = entry.args
            if out_params:
                _out_params = []
                str_args = []
                for i, (arg, param_info) in enumerate(zip(args, param_infos)):
                    if i in out_params:
                        var_name, var_type = self.make_variable(param_info.aType.getName(), param_info.aType)
                        _arg = self.value_to_string(arg, param_info.aType.getTypeClass(), param_info.aType)
                        self.ad("%s[] %s = new %s[]{%s};" % (var_type, var_name, var_type, _arg))
                        str_args.append(var_name)
                        _out_params.append((var_name, _arg))
                    else:
                        str_args.append(self.value_to_string(arg, param_info.aType.getTypeClass(), param_info.aType))
            else:
                str_args = [self.value_to_string(arg, param_info.aType.getTypeClass(), param_info.aType) for arg, param_info in zip(args, param_infos)]
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
                    if self.type_cast:
                        self.ad("%s = (%s) UnoRuntime.queryInterface(" % (l_part, var_type), breakable=False)
                    else:
                        self.ad("%s = UnoRuntime.queryInterface(" % l_part, breakable=False)
                    self.ad("%s%s.class, %s);" % (self.INDENT, var_type, r_part), _break=_break)
                else:
                    obj = self.any_conv(r_part, ret_type_class, var_type)
                    self.ad("%s = %s;" % (l_part, obj), _break=_break)
            else:
                self.ad("%s = %s;" % (l_part, r_part), _break=_break)
        else:
            self.ad("%s;" % r_part, _break=True)
        
        if out_params:
            for _out_param in _out_params:
                self.ad("%s = %s[0];" % (_out_param[1], _out_param[0]), _break=True)
        
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
            if self.type_cast:
                self.ad("XPropertySet %s = (XPropertySet) UnoRuntime.queryInterface(" % propset_var, breakable=False)
            else:
                self.ad("XPropertySet %s = UnoRuntime.queryInterface(" % propset_var, breakable=False)
            self.ad("%sXPropertySet.class, %s);" % (self.INDENT, parent_var_name))
        if not self.propertyset_imported:
            self.add_import("com.sun.star.beans.XPropertySet")
            self.propertyset_imported = True
        
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
            r_part = self.any_conv(obj, ret_type_class, var_type)
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
            arg = self.value_to_string(entry.args, value_type_class, entry.idl)
            self.ad("%s.setPropertyValue(\"%s\", %s);" % (propset_var, name, arg), _break=True)
    
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
            self.add_import(declaring_class_name)
            if declaring_class_name in parent_types:
                parent_var_name = parent_types[declaring_class_name]
            else:
                var_name = "%s%s" % (declaring_class_suffix[0].lower(), declaring_class_suffix[1:])
                parent_var_name = self.make_identical(var_name)
                self.add_variable(parent_var_name)
                parent_types[declaring_class_name] = parent_var_name
                #self.update_variable(entry.parent, parent_var)
                temp_name = self.get_last_part(declaring_class_name)
                if self.type_cast:
                    self.ad("%s %s = (%s) UnoRuntime.queryInterface(" % (temp_name, parent_var_name, temp_name), breakable=False)
                else:
                    self.ad("%s %s = UnoRuntime.queryInterface(" % (temp_name, parent_var_name), breakable=False)
                self.ad("%s%s.class, %s);" % (self.INDENT, temp_name, parent_var["name"]))
        attr_name = entry.key
        if entry.mode & CGMode.GET:
            value_type = entry.value_type
            var_name, var_type = self.make_variable(attr_name, value_type)
            self.register_variable(entry, var_name, value_type.getTypeClass(), value_type.getName())
            self.ad("%s %s = %s.get%s();" % (var_type, var_name, parent_var_name, attr_name))
        else:
            # ToDo
            value_type_class = entry.value_type.getTypeClass()
            arg = self.value_to_string(entry.args, value_type_class, entry.value_type)
            self.ad("%s.set%s(%s);" % (parent_var_name, attr_name, arg))
    
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
    
    # ToDo get field value
    def add_field(self, entry):
        """ Assign value to a field. """
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
        self.add_import(type_name)
        
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
        self.add_import(type_name)
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
        if self.add_import("com.sun.star.lang.XMultiComponentFactory"):
            self.ad("XMultiComponentFactory xMultiComponentFactory = %s.getServiceManager();" % self.COMPONENT_CONTEXT_VAR)
        service_name = entry.key
        _name = self.get_last_part(service_name)
        var_name, var_type = self.make_variable(_name, entry.idl)
        """
        if entry.args:
            self.ad("Object %s = xMultiComponentFactory.createInstanceWithArgumentsAndContext(" % var_name, breakable=False)
            str_args = 
            self.ad("%s\"%s\", new Object[]{%s}, %s);" % (self.INDENT, service_name, self.COMPONENT_CONTEXT_VAR))
        else:
        """
        self.ad("Object %s = xMultiComponentFactory.createInstanceWithContext(" % var_name, breakable=False)
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

