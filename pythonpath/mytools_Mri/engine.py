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

from mytools_Mri.unovalues import MethodConcept, PropertyConcept, \
    PropertyAttribute, FieldAccessMode, ParamMode, TypeClass, TypeClassGroups
from mytools_Mri.values import EMPTYSTR, VOIDVAL, NONSTRVAL, \
    VALUEERROR, PSEUDPORP, IGNORED, NOTACCESSED, WRITEONLY, \
    ATTRIBUTE, ABBROLD, ABBRNEW, IGNORED_INTERFACES, IGNORED_PROPERTIES
import mytools_Mri.node

try:
    basestring
except:
    basestring = str

try:
    long
except:
    long = int


class MethodCallable(object):
    def __init__(self, entry, method, name):
        self._entry = entry
        self._name = name
        self._method = method
    
    def __call__(self, *args, **kwargs):
        self._entry.mri.change_history(0, self._entry)
        return self._entry.mri.invoke_method(self._method, args)


class EntryBase(object):
    """Entry for an target. """
    def __init__(self, mri, target, inspected=None, type_info=None):
        self.__dict__["target"] = target
        self.__dict__["inspected"] = inspected
        self.__dict__["type"] = type_info
        self.__dict__["mri"] = mri
        self.__dict__["code_entry"] = None
    
    def _convert_to_tuple(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            return tuple([self._convert_to_tuple(i) for i in value])
        else:
            return value.get_target() if isinstance(value, Entry) else value
    
    def get_target(self):
        try:
            if self.type.getTypeClass() == TypeClass.SEQUENCE:
                return uno.Any(self.type.getName(), 
                    self._convert_to_tuple(self.target))
        except Exception as e:
            print(("get_target: " + str(e)))
        return self.target
    
    def has_interface(self, interface):
        """check the interface is supported."""
        try:
            #return interface in [t.typeName for t in self.target.Types]
            return self.mri.engine.has_interface2(self, interface)
        except Exception as e:
            pass
        return False
    
    def supports_service(self, service):
        """ Check this entry supports the specific service. """
        if self.has_interface("com.sun.star.lang.XServiceInfo"):
            try:
                return self.target.supportsService(service)
            except:
                pass
        return False
    
    def __str__(self):
        if self.name:
            return self.name
        s = "<Entry: " + str(self.__dict__["target"]) + ">"
        if len(s) > 15:
            s = s[0:15]
        return s
    
    def __repr__(self):
        return "<Entry: " + str(self.__dict__["target"]) + ">"
    
    def __getattr__(self, name):
        """ Maybe call UNO methods or to access properties. """
        if self.inspected.hasMethod(name, MethodConcept.ALL):
            method = self.inspected.getMethod(name, MethodConcept.ALL)
            return MethodCallable(self, method, name)
        elif self.inspected.hasProperty(name, PropertyConcept.ALL):
            self.mri.change_history(0, self)
            type_class = self.type.getTypeClass()
            print((type_class == TypeClass.STRUCT))
            if type_class == TypeClass.INTERFACE:
                return self.mri.get_property_value(name)
            elif type_class == TypeClass.STRUCT:
                return self.mri.get_struct_element(name)
        raise AttributeError("%s is not found" % name)
    
    def __setattr__(self, name, value):
        if self.inspected and \
            self.inspected.hasProperty(name, PropertyConcept.ALL):
            self.mri.change_history(0, self)
            type_class = self.type.getTypeClass()
            if type_class == TypeClass.INTERFACE:
                self.mri.set_property_value(name, arg=value)
            elif type_class == TypeClass.STRUCT:
                self.mri.set_struct_element(name, value)
        else:
            self.__dict__[name] = value
        return None
    
    def __getitem__(self, k):
        if self.type.getTypeClass() == TypeClass.SEQUENCE:
            self.mri.change_history(0, self)
            return self.mri.manage_sequence(self, k)
        raise AttributeError("__getitem__ is not supported, %s" % k)
    
    def __setitem__(self, k, value):
        if self.type.getTypeClass() == TypeClass.SEQUENCE:
            append = False
            if k == len(self.target):
                self.target.append(value)
                append = True
            else:
                self.target[k] = value
            self.mri.change_history(0, self)
            self.mri.assign_element(k, value, append)
            return value
        raise AttributeError("__setitem__ is not supported")
    
    def _append(self, item):
        if self.type.getTypeClass() == TypeClass.SEQUENCE:
            self.target.append(item)
            self.mri.change_history(0, self)
            self.mri.assign_element(len(self.target) -1, item, True)
            return None
        raise AttributeError("append is not supported")


class Entry(EntryBase, mytools_Mri.node.Node):
    def __init__(self, mri, name, target, inspected=None):
        EntryBase.__init__(self, mri, target, inspected)
        mytools_Mri.node.Node.__init__(self, name)


class NotSupportedException(Exception):
    """raised if not supported."""


class MRIEngine(object):
    """Engine for MRI.
    
    engine provides only information about the target.
    """
    
    param_modes = ParamMode.modes
    field_modes = FieldAccessMode.modes
    attrbutes = PropertyAttribute.modes
    
    special_chars = {0: 'NUL', 1: 'SOH', 2: 'STX', 3: 'ETX', 
                     4: 'EOT', 5: 'ENQ', 6: 'ACK', 7: 'BEL', 
                     8: 'BS', 9: 'HT', 10: 'LF', 11: 'VT', 
                     12: 'NP', 13: 'CR', 14: 'SO', 15: 'SI', 
                     16: 'DLE', 17: 'DC1', 18: 'DC2', 19: 'DC3', 
                     20: 'DC4', 21: 'NAK', 22: 'SYN', 23: 'ETB', 
                     24: 'CAN', 25: 'EM', 26: 'SUB', 27: 'ESC', 
                     28: 'FS', 29: 'GS', 30: 'RS', 31: 'US', 32: 'SP', 
                     127: 'DEL'}
    
    def __init__(self, ctx):
        """initialize MRI engine with component context and target."""
        self.ctx = ctx
        
        smgr = ctx.getServiceManager()
        self.reflection = smgr.createInstanceWithContext(
            'com.sun.star.reflection.CoreReflection', ctx)
        self.introspection = smgr.createInstanceWithContext(
            'com.sun.star.beans.Introspection', ctx)
        self.tdm = ctx.getByName(
            '/singletons/com.sun.star.reflection.theTypeDescriptionManager')
    
    def create(self, mri, name, target, complete=True):
        """ Create new entry. """
        entry = Entry(mri, name, target)
        if complete:
            self.complete(entry)
        return entry
    
    def complete(self, entry):
        if not entry.inspected:
            entry.inspected = self.inspect(entry.target)
        if entry.type is None:
            entry.type = self.reflection.getType(entry.target)
            if entry.type is None:
                from mytools_Mri.type import ExtType2
                entry.type = ExtType2(None, self, "void", TypeClass.VOID)
    
    # introspection
    def inspect(self, target):
        """inspect the UNO object."""
        return self.introspection.inspect(target)
    
    # reflection
    def get_type(self, entry):
        """get type of the entry."""
        return self.reflection.getType(entry.target)
    
    def get_type_name(self, entry):
        """returns type name of the entry."""
        ttype = self.reflection.getType(entry.target)
        if ttype is None:
            return ""
        return ttype.Name
    
    def for_name(self, name):
        """returns type from name."""
        return self.reflection.forName(name)
    
    def get_imple_name(self, entry):
        """tries to get implementation name of the entry."""
        ttype = self.reflection.getType(entry.target)
        if not ttype:
            return ''
        elif ttype.getTypeClass() == TypeClass.INTERFACE:
            if entry.inspected.hasMethod("getImplementationName", MethodConcept.ALL):
                try:
                    return entry.target.getImplementationName()
                except:
                    pass
            return ttype.Name
        return ''
    
    def get_component_base_type(self, type):
        _tmp = type
        while type:
            _tmp = type
            type = type.getComponentType()
        return _tmp
    
    def get_method_info(self, entry, method_name, raw=False):
        """information about individual method."""
        target = entry.target
        if entry.inspected.hasMethod(method_name, MethodConcept.ALL):
            method = entry.inspected.getMethod(method_name, MethodConcept.ALL)
            if raw: return method
            try:
                d = (method.getName(), method.getReturnType().getName(), 
                    method.getDeclaringClass().getName(), 
                    ', '.join([e.getName() for e in method.getExceptionTypes()]))
            except: pass
            return d
    
    def get_methods_info(self, entry):
        """get methods informations."""
        target = entry.target
        methods = entry.inspected.getMethods(MethodConcept.ALL)
        txt = []
        atxt = txt.append
        for im in methods:
            name = im.getName()
            rettype = im.getReturnType()
            ret = im.getReturnType().getName()
            
            parainfo = im.getParameterInfos()
            dcname = im.getDeclaringClass().getName()
            exceptinfo = im.getExceptionTypes()
            
            if len(parainfo) > 0:
                args = [" ".join((self.get_mode_string(pi.aMode), pi.aType.getName(), pi.aName))
                                for pi in parainfo]
                arg = '( %s )' % ', '.join(args)
            else:
                arg = '()'
            
            if len(exceptinfo) > 0:
                strexcept = ', '.join([et.getName() for et in exceptinfo])
                
            else:
                strexcept = ""
            
            atxt((name, arg, ret, dcname, strexcept))
        return txt
    
    def get_properties_info(self, entry, property_only=False):
        """get properties informations."""
        target = entry.target
        inspected = entry.inspected
        props = inspected.getProperties(PropertyConcept.ALL)
        psi = False
        if self.has_interface2(entry, 'com.sun.star.beans.XPropertySet'):
            #print('propset supported.')
            pinfo = target.getPropertySetInfo()
            psi = (pinfo != None)
        txt = []
        atxt = txt.append
        
        pseudprop = PSEUDPORP
        ignored_properties = IGNORED_PROPERTIES
        mc_all = MethodConcept.ALL
        mc_property = MethodConcept.PROPERTY
        idlclass = None
        
        for ip in props:
            name = ip.Name
            handle = ''
            #print(name)
            typeclass = ip.Type.typeClass
            rtype = None
            attributes = self.get_attrstring(ip.Attributes)
            
            if name in ignored_properties:
                value = ""
                adinfo = IGNORED
            #else:
            # if XPropertySetInfo supported
            elif psi and pinfo.hasPropertyByName(name):
                try:
                    p = pinfo.getPropertyByName(name)
                    typeclass = p.Type.typeClass
                    # a few properties are ignored
                    vvalue = target.getPropertyValue(name)
                    value = self.get_string_value(typeclass, vvalue)
                    handle = str(p.Handle)#str(ip.Handle)
                except:
                    value = VALUEERROR
                adinfo = ''
            else:
                if property_only:
                    continue
                # get its value from its base method
                if inspected.hasMethod('get%s' % name, mc_property):
                    midl = inspected.getMethod('get%s' % name, mc_property)
                    rtype = midl.getReturnType()
                    adinfo = pseudprop
                    try:
                        vvalue, dummy = midl.invoke(target, ())
                        value = self.get_string_value(typeclass, vvalue)
                    except:
                        value = VALUEERROR
                
                elif inspected.hasMethod('is%s' % name, mc_all):
                    midl = inspected.getMethod('is%s' % name, mc_all)
                    rtype = midl.getReturnType()
                    vvalue, dummy = midl.invoke(target, ())
                    value = self.get_string_value(rtype.getTypeClass(), vvalue)
                    adinfo = pseudprop
                
                elif inspected.hasMethod('set%s' % name, mc_property):
                    value = ''
                    adinfo = pseudprop#"WriteOnly"
                    rtype = None
                    attributes = [WRITEONLY]
                else:
                    if inspected.hasProperty(name, PropertyConcept.ATTRIBUTES):
                        try:
                            vvalue = getattr(target, name)
                            value = self.get_string_value(typeclass, vvalue)
                            adinfo = ATTRIBUTE
                            rtype = None
                        except Exception as e:
                            value = ""
                            adinfo = NOTACCESSED
                            rtype = None
                    else:
                        try:
                            vvalue = getattr(target, name)
                            value = self.get_string_value(typeclass, vvalue)
                            adinfo = ""
                            rtype = None
                        except Exception as e:
                            value = ""
                            adinfo = NOTACCESSED
                            rtype = None
            
            ttype = ip.Type.typeName
            
            atxt((name, ttype, value, adinfo, ','.join(attributes), handle, typeclass, rtype))
        return txt
    

    def get_interfaces_info(self, entry):
        """get interfaces information by the introspection."""
        try:
            methods = entry.inspected.getMethods(MethodConcept.ALL)
            interfaces = {m.getDeclaringClass().getName() for m in methods}
            #interfaces = interfaces | set(self.get_basic_interfaces_info(entry))
            return list(interfaces)
        except:
            return ['Failed to get the list of interfaces.']
    
    
    def all_interfaces_info(self, entry):
        """try to get all interface informations using type definition manager."""
        try:
            services = self.get_services_info(entry)
        except:
            return self.get_interfaces_info(entry)
        all_services = self.get_service_names(entry, services)
        
        has = self.tdm.hasByHierarchicalName
        get = self.tdm.getByHierarchicalName
        interfaces = set(self.get_interfaces_info(entry)) | set(self.get_basic_interfaces_info(entry))
        for name in all_services:
            if has(name):
                interfaces = interfaces | self.get_exported_interfaces_names(get(name))
        
        # search into interfaces hierarchi
        try:
            for i in interfaces:
                interfaces = interfaces | self.get_base_types(get(i))
        except Exception as e:
            print(e)
        return list(interfaces)
    
    
    def get_basic_interfaces_info(self, entry):
        """get interface names from."""
        try:
            if hasattr(entry.target, 'getTypes'):
                return [t.typeName for t in entry.target.getTypes()]
        except Exception as e:
            print(e)
        return []
    
    
    def get_exported_interfaces_names(self, stdm):
        m_interfaces = stdm.getMandatoryInterfaces()
        o_interfaces = stdm.getOptionalInterfaces()
        m_inter = set()
        o_inter = set()
        
        if m_interfaces:
            m_inter = {m.getName() for m in m_interfaces}
        if o_interfaces:
            o_inter = {o.getName() for o in o_interfaces}
        return m_inter | o_inter
        
    
    def get_base_types(self, stdm):
        name = stdm.getName()
        if name == 'com.sun.star.uno.XInterface':
            return set()
        interfaces = {name}
        base_interface = stdm.getBaseType()
        base_interfaces = stdm.getBaseTypes()
        optional_interfaces = stdm.getOptionalBaseTypes()
        if base_interface:
            interfaces = interfaces | self.get_base_types(base_interface)
        if base_interfaces:
            for i in base_interfaces:
                interfaces = interfaces | self.get_base_types(i)
        if optional_interfaces:
            for i in optional_interfaces:
                interfaces = interfaces | self.get_base_types(i)
        return interfaces
    
    
    def get_services_info(self, entry):
        """get services informations from css.lang.XServiceInfo interface."""
        if self.has_interface2(entry, 'com.sun.star.lang.XServiceInfo'):
            if entry.type.getName() in IGNORED_INTERFACES:
                return ['Ignored.']
            try:
                return [str(s) for s in entry.target.getSupportedServiceNames()]
            except:
                pass
        else:
            raise NotSupportedException()
    
    
    def get_available_services_info(self, entry):
        """.lang.XMultiServiceFactory, .lang.XMultiComponentFactory or
        .container.XContentEnumerationAccess
        """
        if self.has_any_interface2(entry, ('com.sun.star.lang.XMultiServiceFactory',
            'com.sun.star.lang.XMultiComponentFactory',
            'com.sun.star.container.XContentEnumerationAccess')):
            try:
                return [str(s) for s in entry.target.getAvailableServiceNames()]
            except:
                pass
        else:
            raise NotSupportedException()
    
    
    def get_listeners_info(self, entry):
        """returns list of supported listeners."""
        return [info.typeName for info in entry.inspected.getSupportedListeners()]
    
    
    def get_struct_info(self, entry):
        """get struct informations."""
        target = entry.target
        ttype = self.reflection.getType(target)
        fields = ttype.getFields()
        txt = []
        atxt = txt.append
        modes = (FieldAccessMode.READWRITE, FieldAccessMode.READONLY)
        
        #if len(fields) < 1: return ''
        for field in fields:
            name = field.getName()
            ttype = field.getType()
            type_class = ttype.getTypeClass()
            type_name = ttype.getName()
            mode = field.getAccessMode()
            access_mode = self.get_field_mode(mode) #
            try:
                if mode in modes:
                    vvalue = field.get(target)
                    value = self.get_string_value(type_class, vvalue)
                else:
                    value = ''
            except Exception as e:
                print(('error at struct info: %s' % e))
                value = ''
            
            atxt((name, type_name, value, access_mode))
        return txt
    
    
    def has_interface2(self, entry, interface):
        return interface in self.get_interfaces_info(entry)
        
    
    def has_interface(self, target, interface):
        """check the interface is supported."""
        try:
            return interface in [t.typeName for t in target.Types]
        except Exception as e:
            pass
        return False
    
    
    def has_any_interface2(self, entry, interfaces):
        types = self.get_interfaces_info(entry)
        for i in interfaces:
            if i in types:
                return True
        return False
    
    def has_any_interface(self, target, interfaces):
        """check one of interfaces supported."""
        types = [t.typeName for t in target.Types]
        for i in interfaces:
            if i in types:
                return True
        return False
    
    
    def get_string_value(self, type_class, vvalue):
        """convert value to string."""
        try:
            if vvalue != None:
                if type_class in TypeClassGroups.NUMERIC:
                    return str(vvalue)
                elif type_class == TypeClass.BOOLEAN:
                    return str(vvalue)
                elif type_class == TypeClass.ENUM:
                    return str(vvalue.value)
                elif type_class == TypeClass.STRING:
                    if vvalue != "":
                        if len(vvalue) > 20: # string abbreviated into 20 chars
                            return "%s%s" % (vvalue[0:15].replace(
                                "\n","\\n").replace("\r","\\r"),"...")
                        else:
                            return vvalue.replace("\n","\\n").replace("\r","\\r")
                    elif vvalue == None:
                        return VOIDVAL
                    else:
                        return EMPTYSTR
                elif type_class == TypeClass.INTERFACE or type_class == TypeClass.STRUCT:
                    return NONSTRVAL % type_class.value
                elif type_class == TypeClass.BYTE:
                    return "%s" % vvalue
                elif type_class == TypeClass.CHAR:
                    try:
                        ch = vvalue.value
                        if ch:
                            if 32 <= ord(ch) <= 126:
                                return ch
                            else:
                                return self.special_chars[ord(ch)]
                        else: return ""
                    except Exception as e:
                        print(e)
                    #return vvalue.value
                elif type_class == TypeClass.TYPE:
                    return vvalue.typeName
                else:
                    if type_class.value != None:
                        # any, interfaces and so on
                        if isinstance(vvalue, basestring):
                            return vvalue
                        elif isinstance(vvalue, (int, float)):
                            return str(vvalue)                  
                        elif isinstance(vvalue, tuple):
                            return NONSTRVAL % 'Sequence'
                        else:
                            return NONSTRVAL % type_class.value
                    else:
                        return str(vvalue)
            else:
                return VOIDVAL
        except:
            return str(type_class)
    
    def get_value(self, value, type_name, type_class):
        if type_class in TypeClassGroups.INT:
            ret = long(value)
        elif type_class in TypeClassGroups.FLOATING:
            ret = float(value)
        elif type_class == TypeClass.BOOLEAN:
            if value.lower() == 'true' or value.strip() == '1':
                ret = True
            else:
                ret = False
        elif type_class == TypeClass.STRING:
            ret = value
        elif type_class == TypeClass.ENUM:
            try:
                ret = uno.Enum(str(type_name), str(value).upper())
            except:
                ret = None
        elif type_class == TypeClass.TYPE:
            ret = uno.getTypeByName(value)
        else:
            ret = str(value)
        return ret
    
    # ParamMode
    def get_mode_string(self, mode):
        """retruns parameter mode in string."""
        return self.param_modes.get(mode.value, '[??]')

    # FieldAccessMode
    def get_field_mode(self, mode):
        """returns field mode in string."""
        return self.field_modes.get(mode.value, '[???]')
    
    # getting infos of the target
    def get_attrstring(self, attrs):
        """convert attribute type to string."""
        attrbutes = self.attrbutes
        return [attrbutes.get(k, "") for k in attrbutes.keys() if attrs & k]
    
    
    def get_property_type(self, entry, name):
        """try to find property type."""
        inspected = entry.inspected
        props = inspected.getProperties(PropertyConcept.PROPERTYSET)
        if name in [p.Name for p in props]: return PropertyConcept.PROPERTYSET
        
        props = inspected.getProperties(PropertyConcept.METHODS)
        if name in [p.Name for p in props]: return PropertyConcept.METHODS
        
        props = inspected.getProperties(PropertyConcept.ATTRIBUTES)
        if name in [p.Name for p in props]: return PropertyConcept.ATTRIBUTES
        return 0
    
    
    def find_declared_module(self, entry, name):
        """try to find declared class of named property of attribute."""
        has = self.tdm.hasByHierarchicalName
        get = self.tdm.getByHierarchicalName
        # services
        if self.has_interface(entry.target, 'com.sun.star.lang.XServiceInfo'):
            for s in self.get_service_names(entry):
                if has(s):
                    for p in get(s).getProperties():
                        if p.getName()[len(s)+1:] == name:
                            return name, s
        
        # method of interface
        for m in entry.inspected.getMethods(MethodConcept.ALL):
            if m.getName().endswith(name):
                return m.getName(), m.getDeclaringClass().getName()
    
        # attribute of interface
        for interface in self.all_interfaces_info(entry):
            if has(interface + "::" + name):
                return name, interface
        
        # struct or exception
        idl_type = self.get_type(entry)
        idl_type_class = idl_type.getTypeClass()
        if idl_type_class in TypeClassGroups.STRUCTS:
            def check_members(_type):
                if name in _type.getMemberNames():
                    return _type.getName()
                else:
                    base_type = _type.getBaseType()
                    if base_type:
                        return check_members(base_type)
            
            desc = get(idl_type.getName())
            found = check_members(desc)
            if found:
                return name, found
        
        return "", ""
    
    def get_service_names(self, entry, names=None):
        """try to get service names hierarchi."""
        has = self.tdm.hasByHierarchicalName
        get = self.tdm.getByHierarchicalName
        if names is None:
            names = self.get_services_info(entry)
        servs = set()
        for name in names:
            try:
                servs.add(name)
            except Exception as e:
                print(("Error on get_service_names: %s" % e))
            if has(name):
                servs = servs | self.get_included_service_names(get(name))
        return servs
    
    def get_included_service_names(self, stdm):
        """Get all included service names."""
        mservs = stdm.getMandatoryServices()
        oservs = stdm.getOptionalServices()
        
        servs = set()
        #servs = {m.getName() for m in mservs} | {o.getName() for o in oservs}
        if mservs:
            servs = servs | {m.getName() for m in mservs}
            for m in mservs:
                servs = servs | self.get_included_service_names(m)
        if oservs:
            servs = servs | {o.getName() for o in oservs}
            for o in oservs:
                servs = servs | self.get_included_service_names(o)
        return servs
    
    
    def find_attribute_interface(self, entry, attr):
        """Find the attribute defining interface name.
        
        The interface name of the attribute can not be get from introspected object.
        needs to get from TypeDescriptionManager.
        """
        has = self.tdm.hasByHierarchicalName
        #interfaces = self.get_interfaces_info(entry)
        interfaces = self.all_interfaces_info(entry)
        for interface in interfaces:
            #name = '%s::%s' % (interface, attr)
            if has('%s::%s' % (interface, attr)):
                return interface
        return False
    
    
    def get_attribute_type(self, interface, attr):
        name = '%s::%s' % (interface, attr)
        if self.tdm.hasByHierarchicalName(name):
            return self.tdm.getByHierarchicalName(name)
        return None
    
    def check_method_from_container(self, method):
        def check_super_klass(klass):
            for k in klass.getSuperclasses():
                if k.getName() == "com.sun.star.container.XElementAccess":
                    return True
                else:
                    if check_super_klass(k):
                        return True
            return False
        return check_super_klass(method.getDeclaringClass())
    
    def find_field(self, name, fields_idl):
        """ Find specific field from fields idl. """
        for field in fields_idl.getFields():
            if field.getName() == name:
                return field
        raise Exception("Field not found: " + name)
    
    def get_module_type(self, name):
        try:
            idl = self.tdm.getByHierarchicalName(name)
        except:
            return ""
        else:
            return idl.getTypeClass().value
    
