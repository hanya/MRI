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

class GeneratorForCpp(GeneratorBase):
    
    NAME = "C++"
    PSEUD_PROPERTY = False
    
    INDENT = " " * 4
    
    OBJ_PREFIX = "oObj%s"
    COMPONENT_CONTEXT_VAR = "xContext"
    HEADER = "void snippet(const Reference< XComponentContext > &%s, const %%s)\n{" % COMPONENT_CONTEXT_VAR
    FOOTER = "}"
    
    TYPE_CLASS_MAP = {
        'INTERFACE': '', 'SHORT': 'sal_Int16', 'UNSIGNED_SHORT': 'sal_uInt16', 
        'LONG': 'sal_Int32', 'UNSIGNED_LONG': 'sal_uInt32', 'HYPER': 'sal_Int64', 
        'UNSIGNED_HYPER': 'sal_uInt64', 'FLOAT': 'float', 'TYPE': 'Type', 
        'DOUBLE': 'double', 'BYTE': 'sal_Int8', 'BOOLEAN': 'sal_Bool', 
        'STRING': 'OUString', 'CHAR': 'sal_Unicode', 'SEQUENCE': 'Sequence', 
        'ANY': 'Any', 'ENUM': '', 'STRUCT': '', 'VOID': 'void'}
    
    PREFIX_MAP = {
        'INTERFACE': 'x', 'SHORT': 'n', 'UNSIGNED_SHORT': 'n',
        'LONG': 'n', 'UNSIGNED_LONG': 'n', 'HYPER': 'n',
        'UNSIGNED_HYPER': 'n', 'FLOAT': 'f', 'TYPE': 't',
        'DOUBLE': 'f', 'BYTE': 'n', 'BOOLEAN': 'b',
        'STRING': 's', 'CHAR': 'c', 'SEQUENCE': '',
        'ANY': 'o', 'STRUCT': 'a', 'ENUM': 'n'}
    
    def __init__(self, type_cast=False):
        GeneratorBase.__init__(self)
        
        self.declarations = []
        self.lines = []
        self.imported = set()
        self.variables = {}
        self.all_variables = set()
        self.namespace = set()
        self.exceptions = {}
        
        self.propertyset_imported = False
        self.get_property_exceptions_added = False
        self.set_property_exceptions_added = False
        self.oustring_imported = False
        self.add_namespace('rtl')
        self.add_namespace("com.sun.star.uno")
        self.add_import("com.sun.star.uno.XComponentContext")
        
        self.items = {
            CGType.METHOD: self.add_method, CGType.PROP: self.add_prop, 
            CGType.ATTR: self.add_attr, CGType.FIELD: self.add_field, 
            CGType.ELEMENT: self.add_element, 
            CGType.STRUCT: self.create_struct, CGType.SEQ: self.create_seq, CGType.PSEUD_PROP: self.add_method, 
            CGType.SERVICE: self.create_service, CGType.CONTEXT: self.get_component_context, CGType.VARIABLE: self.declare_variable
        }
    
    def get(self):
        namespaces = ["using namespace %s;" % i for i in self.namespace]
        namespaces.sort()
        
        if len(self.exceptions) > 0:
            indent = self.INDENT
            indent_1 = '\n%s' % indent
            body_indent = '\n%s' % (indent * 2)
            
            catched = []
            for e in self.exceptions.items():
                catched.append('catch (%s &e)' % self.get_last_part(e[0]))
                catched.append('{')
                catched.append('%s// %s' % (indent, ', '.join(e[1])) )
                catched.append('%s//printf(OUStringToOString(e.Message, RTL_TEXTENCODING_ASCII_US).getStr());' % indent)
                catched.append('}')
            
            return "\n".join((
                "\n".join(self.declarations), '', 
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
                "\n".join(self.declarations), '', 
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
            # initial element
            key_word = entry.key
            if key_word in ("", "none", "current", "selection"):
                key_word = self.VAR_NAME
            value_type = entry.value_type
            self.register_variable(entry, key_word, value_type.getTypeClass(), value_type.getName())
            type_class = value_type.getTypeClass()
            type_name = value_type.getName()
            args = ''
            if type_class == TypeClass.INTERFACE:
                self.add_import('com.sun.star.uno.XInterface')
                args = "Reference< XInterface > &%s" % key_word
            elif type_class == TypeClass.STRUCT:
                self.add_import(type_name)
                args = "%s %s" % (self.get_last_part(type_name), key_word)
            elif type_class == TypeClass.ANY:
                self.add_import('com.sun.star.uno.Any', kind='hxx')
                args = "Any %s" % (key_word)
            elif type_class == TypeClass.SEQUENCE:
                content = "%s" % ""
                args = "Sequence< %s >" % content
            else:
                args = "Any %s" % (key_word)
            #log("init type: %s" % value_type.getTypeClass())
            self.header = self.HEADER % args
    
    def ad(self, line, breakable=True, _break=False):
        self.lines.append(line)
        if _break or (breakable and len(self.lines) % 4 == 3):
            self.lines.append("")
    
    def add_import(self, type_name, kind='hpp'):
        """Add new import element."""
        type_name = type_name.strip("[]")
        if not type_name in self.imported:
            #type_name = name.strip('[]')
            self.imported.add(type_name)
            if kind == 'hpp':
                self.declarations.append('#include <%s.hpp>' % type_name.replace('.', '/'))
            elif kind == 'hxx':
                self.declarations.append('#include <%s.hxx>' % type_name.replace('.', '/'))
            else:
                return
            self.declarations.sort()
            self.add_namespace(type_name, split=True)
            return True
        return False
    
    def add_namespace(self, name, split=False):
        if split:
            name = name[0:name.rfind('.')]
        name = name.strip('[]')
        rname = '::' + name.replace('.', '::')
        if not rname in self.namespace:
            self.namespace.add(rname)
    
    def add_exception(self, name, method_name):
        methods = self.exceptions.get(name, [])
        if not method_name in methods:
            methods.append(method_name)
        self.exceptions[name] = methods
        self.add_namespace(name, split=True)
    
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
            self.all_variables.add(name)
    
    def make_variable(self, name, idl_class):
        """Make variable name and get type name."""
        var_name, var_type = self._make_variable(name, idl_class)
        vname = self.make_identical(var_name)
        self.add_variable(vname)
        return vname, var_type
    
    def _make_type_name(self, name, idl):
        """ Construct type name. """
        type_class = idl.getTypeClass()
        type_name = idl.getName()
        if type_class == TypeClass.SEQUENCE:
            comp_idl = idl.getComponentType()
            comp_type_class = comp_idl.getTypeClass()
            return "Sequence< %s >" % self._make_type_name(comp_idl.getName(), comp_type_class)
        elif type_class == TypeClass.INTERFACE:
            self.add_import(type_name)
            return "Reference< %s >" % self.get_last_part(type_name)
        else:
            return type_name
    
    def _make_variable(self, name, idl):
        """Make a variable name from XIdlClass."""
        seq = False
        name = name.strip("[]")
        type_class = idl.getTypeClass()
        type_name = idl.getName()
        
        if type_class == TypeClass.SEQUENCE:
            comp_idl = idl.getComponentType()
            cmp_type_class = comp_idl.getTypeClass()
            
            if cmp_type_class == TypeClass.SEQUENCE:
                name, vtype = self._make_variable(name, comp_idl)
                return name, "Sequence< %s >" % vtype
            else:
                #type_class = cmp_type_class
                seq = True
                name, vtype = self._make_variable(name, comp_idl)
                vtype = self._make_type_name(type_name, comp_idl)
                return name, "Sequence< %s >" % vtype
                
        if type_class == TypeClass.INTERFACE:
            self.add_import(type_name)
            suffix = self.get_last_part(type_name)
            vname = '%s%s' % (self.PREFIX_MAP.get(type_class.value, ""), suffix[1:])
            vtype = suffix
        elif type_class == TypeClass.STRUCT or \
            type_class == TypeClass.ENUM:
            self.add_import(type_name)
            suffix = self.get_last_part(type_name)
            vname = '%s%s' % (self.PREFIX_MAP.get(type_class.value, ""), suffix)
            vtype = suffix
        else:
            vname = '%s%s' % (self.PREFIX_MAP.get(type_class.value, ""), name)
            vtype = self.TYPE_CLASS_MAP.get(type_class.value, "")
        if seq:
            return (vname, "Sequence< %s >" % vtype)
        else:
            return vname, vtype
    
    def any_conv(self, obj, type_class, vtype):
        if type_class in (TypeClass.SEQUENCE, TypeClass.STRUCT, TypeClass.ENUM):
            return obj
        elif type_class == TypeClass.INTERFACE:
            return 'Reference< %s > %%s( %s, UNO_QUERY );' % (vtype, obj)
        else:
            return obj
    
    def value_to_string(self, value, type_class, param_info=None):
        """Convert value to its string notation used in the code."""
        if isinstance(value, Entry):
            var = self.get_variable(value.code_entry)
            if type_class == TypeClass.INTERFACE:
                type_name = param_info.getName()
                var_name = var["interfaces"].get(type_name, None)
                if var_name is None:
                    self.add_import(type_name)
                    _type_name = self.get_last_part(type_name)
                    return "Reference< %s >( %s, UNO_QUERY )" % (_type_name, var["name"])
                else:
                    return var_name
            return var["name"]
        else:
            if type_class == TypeClass.STRING:
                return 'OUString(RTL_CONSTASCII_USTRINGPARAM("%s"))' % value
            elif type_class == TypeClass.BOOLEAN:
                if value:
                    return 'sal_True'
                else:
                    return 'sal_False'
            elif type_class == TypeClass.ENUM:
                return '%s_%s' % (value.typeName.replace(".", "::"), value.value)
            elif type_class == TypeClass.SEQUENCE:
                comp_type, n = self.parse_seq(param_info)
                _comp_type_class = comp_type.getTypeClass()
                _comp_type = self.TYPE_CLASS_MAP.get(_comp_type_class.value)
                str_val = [self.value_to_string(v, _comp_type_class) for v in value]
                return "".join(("Sequence< " * n, _comp_type, " >" * n, "({%s}, %s)" % (", ".join(str_val), len(value))))
            elif type_class == TypeClass.INTERFACE:
                #print("void?") # ToDo return invalid reference for requested interface]
                type_name = param_info.getName()
                self.add_import(type_name)
                _type_name = self.get_last_part(type_name)
                #print(dir(param_info))
                return "Reference< %s >()" % _type_name
            else:
                if type_class in (TypeClass.BYTE, TypeClass.SHORT, TypeClass.UNSIGNED_SHORT, TypeClass.UNSIGNED_LONG, TypeClass.HYPER, TypeClass.UNSIGNED_HYPER, TypeClass.DOUBLE):
                    type_name = self.TYPE_CLASS_MAP[type_class.value]
                    return '(%s) %s' % (type_name, str(value))
                else:
                    return str(value)
    
    def assign_value(self, type_class, variable_type_name, variable_name, value):
        if type_class == TypeClass.ANY:
            self.ad('%s %s;' % (variable_type_name, variable_name), breakable=False)
            self.ad('%s >>= %s;' % (value, variable_name), force_break=True)
        else:
            self.ad('%s %s = %s;' % (variable_type_name, variable_name, value))
    
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
                temp_name = self.get_last_part(declaring_class_name)
                self.ad("Reference< %s > %s(%s, UNO_QUERY);" % (temp_name, parent_var_name, parent_var["name"]))
        out_params = None
        if len(param_infos) == 0:
            r_part = "%s->%s()" % (parent_var_name, method_name)
        else:
            args = entry.args
            str_args = [self.value_to_string(arg, param_info.aType.getTypeClass(), param_info.aType) for arg, param_info in zip(args, param_infos)]
            r_part = "%s->%s(%s)" % (parent_var_name, method_name, ", ".join(str_args))
            # ToDo outprameters, nothing to be done if 
            # passed as a variable
        
        ret_type_class = value_type_info.getTypeClass()
        ret_type_name = value_type_info.getName()
        # ToDo check any return type
        if ret_type_class == TypeClass.VOID:
            l_part = None
        elif ret_type_class == TypeClass.INTERFACE:
            var_name, var_type = self.make_variable(self.get_last_part(ret_type_name), value_type_info)
            l_part = "Reference< %s > %s" % (var_type, var_name)
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
                    self.ad("Reference< %s > %s(%s, UNO_QUERY);" % (var_type, var_name, r_part))
                else:
                    obj = self.any_conv(r_part, ret_type_class, var_type)
                    self.ad("%s;" % l_part, breakable=False)
                    self.ad("%s >>= %s;" % (obj, var_name), _break=True)
            else:
                self.ad("%s = %s;" % (l_part, r_part), _break=_break)
        else:
            self.ad("%s;" % r_part, _break=True)
        
        for e in exception_infos:
            self.add_exception(e.getName(), method_name)
    
    # ToDo extract from Any
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
            self.ad("Reference< XPropertySet > %s(%s, UNO_QUERY);" % (propset_var, parent_var_name), breakable=False)
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
            obj = "%s->getPropertyValue(OUString(RTL_CONSTASCII_USTRINGPARAM(\"%s\")))" % (propset_var, name)
            #r_part = self.any_conv(obj, ret_type_class, var_type)
            #self.ad("%s %s = %s;" % (var_type, var_name, r_part), _break=True)
            self.ad("%s %s;" % (var_type, var_name), breakable=False)
            self.ad("%s >>= %s;" % (obj, var_name), _break=True)
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
            idl = entry.idl
            value_type = entry.value_type
            value_type_class = value_type.getTypeClass()
            arg = self.value_to_string(entry.args, value_type_class, idl)
            _name = self.get_last_part(value_type.getName())
            #var_name, var_type = self.make_variable(_name, idl)
            #self.register_variable(entry, var_name, idl.getTypeClass(), idl.getName())
            #self.ad("%s %s = %s;" % (var_type, var_name, arg))
            var_name = arg
            self.ad("%s->setPropertyValue(OUString(RTL_CONSTASCII_USTRINGPARAM(\"%s\")), makeAny(%s));" % (propset_var, name, var_name), _break=True)
    
    def add_attr(self, entry):
        method = entry.value_type
        declaring_class_name = entry.idl#declaring_class.getName()
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
                temp_name = self.get_last_part(declaring_class_name)
                self.ad("Reference< %s > %s(%s, UNO_QUERY);" % (temp_name, parent_var_name, parent_var["name"]))
        attr_name = entry.key
        if entry.mode & CGMode.GET:
            value_type = entry.value_type
            type_class = value_type.getTypeClass()
            var_name, var_type = self.make_variable(attr_name, value_type)
            self.register_variable(entry, var_name, type_class, value_type.getName())
            if type_class == TypeClass.INTERFACE:
                self.ad("Reference< %s > %s = %s->get%s();" % (var_type, var_name, parent_var_name, attr_name))
            else:
                self.ad("%s %s = %s->get%s();" % (var_type, var_name, parent_var_name, attr_name))
        else:
            # ToDo
            value_type_class = entry.value_type.getTypeClass()
            arg = self.value_to_string(entry.args, value_type_class, entry.value_type)
            self.ad("%s->set%s(%s);" % (parent_var_name, attr_name, arg))
    
    def add_element(self, entry):
        parent = entry.parent
        parent_var = self.get_variable(parent)
        if entry.mode & CGMode.GET:
            value_type = entry.value_type
            # ToDo Any
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
                self.ad("%s %s;" % (var_type, var_name), breakable=False)
                self.ad("%s.%s >>= %s;" % (var["name"], field_name, var_name), _break=True)
                #self.ad("%s %s = %s;" % (var_type, var_name, self.any_conv("%s.%s" % (var["name"], field_name), field_idl.getTypeClass(), var_type)))
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
        self.ad("Sequence< %s > %s(%s);" % (var_type, var_name, entry.args))
    
    # ToDo multiple import for multiple seq
    def create_struct(self, entry):
        idl = entry.idl
        type_name = idl.getName()
        self.add_import(type_name)
        name = self.get_last_part(type_name)
        var_name, type_name = self.make_variable(name, idl)
        self.register_variable(entry, var_name, idl.getTypeClass(), idl.getName())
        if entry.args:
            #print(entry.args)
            #param_infos = self.get_member_types(idl)
            param_infos = [info.getType() for info in idl.getFields()]
            str_args = [self.value_to_string(arg, param_info.getTypeClass(), param_info) 
                for arg, param_info in zip(entry.args, param_infos)]
            #print(str_args)
            self.ad("%s %s = %s(%s);" % (name, var_name, name, 
                ", ".join(str_args)))
        else:
            self.ad("%s %s = %s();" % (name, var_name, name))
    
    def create_service(self, entry):
        if self.add_import("com.sun.star.lang.XMultiComponentFactory"):
            #self.register_variable("xMultiServiceFactory")
            self.ad("Reference< XMultiComponentFactory > xMultiComponentFactory = %s->getServiceManager();" % self.COMPONENT_CONTEXT_VAR)
        service_name = entry.key
        _name = self.get_last_part(service_name)
        var_name, var_type = self.make_variable(_name, entry.idl)
        self.ad("Reference< XInterface > %s = xMultiComponentFactory->createInstanceWithContext(" % var_name, breakable=False)
        self.ad("%sOUString(RTL_CONSTASCII_USTRINGPARAM(\"%s\")), %s);" % (self.INDENT, service_name, self.COMPONENT_CONTEXT_VAR))
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

