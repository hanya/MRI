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

from com.sun.star.frame.FrameSearchFlag import CHILDREN as FSF_CHILDREN

def get_extension_dirurl(ctx, extid):
    """Get extension directory url from the extension id."""
    pip_name = '/singletons/com.sun.star.deployment.PackageInformationProvider'
    if ctx.hasByName(pip_name):
        pip = ctx.getByName(pip_name)
        return pip.getPackageLocation(extid)
    return ''


def create_dialog_from_url(ctx,dlg_url):
    """Create dialog from URL."""
    dp = ctx.getServiceManager().createInstanceWithContext(
        'com.sun.star.awt.DialogProvider', ctx)
    return dp.createDialog(dlg_url)


# read config value from the node and the property name
def get_configvalue(ctx, nodepath, prop):
    from com.sun.star.beans import PropertyValue
    cp = ctx.getServiceManager().createInstanceWithContext( 
        'com.sun.star.configuration.ConfigurationProvider', ctx)
    node = PropertyValue()
    node.Name = 'nodepath'
    node.Value = nodepath
    try:
        cr = cp.createInstanceWithArguments( 
            'com.sun.star.configuration.ConfigurationAccess', (node,))
        if cr and (cr.hasByName(prop)):
            return cr.getPropertyValue(prop)
    except:
        return None


def call_dispatch(ctx, frame, cmd, target_name='_self'):
    from com.sun.star.util import URL
    url = URL()
    url.Complete = cmd
    
    transformer = ctx.getServiceManager().createInstanceWithContext(
        'com.sun.star.util.URLTransformer', ctx)
    dummy, url = transformer.parseStrict(url)
    dispatcher = frame.queryDispatch(url, target_name, 0)
    if dispatcher:
        dispatcher.dispatch(url, ())
        return True
    return False


# open help url (vnd.sun.star.help:...)
def open_help(desktop, url):
    if not desktop: return None
    task_frame = None
    task_frame = desktop.findFrame('OFFICE_HELP_TASK', FSF_CHILDREN)
    if not task_frame: return None
    help_frame = None
    help_frame = task_frame.findFrame('OFFICE_HELP', FSF_CHILDREN)
    if not help_frame: return None
    
    return help_frame

def get_package_info(ctx, ext_id):
    """ Get package information for extension id. """
    repositories = ("user", "shared", "bundle")
    manager_name = "/singletons/com.sun.star.deployment.ExtensionManager"
    factory_name = "/singletons/com.sun.star.deployment.thePackageManagerFactory"
    older = False
    if ctx.hasByName(manager_name):
        # 3.3 required
        manager = ctx.getByName(manager_name)
        
    elif ctx.hasByName(factory_name):
        factory = ctx.getByName(factory_name)
        older = True
    package = None
    for repository in repositories:
        if older:
            try:
                manager = factory.getPackageManager(repository)
                package = manager.getDeployedPackage(ext_id, "", None)
            except:
                pass
        else:
            package = manager.getDeployedExtension(repository, ext_id, "", None)
        if package:
            break
    return package


def get_package_version(ctx, ext_id):
    """ Get package version number. """
    package = get_package_info(ctx, ext_id)
    if package:
        return package.getVersion()
    return ""


def create_service(ctx, name, args=None):
    """ Create service with args if required. """
    smgr = ctx.getServiceManager()
    if args:
        return smgr.createInstanceWithArgumentsAndContext(name, args, ctx)
    else:
        return smgr.createInstanceWithContext(name, ctx)


def check_interface(ctx, interface_name, method_names):
    """ Check the interface is implemented or methods are implemented. """
    cr = create_service(ctx, "com.sun.star.reflection.CoreReflection")
    try:
        idl = cr.forName(interface_name)
        for name in method_names:
            r = idl.getMethod(name)
            if r is None:
                return False
    except:
        return False
    return True


def check_method_parameter(ctx, interface_name, method_name, param_index, param_type):
    """ Check the method has specific type parameter at the specific position. """
    cr = create_service(ctx, "com.sun.star.reflection.CoreReflection")
    try:
        idl = cr.forName(interface_name)
        m = idl.getMethod(method_name)
        if m:
            info = m.getParameterInfos()[param_index]
            return info.aType.getName() == param_type
    except:
        pass
    return False

