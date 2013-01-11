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
import os
import re
import operator

from mytools_Mri.values import PSEUDPORP, NONSTRVAL, ABBROLD, ABBRNEW
from mytools_Mri.unovalues import TypeClass

from mytools_Mri import engine


class Mri_output_calc(object):
    
    def __init__(self, main):
        self.main = main
        self.engine = engine.MRIEngine(self.main.ctx)
        
        doc = main.desktop.loadComponentFromURL(
            'private:factory/scalc', '_blank', 0, ())
        
        doc.lockControllers()
        self._check_sheets(doc)
        try:
            self.parse_entry(self.main.main.current, doc)
        except Exception as e:
            print(e)
        doc.unlockControllers()
    
    
    def _check_sheets(self, doc):
        sheets = doc.getSheets()
        while sheets.getCount() < 4:
            for i in range(100):
                try:
                    sheets.insertNewByName("Sheet" + str(i),i)
                    break
                except:
                    continue
        names = ['Properties', 'Methods', 'Interfaces', 'Services']
        for i in range(4):
            sheets.getByIndex(i).setName(names[i])
        doc.getCurrentController().setActiveSheet(sheets.getByIndex(0))
        return
    
    
    def parse_entry(self, entry, doc):
        sheets = doc.getSheets()
        
        ttype = self.engine.get_type(entry)
        type_class = ttype.getTypeClass()
        if type_class == TypeClass.INTERFACE:
            self.make_properties(entry, sheets.getByName('Properties'))
            self.make_methods(entry, sheets.getByName('Methods'))
            self.make_interfaces(entry, sheets.getByName('Interfaces'))
            self.make_services(entry, sheets.getByName('Services'))
        elif type_class == TypeClass.STRUCT:
            pass
        elif type_class == TypeClass.SEQUENCE:
            pass
    
    
    def make_properties(self, entry, sheet):
        properties = self.engine.get_properties_info(entry)
        try:
            properties.sort(key=operator.itemgetter(0))
        except:
            _items = [(item[0], item) for item in properties]
            _items.sort()
            properties = [item for (key, item) in _items]
        data_range = sheet.getCellRangeByPosition(
            0, 1, len(properties[0]) -4, len(properties))
        
        data_range.setDataArray(tuple([tuple(p[0:5]) for p in properties]))
        sheet.getCellRangeByPosition(
            0, 0, len(properties[0]) -4, 0).setDataArray(
                (('Name', 'Value Type', 'Value', 'Info.', 'Attr.'),))
    
    def make_methods(self, entry, sheet):
        methods = self.engine.get_methods_info(entry)
        try:
            methods.sort(key=operator.itemgetter(0))
        except:
            _items = [(item[0], item) for item in methods]
            _items.sort()
            methods = [item for (key, item) in _items]
        data_range = sheet.getCellRangeByPosition(
            0, 1, len(methods[0]) -1, len(methods))
        
        data_range.setDataArray(
            tuple([tuple(m) for m in methods]))
        sheet.getCellRangeByPosition(
            0, 0, len(methods[0]) -1, 0).setDataArray(
                (('Name', 'Arguments', 'Return Type', 'Declaring Class', 'Exceptions'),))
    
    def make_interfaces(self, entry, sheet):
        interfaces = self.engine.all_interfaces_info(entry)
        interfaces.sort()
        data_range = sheet.getCellRangeByPosition(
            0, 1, 0, len(interfaces))
        
        data_range.setDataArray(
            tuple([tuple([i]) for i in interfaces]))
        sheet.getCellByPosition(0, 0).setString('Interfaces')
            
        
    
    def make_services(self, entry, sheet):
        data_range = None
        try:
            services = self.engine.get_services_info(entry)
            if services:
                services.sort()
                data_range = sheet.getCellRangeByPosition(
                    0, 1, 0, len(services))
            
                data_range.setDataArray(
                    tuple([tuple([i]) for i in services]))
                sheet.getCellByPosition(0, 0).setString('Supported Services')
        except:
            pass
        try:
            services = self.engine.get_available_services_info(entry)
            if services:
                services.sort()
                if data_range:
                    addr = data_range.getRangeAddress()
                    data_range = sheet.getCellRangeByPosition(
                        0, addr.EndRow +3, 0, addr.EndRow + len(services) +2)
                    
                    data_range.setDataArray(
                        tuple([tuple([i]) for i in services]))
                    sheet.getCellByPosition(0, addr.EndRow +2).setString('Available Services')
        except:
            pass



