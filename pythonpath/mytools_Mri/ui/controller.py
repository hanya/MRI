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

from com.sun.star.frame import XController, XTitle, XDispatchProvider
from com.sun.star.lang import XServiceInfo
from com.sun.star.task import XStatusIndicatorSupplier


class MRIUIController(unohelper.Base, 
    XController, XTitle, XDispatchProvider, 
    XStatusIndicatorSupplier, XServiceInfo):
    """ Provides controller which connects between frame and model. """
    
    IMPLE_NAME = "mytools.mri.UIController"
    
    def __init__(self,frame, model):
        self.frame = frame
        self.model = model
        self.ui = None
    
    def set_ui(self, ui):
        self.ui = ui
    
    def get_imple_name(self):
        return self.ui.pages.get_imple_name()
    
    # XTitle
    def getTitle(self):
        return self.frame.getTitle()
    def setTitle(self, title):
        self.frame.setTitle(title)
    
    def dispose(self):
        self.frame = None
        self.model = None
    def addEventListener(self, xListener):
        pass
    def removeEventListener(self, aListener):
        pass
    
    # XController
    def attachFrame(self, frame):
        self.frame = frame
    def attachModel(self, model):
        self.model = model
    def suspend(self, Suspend):
        return True
    
    def getViewData(self):
        """ Returns current instance inspected. """
        return self.ui.main.current.target
    
    def restoreViewData(self, Data):
        pass
    def getModel(self):
        return self.model
    def getFrame(self):
        return self.frame
    
    def getStatusIndicator(self):
        pass
    
    # XDispatchProvider
    def queryDispatch(self, url, name, flags):
        pass
    def queryDispatches(self, requests):
        pass

    # XServiceInfo
    def getImplementationName(self):
        return self.IMPLE_NAME
    
    def supportsService(self, name):
        return name == self.IMPLE_NAME
    
    def getSupportedServiceNames(self):
        return self.IMPLE_NAME,
