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

MRINAME = 'MRI'
MRI_HOME = 'http://extensions.services.openoffice.org/project/MRI'
MRI_ID = 'mytools.mri'
MRI_DIR = None

def set_mri_dir(ctx):
    global MRI_DIR
    import mytools_Mri.tools
    MRI_DIR = mytools_Mri.tools.get_extension_dirurl(ctx, MRI_ID)

class ConfigNames(object):
    config_node = '/mytools.Mri.Configuration/Settings'
    sdk_path = 'SDKDirectory'
    browser = 'Browser'
    pos_size = 'WindowPosSize'
    font_name = 'CharFontName'
    char_size = 'CharHeight'
    sorted = 'Sorted'
    abbrev = 'Abbreviated'
    detailed = 'Detailed'
    show_labels = 'ShowLabels'
    origin = 'MRIOrigin'
    show_code = 'ShowCode'
    code_type = 'CodeType'
    use_pseud_props = 'UsePseudProperty'
    grid = 'UseGrid'
    use_tab = 'UseTab'
    macros = 'Macros'
    ref_by_doxygen = "DoxygenRef"

IGNORED_INTERFACES = {'com.sun.star.script.browse.XBrowseNode'}
IGNORED_PROPERTIES = {'ActiveLayer', 'AsProperty', 'ClientMap', 'FontSlant',
    'LayoutSize', 'Modified', 'PropertyToDefault', 'UIConfigurationManager',
    'ParaIsNumberingRestart', 'NumberingLevel', 'NumberingStartValue', 'NumberingStartLevel', 'DataArray', 'FormulaArray', 'Printer', 'Material'}

# value descriptions
EMPTYSTR = '""'
VOIDVAL = '-void-'
NONSTRVAL = '-%s-'  # values can not be converted to strings
VALUEERROR = '-Error-'

# additional informations
PSEUDPORP = 'Pseud '    # pseud property
IGNORED = 'Ignored'     # listed in IGNORED_PROPERTIES
NOTACCESSED = '-----'
WRITEONLY = 'WriteOnly'
ATTRIBUTE = 'Attr.'

# abbreviated string
ABBROLD = 'com.sun.star.'
ABBRNEW = '.'