class Mri_output_html(object):
    indent = ' ' * 2
    
    header = """<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US">
<head>
<meta http-equiv="content-type" content="application/xhtml+xml; charset=UTF-8" />
<meta http-equiv="content-style-type" content="text/css" />
<meta http-equiv="content-script-type" content="text/javascript" />
<title>#{title}</title>
<link rel="stylesheet" href="{css}" type="text/css" media="screen" charset="UTF-8" />
<link rel="shortcut icon" href="{favicon}" type="image/png" />
</head>
<body>"""
    footer = """</body></html>"""
    title_heading = "<h2 class=\"title\">Informations</h2>"
    contents = """<div id=\"contents\"><ul>
<li><a class="contents" href="#properties">Properties</a></li>
<li><a class="contents" href="#methods">Methods</a></li>
<li><a class="contents" href="#interfaces">Interfaces</a></li>
<li><a class="contents" href="#services">Services</a></li>
</ul></div>"""
    struct_contents = """<ul>
<li><a class="contents" href="#elements">Elements</a></li>
<li><a class="contents" href="#struct_name">Struct Name</a></li>
</ul>"""
    
    idl_exp = re.compile("com\.sun\.star\.[^\s]*")
    
    def __init__(self, main):
        self.main = main
        self.engine = engine.MRIEngine(self.main.ctx)
        
        # set css
        from mytools_Mri.tools import get_extension_dirurl
        from mytools_Mri.values import MRI_ID
        ext_dir = get_extension_dirurl(self.main.ctx, MRI_ID) 
        css_url = "%s/web/history.css" % ext_dir
        js_url = "%s/web/mri.js" % ext_dir
        favicon_url = "%s/web/favicon.png" % ext_dir
        try:
            self.header = self.header.format(title='{title}', css=css_url, js=js_url, favicon=favicon_url)
        except:
            self.header = self.header.replace("{title}", "{title}").\
                replace("{css}", css_url).\
                replace("{favicon}", favicon_url)
        
        #.replace('#{css}', css_url).replace('#{js}', js_url)
        
        #self.idl_path = self.main.idlpath + ("" if self.main.idlpath.endswith("/") else "/") + 'docs/common/ref/'
        if self.main.config.sdk_path.endswith("/"):
            sep = ""
        else:
            sep = "/"
        self.idl_path = self.main.config.sdk_path + sep + 'docs/common/ref/'
        
        self.counter = 0
        self.temp_dir = self._get_temp_dir()
        
        txt = []
        txt.append(self.header.replace('#{title}', 'History'))
        txt.append('<h2 class="history">History</h2>')
        txt.append('<div class="history">')
        txt.append('<table>')
        txt.append('<tr><td class="tbl_head">Name</td><td class="tbl_head">Categories</td><td class="tbl_head">Type Name</td><td class="tbl_head">Implementation Name</td></tr>')
        #print(self.main.history.get_children())
        try:
            for child in self.main.history.get_children():
                #print("'%s'" % child)
                txt.append(self.parse_children(child, 0))
        except Exception as e:
            print(e)
        #print "\n".join(txt)
        #print(self.make_interfaces(self.main.current_entry))
        
        txt.append('</table>')
        txt.append('</div>')
        txt.append(self.footer)
        
        temp_path = self._get_temp_file_name('main.html')
        f = self._get_temp_file(temp_path)
        
        f.write("\n".join(txt).encode('utf-8'))
        f.close()
        
        self.main.web.open_url(temp_path)
    
    def _get_count(self):
        self.counter += 1
        return self.counter
    
    def parse_children(self, entry, level=0):
        txt = []
        ttype = self.engine.get_type(entry)
        type_class = ttype.getTypeClass()
        if type_class == TypeClass.INTERFACE:
            txt.append('<tr>' + self.parse_entry(entry, level) + "</tr>\n")
        elif type_class == TypeClass.STRUCT:
            txt.append('<tr>' + self.parse_struct_entry(entry, level) + "</tr>\n")
        elif type_class == TypeClass.SEQUENCE:
            txt.append('<tr>' + self.parse_struct_entry(entry, level, True) + "</tr>\n")
        level += 1
        for child in entry.get_children():
            #print(child.name)
            try:
                txt.append(self.parse_children(child, level))
            except Exception as e:
                print(e)
        return ''.join(txt)
    
    def parse_entry(self, entry, level=0):
        txt = []
        txt.append(self.get_header().replace('#{title}', entry.name))
        txt.append(self.title_heading)
        txt.append(self.contents)
        
        txt.append(self.make_properties(entry))
        txt.append(self.make_methods(entry))
        txt.append(self.make_interfaces(entry))
        txt.append(self.make_services(entry))
        
        txt.append(self.get_footer())
        
        #file_name = entry.name + ("-%s.html" % self._get_count())
        file_name = ("file_%s.html" % self._get_count())
        temp_path = self._get_temp_file_name(file_name)
        f = self._get_temp_file(temp_path)
        #f = self._get_temp_file(entry.name + '.html')
        f.write("\n".join(txt).encode('utf-8'))
        f.close()
        t = "<a href=\"" + file_name + "#%s\" title=\"%s\">%s</a>"
        categories = []
        for c in ('Properties', 'Methods', 'Interfaces', 'Services'):
            categories.append(t % (c.lower(), c, c[0]))
        return "<td class=\"name\">%s</td><td class=\"categories\"><span class=\"category\">%s</span></td><td class=\"type_name\">%s</td><td class=\"impl_name\">%s</td>" % (
            (self.indent * level) + entry.name, " ".join(categories), self.engine.get_type_name(entry), self.engine.get_imple_name(entry))
    
    
    def parse_struct_entry(self, entry, level=0, seq=False):
        txt = []
        txt.append(self.get_header().replace('#{title}', entry.name))
        txt.append(self.title_heading)
        txt.append(self.struct_contents)
        
        txt.append(self.make_struct(entry, seq))
        
        #txt.append("")
        
        txt.append(self.get_footer())
        
        file_name = entry.name + ("-%s.html" % self._get_count())
        temp_path = self._get_temp_file_name(file_name)
        f = self._get_temp_file(temp_path)
        f.write("\n".join(txt).encode('utf-8'))
        f.close()
        t = "<a href=\"" + file_name + "#%s\" title=\"%s\">%s</a>"
        categories = []
        for c in ('Elements', '', '', 'Struct Name'):
            if c:
                categories.append(t % (c.lower().replace(" ", "_"), c, c[0]))
            else:
                categories.append("_")
        return "<td class=\"name\">%s</td><td class=\"categories\"><span class=\"category\">%s</span></td><td class=\"type_name\">%s</td><td class=\"impl_name\"></td>" % ((self.indent * level) + entry.name, " ".join(categories), entry.type.getName())
    
    
    def idl_link(self, item, tag='', idl=''):
        if tag:
            if idl:
                return '<a class="" href="' + self.idl_path + idl.replace(".", "/") + ".html#" + tag + '">' + item + '</a>'
            else:
                return '<a class="" href="' + self.idl_path + item.replace(".", "/") + ".html#" + tag + '">' + item + '</a>'
        else:
            return '<a class="" href="' + self.idl_path + item.replace(".", "/") + '.html' + '">' + item + '</a>'
    
    
    def make_idl_link(self, item, abbr=True):
        if abbr:
            def idl_match(m):
                return "<a href=\"%s.html\">%s</a>" % (self.idl_path + m.group(0).replace('.', '/'), m.group(0)[12:])
            return self.idl_exp.sub(idl_match, item)
        else:
            def idl_match(m):
                return "<a href=\"%s.html\">%s</a>" % (self.idl_path + m.group(0).replace('.', '/'), m.group(0))
            return self.idl_exp.sub(idl_match, item)
    
    def _get_temp_dir(self):
        temp = self.main.ctx.getServiceManager().createInstanceWithContext(
            'com.sun.star.io.TempFile', self.main.ctx)
        uri = temp.Uri
        sys_path = uno.fileUrlToSystemPath(uri)
        i = 0
        while True:
            if not os.path.exists(sys_path + ("-%s" % i)):
                break
        name = sys_path + ("-%s" % i)
        os.mkdir(name)
        
        return name
    
    def _get_temp_file_name(self, name):
        return os.path.join(self.temp_dir, name)
    
    def _get_temp_file(self, path):
        return open(path, 'w')
    
    def get_header(self):
        return self.header

    def get_footer(self):
        return self.footer

        
    def make_properties(self, entry):
        txt = []
        txt.append('<div class="properties">')
        txt.append('<h2 class="category"><a name="properties" />Properties</h2>')
        txt.append('<table class="properties">')
        txt.append('<tr><td class="label">Name</td><td class="label">Value Type</td><td class="label">Value</td><td class="label">Info.</td class="label"><td>Attr.</td></tr>')
        services = []
        try:
            services = self.engine.get_service_names(entry)
        except: pass
        info = AttrInfo(self.engine, services, 
            self.engine.all_interfaces_info(entry))
        
        properties = self.engine.get_properties_info(entry)
        try:
            properties.sort(key=operator.itemgetter(0))
        except:
            _items = [(item[0], item) for item in properties]
            _items.sort()
            properties = [item for (key, item) in _items]
        
        names = [p[0] for p in properties]
        klasses = info.create(names)
        
        for p, k in zip(properties, klasses):
            #name, klass = self.engine.find_declared_module(entry, p[0])
            
            if k:
                item = self.idl_link(p[0], k.name, k.klass)
            else:
                item = p[0]
            try:
                txt.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                item, self.make_idl_link(p[1]), p[2], p[3], p[4]))
            except Exception as e:
                print(e)
                print(item)
        
        txt.append('</table>')
        txt.append('</div>')
        return "\n".join(txt)
    
    def make_methods(self, entry):
        txt = []
        txt.append('<div class="methods">')
        txt.append('<h2 class="category"><a name="methods" />Methods</h2>')
        txt.append('<table class="methods">')
        txt.append('<tr><td class="label">Name</td><td class="label">Arguments</td><td class="label">Return Type</td><td class="label">Declaring Class</td><td class="label">Exceptions</td>')
        
        methods = self.engine.get_methods_info(entry)
        try:
            methods.sort(key=operator.itemgetter(0))
        except:
            _items = [(item[0], item) for item in methods]
            _items.sort()
            methods = [item for (key, item) in _items]
        
        for method in methods:
            txt.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            self.idl_link(method[0], method[0], method[3]), self.make_idl_link(method[1]), 
            self.make_idl_link(method[2]), self.make_idl_link(method[3]), 
            self.make_idl_link(method[4])))
        
        txt.append('</table>')
        txt.append('</div>')
        return "\n".join(txt)
    
    def make_interfaces(self, entry):
        txt = []
        txt.append('<div class="interfaces">')
        txt.append('<h2 class="category"><a name="interfaces" />Interfaces</h2>')
        
        txt.append('<ul class="names">')
        
        #interfaces = self.engine.get_interfaces_info(entry)
        interfaces = self.engine.all_interfaces_info(entry)
        interfaces.sort()
        for i in interfaces:
            txt.append("<li>%s</li>" % self.idl_link(i))
        
        txt.append('</ul>')
        txt.append('</div>')
        
        return "\n".join(txt)
    
    def make_services(self, entry):
        txt = []
        txt.append('<div class="services">')
        txt.append('<h2 class="category"><a name="services" />Supported Service Names</h2>')
        txt.append('<ul class="names">')
        
        try:
            services = self.engine.get_services_info(entry)
            services.sort()
            for service in services:
                txt.append("<li>%s</li>" % self.idl_link(service))
        except:
            txt.append('com.sun.star.lang.XServiceInfo is not supported.')
        
        txt.append('</ul>')
        txt.append('</div>')
        
        try:
            services = self.engine.get_available_services_info(entry)
            if services:
                txt.append('<div class="services">')
                txt.append('<h2 class="category"><a name="available_services" />Available Service Names</h2>')
                txt.append('<ul class="names">')
                services.sort()
                for service in services:
                    txt.append("<li>%s</li>" % self.idl_link(service))
                
                txt.append('</ul>')
                txt.append('</div>')
        except: pass
        
        return "\n".join(txt)
    
    def make_struct(self, entry, seq=True):
        txt = []
        txt.append('<div class="elements">')
        txt.append('<h2 class="category"><a name="elements" />Elements</h2>')
        txt.append('<table class="elements">')
        txt.append('<tr><td class="label">Name</td><td class="label">Value Type</td><td class="label">Value</td><td class="label">Access Mode</td></tr>')
        
        if seq:
            txt.append(self.make_struct_sequence(entry))
        else:
            txt.append(self.make_mono_struct(entry))
        
        txt.append('</table>')
        txt.append('</div>')
        
        txt.append('<div class="struct_name">')
        txt.append('<h2 class="category"><a name="struct_name" />Struct Name</h2>')
        
        if seq:
            from mytools_Mri import Entry
            type_name = entry.type.getName()#self.engine.get_type_name(entry)
            value = entry.target
            for i in range(type_name.count('[]')):
                value = value[0]
            
            txt.append('<ul><li>%s</li></ul>' % ('[]' * type_name.count('[]') + self.idl_link(type_name.strip("[]"))))
        else:
            txt.append('<ul><li>%s</li></ul>' % self.idl_link(self.engine.get_type_name(entry)))
        txt.append('</div>')
        
        return "\n".join(txt)
    
    def make_mono_struct(self, entry):
        try:
            txt = []
            elements = self.engine.get_struct_info(entry)
            try:
                elements.sort(key=operator.itemgetter(0))
            except:
                _items = [(item[0], item) for item in elements]
                _items.sort()
                elements = [item for (key, item) in _items]
            for element in elements:
                txt.append('<tr><td>' + element[0] + \
                    '</td><td>' + self.make_idl_link(element[1]) + \
                    '</td><td>' + element[2] + \
                    '</td><td>' + element[3] + '</td></tr>')
            return "\n".join(txt)
        except Exception as e:
            print(e)
    
    def make_struct_sequence(self, entry):
        from mytools_Mri import Entry#, get_elements
        from mytools_Mri.ui.info import get_elements
        ttype = self.engine.get_type(entry)
        if not ttype: return "not supported."
        type_name = ttype.getName()
        
        n = type_name.count('[]')
        l = list(range(len(entry.target)))
        b = entry.target[:]
        if n > 1:
            for i in range(n -1):
                l, b = get_elements(l, b)
        txt = []
        if len(entry.target) > 0:
            txt = ["<tr><td colspan=\"4\">%s</td></tr>\n%s" % (m, self.make_mono_struct(Entry(None, '', t, self.engine.inspect(t)))) for t, m in zip(b, l)]
        return "\n".join(txt)
    


