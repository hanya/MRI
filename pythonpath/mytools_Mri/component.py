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

import unohelper
from com.sun.star.beans import XIntrospection
from com.sun.star.lang import XServiceInfo
from com.sun.star.task import XJobExecutor

IMPLE_NAME = None

def create(imple_name, ctx, *args):
    global IMPLE_NAME
    if IMPLE_NAME is None:
        IMPLE_NAME = imple_name
    return Mri(ctx, *args)


class Mri(unohelper.Base, XServiceInfo, XJobExecutor, XIntrospection):
    """ Factory class for MRI instance. """
    
    VAR_NAME = 'oInitialTarget'
    
    def __init__(self, ctx, *args):
        self.ctx = ctx
        if isinstance(args, tuple) and len(args) > 0:
            self.inspect(args[0])
    
    # XJobExecutor
    def trigger(self, args=''):
        """ MRI called with arguments:
        service:mytools.Mri?OPTION_VALUE """
        desktop = self.ctx.getServiceManager().createInstanceWithContext( 
            'com.sun.star.frame.Desktop', self.ctx)
        target = None
        if args == 'none' or len(args) == 0:
            target = desktop
        elif args == 'current':
            target = desktop.getCurrentComponent()
        elif args == 'selection':
            component = desktop.getCurrentComponent()
            if component != None and hasattr(component, 'getCurrentSelection'):
                selection = component.getCurrentSelection()
                target = selection
        else:
            target = desktop
        self._run_mri(target, args)
    
    def _run_mri(self, target, name=''):
        if name == "":
            name = self.VAR_NAME
        try:
            import mytools_Mri, mytools_Mri.ui
            mri = mytools_Mri.MRI(self.ctx, mytools_Mri.ui.MRIUi)
            return mri.inspect(name, target)
        except Exception as e:
            print(("Exception %s" % e))
            import traceback
            traceback.print_exc()
        return None
    
    # XIntrospection
    def inspect(self, target):
        return self._run_mri(target)
    
    # XServiceInfo
    def getImplementationName(self):
        return IMPLE_NAME
    
    def supportsService(self, name):
        return name == IMPLE_NAME
    
    def getSupportedServiceNames(self):
        return (IMPLE_NAME,)

