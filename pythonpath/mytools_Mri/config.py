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

from com.sun.star.beans import PropertyValue
from mytools_Mri.values import ConfigNames
from mytools_Mri.tools import get_configvalue

class Config(object):
    """Keeps configuration variables and load/write them."""
    
    config_attrs = [
        'abbrev', 'browser', 'char_size', 
        'code_type', 'detailed', 'font_name', 'grid', 'pos_size', 
        'sdk_path', 'show_labels', 'show_code', 
        'sorted', 'use_pseud_props', 'use_tab', 'macros', 
        'ref_by_doxygen']
    
    GRID = 0
    GRID_UPDATE = True
    TAB = 0
    LOADED = False
    
    def __init__(self, ctx):
        """initialize and load configuration."""
        self.__dict__["ctx"] = ctx
        self.__dict__["save_options"] = False
        try:
            if not Config.LOADED:
                self.load()
                self.check_version()
                Config.LOADED = True
        except Exception as e:
            print(e)
    
    
    def __getattr__(self, name):
        if name in Config.config_attrs:
            return getattr(Config, name)
        else:
            return self.__dict__[name]
    
    def __setattr__(self, name, value):
        if name in Config.config_attrs:
            setattr(Config, name, value)
        else:
            self.__dict__[name] = value
    
    def check_version(self):
        nodepath = "/org.openoffice.Setup/Product"
        version = get_configvalue(self.ctx, nodepath, "ooSetupVersion")
        name = get_configvalue(self.ctx, nodepath, "ooName")
        if version >= "3.3":
            if name in ("OpenOffice", "Apache OpenOffice", 
                        "OpenOffice.org", "OOo-dev"):
                if version == "3.3":
                    Config.TAB = 0
                    Config.GRID = 1
                else:
                    Config.TAB = 1
                    Config.GRID = 2
                    if version > "3.4":
                        Config.GRID_UPDATE = False
            elif name == "LibreOffice":
                if version == "3.3":
                    Config.TAB = 0
                    Config.GRID = 1
                else:
                    Config.TAB = 2
                    Config.GRID = 2 if version >= "4.0" else 3
            else:
                pass
        if Config.TAB == 0:
            Config.use_tab = False
        if Config.GRID == 0:
            Config.grid = False
    
    def load(self):
        names = []
        for c in self.config_attrs:
            names.append((getattr(ConfigNames, c), c))
        try:
            names.sort(key=operator.itemgetter(0))
        except:
            _names = [(item[0], item) for item in names]
            _names.sort()
            names = [item for (key, item) in _names]
        
        config_provider = self.ctx.getServiceManager().createInstanceWithContext( 
            'com.sun.star.configuration.ConfigurationProvider', self.ctx)
        node = PropertyValue()
        node.Name = 'nodepath'
        node.Value = ConfigNames.config_node
        try:
            config_reader = config_provider.createInstanceWithArguments( 
                'com.sun.star.configuration.ConfigurationAccess', (node,))
            config_values = config_reader.getPropertyValues(tuple([name[0] for name in names]))
            for k, v in zip([name[1] for name in names], config_values):
                setattr(Config, k, v)
        except:
            raise

    def write(self):
        config_provider = self.ctx.getServiceManager().createInstanceWithContext( 
            'com.sun.star.configuration.ConfigurationProvider', self.ctx)
        node = PropertyValue()
        node.Name = 'nodepath'
        node.Value = ConfigNames.config_node
        cn = ConfigNames
        try:
            config_writer = config_provider.createInstanceWithArguments( 
                'com.sun.star.configuration.ConfigurationUpdateAccess', (node,) )
            cfg_names = (cn.browser, cn.font_name, cn.char_size, cn.sdk_path)
            cfg_values =(self.browser, self.font_name, self.char_size, self.sdk_path) 
            config_writer.setPropertyValues(cfg_names, cfg_values)
            
            config_writer.setHierarchicalPropertyValue(cn.pos_size, self.pos_size)
            if self.save_options:
                cfg_names = (cn.abbrev, cn.code_type, cn.show_code, 
                    cn.show_labels, cn.sorted, cn.use_pseud_props)
                cfg_values = (self.abbrev, self.code_type, self.show_code, 
                    self.show_labels, self.sorted, self.use_pseud_props)
                config_writer.setPropertyValues(cfg_names, cfg_values)
                self.save_options = False
            
            # store grid mode
            prev_grid = config_writer.getPropertyValue(cn.grid)
            config_writer.setPropertyValue(cn.grid, self.grid)
            if not (prev_grid == self.grid):
                self.__dict__["grid"] = prev_grid
            prev_tab = config_writer.getPropertyValue(cn.use_tab)
            config_writer.setPropertyValue(cn.use_tab, self.use_tab)
            if not (prev_tab == self.use_tab):
                self.__dict__["use_tab"] = prev_tab
            
            config_writer.setPropertyValue(cn.ref_by_doxygen, self.ref_by_doxygen)
            config_writer.commitChanges()
        except:
            raise
    
    def __repr__(self):
        return ', '.join(["%s: %s" % (k, getattr(Config, k)) for k in self.config_attrs])