class AttrInfoEntry(object):
    def __init__(self, name, klass):
        self.name = name
        self.klass = klass


class AttrInfo(object):
    def __init__(self, engine, services, interfaces):
        self.services = services
        self.interfaces = interfaces
        self.engine = engine
    
    def create(self, names):
        klasses = [None for i in range(len(names))]
        
        tdm = self.engine.tdm
        # properties
        for service in self.services:
            if tdm.hasByHierarchicalName(service):
                stdm = tdm.getByHierarchicalName(service)
                n = len(service) +1
                for p in stdm.getProperties():
                    name = p.getName()[n:]
                    try:
                        klasses[names.index(name)] = AttrInfoEntry(name, service)
                    except: pass
        # attributes and based on method
        for interface in self.interfaces:
            if tdm.hasByHierarchicalName(interface):
                itdm = tdm.getByHierarchicalName(interface)
                n = len(interface) +2
                for m in itdm.getMembers():
                    name = m.getName()#[n:]
                    try:
                        name = name[n:]
                        if name.startswith(interface):
                            # attribute member
                            klasses[names.index(name)] = AttrInfoEntry(name, interface)
                        else:
                            # method member
                            for i, k in zip(range(len(klasses)), klasses):
                                if k: continue
                                if name.endswith(names[i]):
                                    klasses[i] = AttrInfoEntry(name, interface)
                    except: pass
        
        return klasses
