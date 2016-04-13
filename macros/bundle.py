
# These methods are shown in Macros menu.
__all__ = [
    "inspect_index_entries", 
    "inspect_name_entries", 
    "inspect_enumeration_entries", 
    "inspect_sequence_elements", 
    "inspect_accessible_children", 
    "inspect_chart_type", 
    "", 
    "add_component_context", 
    "add_struct", 
    "", 
    "diff_with_another_mri", "diff_from_history", 
    "", 
    "inspect_configuration_modifiable", 
    "", 
    "import_macro", 
    "reload_properties", 
    "reload_macros", 
    "reload_generator", 
    "", 
    "console", 
]

import traceback

def add_component_context(mri):
    """ Add css.uno.XComponentContext to the history.
        """
    ctx = mri.get_component_context()
    mri.action_by_type(ctx)

def add_struct(mri):
    """ Add new instance of a struct.
        """
    name, state = mri.ui.dlgs.dialog_input("Struct name", "", "com.sun.star.")
    if state:
        # check the name is valid struct
        from mytools_Mri.unovalues import TypeClass, TypeClassGroups
        try:
            idl = mri.engine.for_name(name)
            if not idl.getTypeClass() == TypeClass.STRUCT:
                raise Exception()
        except:
            mri.ui.dlgs.message("%s is not valid struct name." % name, "Error")
            return
        # check the struct can be instantiated
        COMPATIBLE = TypeClassGroups.COMPATIBLE
        
        fields = idl.getFields()
        try:
            for field in fields:
                field_type = field.getType()
                field_type_class = field_type.getTypeClass()
                #field.getAccessMode() # should not READ only # ToDo ?
                if not field_type_class in COMPATIBLE:
                    raise Exception()
            elements = [(field.getName(), field.getType().getTypeClass().value) 
                            for field in fields]
            state, ret_args = mri.ui.dlgs.dialog_elemental_input(elements, "Struct " + name, 
                            ", \n".join(["%s %s" % (element[1], element[0]) for element in elements]), (name, ""))
            if state:
                try:
                    args = []
                    for field, element in zip(fields, ret_args):
                        if field.getType().getTypeClass() in (TypeClass.INTERFACE, TypeClass.STRUCT):
                            args.append(element)
                        else:
                            args.append(
                                mri.engine.get_value(element, field.getType().getName(), field.getType().getTypeClass()))
                except Exception as e:
                    mri.ui.dlgs.message("During to instantiate struct %s, \nIllegal value specified. %s" % (name, str(e)))
                    return
                try:
                    entry = mri.create_struct(name, *args)
                    mri.action_by_type(entry)
                except:
                    traceback.print_exc()
        except:
            traceback.print_exc()
            mri.ui.dlgs.message("%s contains complex type that can not be created now" % name)


def reload_properties(mri):
    """ Reload Property Values
        Try to re-get all property values. """
    mri.ui.reload_entry()

def reload_macros(mri):
    """ Reload Macros Menu
        Reload macros menu. """
    mri.macros.clear()


class MacroImportor(object):
    """ Import macros to user's directory. """
    
    class Archive(object):
        def __init__(self, file_path):
            import os.path
            file_name = os.path.basename(file_path)
            if file_name.endswith(".zip"):
                name = file_name[0:-4]
                ext = "zip"
            elif file_name.endswith(".tar.gz"):
                name = file_name[0:-7]
                ext = "tar.gz"
            elif file_name.endswith(".tar.bz2"):
                name = file_name[0:-8]
                ext = "tar.bz2"
            self.name = name
            self.ext = ext
        
        def close(self):
            self.a.close()
        
        def get_names(self): pass
        
        def get_status(self, macros_path, names):
            import os.path
            status = []
            for name in names:
                _path = os.path.join(macros_path, name)
                if os.path.exists(_path):
                    status.append("%s (Overwrite)" % name)
                else:
                    status.append(name)
            return status
        
        def extract_file(self, name): pass
        
        def extract(self, name, path): pass
        
        def has_file(self, name):
            return name in self.get_names()
    
    class ZipArchive(Archive):
        def __init__(self, file_path, mode):
            MacroImportor.Archive.__init__(self, file_path)
            import zipfile
            self.a = zipfile.ZipFile(file=file_path, mode=mode)
        
        def get_names(self):
            names = []
            for name in self.a.namelist():
                if name.find("/") == -1 and not name.startswith("."):
                    names.append(name)
            return names
        
        def extract(self, name, path, dest=None):
            import os.path
            _name = name
            if dest:
                _name = dest
            f = open(os.path.join(path, _name), "w")
            f.write(self.a.read(name))
            f.flush()
            f.close()
        
        def extract_file(self, name):
            s = self.a.read(name)
            return s
    
    class TarArchive(Archive):
        def __init__(self, file_path, mode):
            MacroImportor.Archive.__init__(self, file_path)
            import tarfile
            self.a = tarfile.open(name=file_path, mode=mode)
        
        def get_names(self):
            names = []
            members = self.a.getmembers()
            for member in members:
                if member.isfile():
                    name = member.name
                    if not name.startswith(".") and \
                        not name.startswith("/"):
                        names.append(name)
            return names
        
        def extract(self, name, path, dest=None):
            if dest:
                import os.path
                f = open(os.path.join(path, dest), "w")
                f.write(self.extract_file(name))
                f.flush()
                f.close()
            else:
                self.a.extract(name, path)
        
        def extract_file(self, name):
            f = self.a.extractfile(name)
            s = f.read()
            f.close()
            return s
    
    README = "README"
    PY_EXTENSION = ".py"
    ZIP_EXTENSION = ".zip"
    GZ_EXTENSION = ".tar.gz"
    BZ2_EXTENSION = ".tar.bz2"
    
    def __init__(self, mri):
        self.mri = mri
    
    def create(self, name):
        return self.mri.create_service(name, nocode=True)
    
    def start(self):
        sfa = self.create("com.sun.star.ucb.SimpleFileAccess")
        macros_url = self._check_directory(sfa)
        if macros_url is None: return
        files = self.select_files()
        if files is None: return
        names = []
        if len(files) == 1:
            import os.path
            dir_url = os.path.dirname(files[0])
            names.append(os.path.basename(files[0]))
        else:
            dir_url = files[0]
            names = files[1:]
        self.import_file(sfa, macros_url, dir_url, names)
        reload_macros(mri)
    
    def import_file(self, sfa, macros_url, dest_base, names):
        for name in names:
            if name.endswith(self.PY_EXTENSION):
                self.copy(sfa, macros_url, dest_base, name)
            elif name.endswith(self.ZIP_EXTENSION) or \
                name.endswith(self.GZ_EXTENSION):
                self.copy_from_archive(macros_url, dest_base, name)
    
    def copy(self, sfa, macros_url, dest_base, file_name):
        """ Simple copy. """
        sfa.copy(dest_base + "/" + file_name, macros_url + "/" + file_name)
    
    def copy_from_archive(self, macros_url, dest_base, file_name):
        import uno
        macros_path = uno.fileUrlToSystemPath(macros_url)
        file_path = uno.fileUrlToSystemPath(dest_base + "/" + file_name)
        if file_name.endswith(self.ZIP_EXTENSION):
            a = self.ZipArchive(file_path, "r")
        else:
            if file_name.endswith(self.GZ_EXTENSION):
                mode = "r:gz"
            elif file_name.endswith(self.BZ2_EXTENSION):
                mode = "r:bz2"
            else: raise TypeError("Illegal file name: %s" % file_name)
            a = self.TarArchive(file_path, mode)
        names = a.get_names()
        status = a.get_status(macros_path, names)
        message = "Following files will be imported from %s:\n%s" % \
            (file_name, "\n".join(status))
        self.message(message)
        try:
            if a.has_file(self.README):
                message = a.extract_file(self.README)
                if not self.show_readme(file_name, message):
                    raise Exception()
                a.extract(self.README, macros_path, "%s-%s" % (self.README, a.name))
            names.remove(self.README)
            for name in names:
                a.extract(name, macros_path)
        except Exception as e:
            print(e)
        a.close()
    
    def message(self, message):
        return self.mri.ui.dlgs.dialog_info(message)
    
    def _check_directory(self, sfa):
        mri = self.mri
        macros_dir = mri.config.macros
        macros_url = self.create("com.sun.star.util.PathSubstitution").\
            substituteVariables(macros_dir, True)
        # check user's dir is exist
        if not sfa.exists(macros_url):
            n = mri.ui.dlgs.message(
                "User's macros directory is not exist."+ \
                "\nDo you want to make directory?: %s" % macros_url, 
                "", "querybox", 3)
            if n == 2:
                sfa.createFolder(macros_url)
            else:
                return None
        return macros_url
    
    def show_readme(self, name, readme):
        ctx = self.mri.ctx
        dlg = ctx.getServiceManager().createInstanceWithArgumentsAndContext(
            "com.sun.star.deployment.ui.LicenseDialog", 
            (self.mri.ui.window, name, readme), ctx)
        n = dlg.execute()
        #dlg.dispose()
        return n
    
    def select_files(self):
        fp = self.create("com.sun.star.ui.dialogs.OfficeFilePicker")
        fp.initialize((0,))
        fp.setMultiSelectionMode(True)
        fp.appendFilter('All Files (*.*)', '*.*')
        fp.appendFilter('Python Script Files (*.py)', '*.py')
        fp.appendFilter("Zip Archive (*.zip)", "*.zip")
        fp.appendFilter("Tar Archive (*.tar.gz, *.tar.bz2)", "*.tar.gz;*.tar.bz2")
        fp.setCurrentFilter('All Files (*.*)')
        if fp.execute() == 1:
            return fp.getFiles()
        fp.dispose()
        return None


def import_macro(mri):
    """ Import Macros
        Copy macro files into your user's macro directory. """
    MacroImportor(mri).start()


# built-ins
# Following macros are not registered in __all__ variable but 
# they can be called though menu or shortcut keys.

def change_title(mri):
    """ Change Title
    Change title of current MRI window. """
    ui = mri.ui
    txt, state = ui.dlgs.dialog_input("Input new title name.", 
            "", ui.frame.getTitle())
    if state:
        ui.frame.setTitle(txt)

def _open_new(mri, obj):
    """ Open new MRI for a target. """
    _mri = mri.create_service('mytools.Mri', nocode=True)
    try:
        _mri.inspect(obj)
    except:
        mri.ui.error("Faild to open new window.")

def inspect_desktop(mri):
    _open_new(mri, mri.ui.desktop)

def inspect_service_manager(mri):
    _open_new(mri, mri.ctx.getServiceManager())

def inspect_service(mri):
    name, state = mri.ui.dlgs.dialog_input(
        'Service Name', 'Input a service name.', 'com.sun.star.')
    if not state: return
    
    obj = mri.create_service(name, nocode=True)
    if obj:
        _open_new(mri, obj)
    else:
        mri.ui.error("Illegal service name: \n%s" % name)

def inspect_struct(mri):
    name, state = mri.ui.dlgs.dialog_input(
        'Struct Name', 'Input a strct name.', 'com.sun.star.')
    if not state: return
    obj = None
    ttype = mri.engine.for_name(name) # check is struct
    if ttype != None:
        type_class = ttype.getTypeClass()
        from com.sun.star.uno.TypeClass import STRUCT
        if type_class == STRUCT:
            d, obj = ttype.createObject(None)
    if obj:
        _open_new(mri, obj)
    else:
        mri.ui.error("Illegal struct name: \n%s" % name)

def inspect_configuration(mri):
    name, state = mri.ui.dlgs.dialog_input( 
        'Node Name', 'Input a hierachical name of a configuration node.', '/org.openoffice.')
    if not state: return
    cp = mri.create_service('com.sun.star.configuration.ConfigurationProvider', nocode=True)
    props = mri.create_struct('com.sun.star.beans.PropertyValue',  nocode=True)
    props.Name = 'nodepath'
    props.Value = name
    try:
        obj = cp.createInstanceWithArguments(
                'com.sun.star.configuration.ConfigurationAccess', (props,))
        _open_new(mri, obj)
    except:
        mri.ui.error("Illegal node name: \n%s" % name)

def inspect_frame(mri, name):
    obj = None
    frames = mri.ui.desktop.getFrames()
    for i in range(frames.getCount()):
        frame = frames.getByIndex(i)
        if name == frame.Title:
            obj = frame
            break
    if obj:
        _open_new(mri, obj)
    else:
        mri.ui.error("Unknown frame name: \n%s" % name)

def inspect_new_document(mri, name):
    obj = mri.ui.desktop.loadComponentFromURL(
        "private:factory/%s" % name, "_blank", 0, ())
    _open_new(mri, obj)

def duplicate_mri_window(mri):
    _open_new(mri, mri.current.target)


# General purpose macros.

def inspect_enumeration_entries(mri):
    """ Inspect Elements of Enumeration Container
        Load all entries by enumeration. """
    entry = mri.current
    enum = None
    if entry.has_interface("com.sun.star.container.XEnumerationAccess"):
        enum = entry.createEnumeration()
    elif entry.has_interface("com.sun.star.container.XEnumeration"):
        enum = entry
    if enum:
        target = enum.target
        while target.hasMoreElements():
            enum.nextElement()

def inspect_index_entries(mri):
    """ Inspect Elements of Index Container
        Load all entries from index container. """
    entry = mri.current
    if entry.has_interface("com.sun.star.container.XIndexAccess"):
        for i in range(entry.target.getCount()):
            entry.getByIndex(i)

def inspect_name_entries(mri):
    """ Inspect Elements of Named Container
        Load all entries from named container. """
    entry = mri.current
    if entry.has_interface("com.sun.star.container.XNameAccess"):
        for name in entry.target.getElementNames():
            entry.getByName(name)

def inspect_sequence_elements(mri):
    """ Inspect Elements of Sequence 
        Load all entries of the sequence. """
    from mytools_Mri.unovalues import TypeClass
    entry = mri.current
    if entry.type.getTypeClass() == TypeClass.SEQUENCE:
        for i in range(len(entry.target)):
            dummy = entry[i]


def inspect_accessible_children(mri):
    """ Inspect Accessible Children
        Inspect all accessible children. """
    _entry = mri.current
    
    roles = get_enum_map(mri, "com.sun.star.accessibility.AccessibleRole")
    
    entry = _entry.getAccessibleContext() if _entry.has_interface("com.sun.star.accessibility.XAccessible") else _entry
    for i in range(entry.target.getAccessibleChildCount()):
        c = entry.getAccessibleChild(i)
        if c:
            if c.has_interface("com.sun.star.accessibility.XAccessibleContext"):
                role = c.target.getAccessibleRole()
            elif c.has_interface("com.sun.star.accessibility.XAccessible"):
                role = c.target.getAccessibleContext().getAccessibleRole()
            
            c.name = c.name + ", Role: {}".format(roles[role])
    # update history list and tree view if there
    if mri.ui.tree:
        mri.ui.tree.update_labels()


def get_enum_map(mri, name):
    """ Returns enum value to name and name to enum value map.
        @param mri      mri instance
        @param name     name of enum """
    ret = {}
    tdm = mri.engine.tdm
    n = len(name) + 1
    roles = tdm.getByHierarchicalName(name)
    constants = roles.getConstants()
    for c in constants:
        _name = c.getName()
        v = c.getConstantValue()
        ret[_name[n:]] = v
        ret[v] = _name[n:]
    return ret


# For charts.

def inspect_chart_type(mri):
    """ Inspect Data Sequences of Chart
        Inspect all data sequence of current chart. """
    if mri.current.supports_service("com.sun.star.chart.ChartDocument"):
        chart = mri.current
        diagram = chart.getFirstDiagram()
        coords = diagram.getCoordinateSystems()
        coord = coords[0]
        chart_types = coord.getChartTypes()
        chart_type = chart_types[0]
        list_of_series = chart_type.getDataSeries()
        for i in range(len(list_of_series.target)):
            series = list_of_series[i]
            list_of_seq = series.getDataSequences()
            for j in range(len(list_of_seq.target)):
                seq = list_of_seq[j]
                seq.getLabel()
                seq.getValues()


def inspect_configuration_modifiable(mri):
    """ Modifiable Configuration
        provided by UpdateAccess. """
    name, state = mri.ui.dlgs.dialog_input( 
        'Node Name', 'Input a hierachical name of a configuration node.', '/org.openoffice.')
    if not state: return
    cp = mri.create_service('com.sun.star.configuration.ConfigurationProvider', nocode=True)
    props = mri.create_struct('com.sun.star.beans.PropertyValue',  nocode=True)
    props.Name = 'nodepath'
    props.Value = name
    try:
        obj = cp.createInstanceWithArguments(
                'com.sun.star.configuration.ConfigurationUpdateAccess', (props,))
        _open_new(mri, obj)
    except:
        mri.ui.error("Illegal node name: \n%s" % name)


def reload_generator(mri):
    """ Reload Current Code Generator
        For code generator development. """
    reloaded = False
    cg = mri.cg
    g = cg.generator
    cg.set_enable(False)
    try:
        name = g.__class__.__module__
        mod = __import__(name)
        for name in name.split(".")[1:]:
            mod = getattr(mod, name)
        reload(mod) # reload has been gone since Python 3.4
    except Exception as e:
        if str(e) != "name 'reload' is not defined":
            print(e)
    else:
        reloaded = True
    if not reloaded:
        try:
            import importlib
            importlib.reload(mod)
        except Exception as e:
            print(e)
    cg.set_enable(True)


# diff

def diff_from_history(mri):
    """ Diff in History
        Compare current target with a target from history."""
    children = mri.history.get_children()
    if len(children) == 0 or \
        (len(children) > 0 and children[0].get_child_count() <= 0):
        mri.ui.message("No history to compare with current one.")
        return
    engine = mri.engine
    current = mri.current
    imple_name = engine.get_imple_name(current)
    
    import unohelper
    from com.sun.star.view import XSelectionChangeListener
    class TreeSelectionListener(unohelper.Base, XSelectionChangeListener):
        def __init__(self, engine, entry, imple_name):
            self.engine = engine
            self.entry = entry
            self.imple_name = imple_name
        def disposing(self, ev): pass
        def selectionChanged(self, ev):
            state = False
            selected = ev.Source.getSelection()
            try:
                if selected:
                    obj = selected.DataValue.obj
                    if not obj == self.entry and \
                        self.engine.get_imple_name(obj) == self.imple_name:
                        state = True
                    ev.Source.getContext().getControl("btnOk").setEnable(state)
            except Exception as e:
                print(e)
    
    listener = TreeSelectionListener(engine, current, imple_name)
    obj = mri.ui.dlgs.history_selector("Choose an Entry", listener)
    if obj:
        if engine.get_imple_name(obj) != imple_name:
            mri.ui.error()
            return
        _diff_compare(mri, current, obj, current.name, obj.name)


def diff_with_another_mri(mri):
    """ Diff
        Compare current target with a target from another MRI."""
    ui = mri.ui
    from mytools_Mri.ui.controller import MRIUIController
    import mytools_Mri.values
    MRINAME = mytools_Mri.values.MRINAME
    mris = []
    current = ui.frame.getController()
    imple_name = ui.pages.get_imple_name()
    frames = ui.desktop.getFrames()
    for i in range(frames.getCount()):
        frame = frames.getByIndex(i)
        if frame.Name == MRINAME:
            controller = frame.getController()
            #if isinstance(controller, MRIUIController) and \
            if controller.getImplementationName() == MRIUIController.IMPLE_NAME and \
                not current == controller:
                mris.append(frame)
    if len(mris) == 0:
        ui.error("There is not any MRI frame that comparing with.")
        return
    names = tuple([frame.Title for frame in mris])
    title = ui.dlgs.dialog_select(names)
    if title is None:
        return
    n = names.index(title)
    frame = mris[n]
    del names
    del mris
    if frame.Name != MRINAME:
        ui.error("%s frame does not exist." % title)
        return
    if hasattr(frame.getController(), "ui"):
        entry2 = frame.getController().ui.main.current
    else:
        entry2 = frame.getController().getViewData()
    _diff_compare(mri, mri.current, 
        entry2, 
        ui.frame.Title, frame.Title)


def _diff_compare(mri, entry1, entry2, title1="", title2=""):
    """ Compare two entries. """
    engine = mri.engine
    if not isinstance(entry2, entry1.__class__):
        entry2 = engine.create(mri, "temp", entry2)
    if engine.get_imple_name(entry1) != engine.get_imple_name(entry2):
        raise Exception("Different type objects are not comparable.")
    
    diffs = [] # different properties
    # cutting corner
    info1 = engine.get_properties_info(entry1)
    info2 = engine.get_properties_info(entry2)
    
    names1 = set([i[0] for i in info1])
    names2 = set([i[0] for i in info2])
    
    names = names1.intersection(names2)
    _names1 = names1.difference(names2)
    _names2 = names2.difference(names1)
    
    _info1 = {}
    for i in info1:
        _info1[i[0]] = i
    _info2 = {}
    for i in info2:
        _info2[i[0]] = i
    
    names = list(names)
    names.sort()
    for name in names:
        i1 = _info1[name]
        i2 = _info2[name]
        if not i1[2] == i2[2]:
            diffs.append((i1, i2))
    
    _write_diff_to_doc(mri, names, diffs, _info1, _info2, _names1, _names2, title1, title2)

def _write_diff_to_doc(mri, names, diffs, _info1, _info2, _names1, _names2, title1, title2):
    DIFFERENCE = "Table Difference"
    # write into writer's table
    doc = mri.ui.desktop.loadComponentFromURL(
        "private:factory/swriter", "_blank", 0, ())
    doc.lockControllers()
    text = doc.getText()
    # create style
    styles = doc.getStyleFamilies().getByName("ParagraphStyles")
    if not styles.hasByName(DIFFERENCE):
        style = doc.createInstance(
            "com.sun.star.style.ParagraphStyle")
        styles.insertByName(DIFFERENCE, style)
        style.CharColor = 0xff0000
        style.CharWeight = 150.0
    
    def create_table(rows, columns, title):
        table = doc.createInstance("com.sun.star.text.TextTable")
        table.initialize(rows, columns)
        text.insertTextContent(text.getEnd(), table, False)
        cursor = table.createCursorByCellName("A1")
        cursor.goRight(4, True)
        cursor.mergeRange()
        cell = table.getCellByName("A1")
        cell.setString(title)
        r = table.getCellRangeByName("A2:E2")
        r.setDataArray((("Name", "Type", "Value", "Info.", "Attr."),))
        for i in range(5):
            cell = table.getCellByName("%s2" % chr(i + 0x41)).\
                getText().createTextCursor().ParaStyleName = "Table Heading"
        return table
    
    if title1 and title2:
        title = "Difference between A: \"%s\" and B: \"%s\"" % (title1, title2)
    else:
        title = "Result of diff."
    table = create_table(len(diffs) * 2 + 2, 5, title)
    i = 3
    for i1, i2 in diffs:
        r = table.getCellRangeByName("A%d:E%d" % (i, i +1))
        r.setDataArray(
            ((i1[0], i1[1], i1[2], i1[3], i1[4]), 
            (i2[0], i2[1], i2[2], i2[3], i2[4])))
        cell = table.getCellByName("C%d" % (i+1))
        cell.getText().createTextCursor().ParaStyleName = DIFFERENCE
        i += 2
    if _names1:
        names = list(_names1)
        names.sort()
        table = create_table(len(names) + 2, 5, 
            "Properties exist only on A")
        for i, name in enumerate(names):
            i1 = _info1[name]
            r = table.getCellRangeByName("A%d:E%d" % (i +3, i +3))
            r.setDataArray(
                ((i1[0], i1[1], i1[2], i1[3], i1[4]),))
    if _names2:
        names = list(_names2)
        names.sort()
        table = create_table(len(names) + 2, 5, 
            "Properties exist only on B")
        for i, name in enumerate(names):
            i2 = _info2[name]
            r = table.getCellRangeByName("A%d:E%d" % (i +3, i +3))
            r.setDataArray(
                ((i2[0], i2[1], i2[2], i2[3], i2[4]),))
    doc.unlockControllers()
    doc.setModified(False)


import uno
import unohelper

from com.sun.star.lang import XEventListener
class ComponentWindowListener(unohelper.Base, XEventListener):
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev):
        self.cast.dispose()
        self.cast = None

from com.sun.star.awt import XWindowListener
class WindowListener(unohelper.Base, XWindowListener):
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev):
        self.cast = None
    def windowMoved(self, ev): pass
    def windowShown(self, ev): pass
    def windowHidden(self, ev): pass
    def windowResized(self, ev):
        ps = ev.Source.getPosSize()
        self.cast.resize(ps.Width, ps.Height)

from com.sun.star.awt import XKeyListener
class KeyListener(unohelper.Base, XKeyListener):
    def __init__(self, cast):
        self.cast = cast
    def disposing(self, ev):
        self.cast = None
    def keyReleased(self, ev): pass
    def keyPressed(self, ev):
        code = ev.KeyCode
        if code == 1280:
            self.cast.do_enter()
        elif code == 1025:
            self.cast.do_previous()
        elif code == 1024:
            self.cast.do_next()
        #elif code == 524: # P


from com.sun.star.awt.PosSize import \
    POSSIZE as PS_POSSIZE, SIZE as PS_SIZE, \
    Y as PS_Y, HEIGHT as PS_HEIGHT, WIDTH as PS_WIDTH
from com.sun.star.awt.WindowAttribute import \
    BORDER as WA_BORDER, SHOW as WA_SHOW, \
    SIZEABLE as WA_SIZEABLE, MOVEABLE as WA_MOVEABLE, CLOSEABLE as WA_CLOSEABLE
from com.sun.star.view.SelectionType import SINGLE as ST_SINGLE
from com.sun.star.awt.WindowClass import SIMPLE as WC_SIMPLE
from com.sun.star.awt import FocusEvent, Selection
from com.sun.star.beans import NamedValue, PropertyValue

import code
import sys

# complement from the object

class NoEntryExist(Exception):
    """ Any more entry exist. """


class History(object):
    """ Manages history. """
    
    #MAX = 30
    
    def __init__(self):
        self.history = []
        self.i = 0
    
    def __len__(self):
        return len(self.history)
    
    def append(self, s):
        self.history.append(s)
    
    def reset(self):
        self.i = 0
    
    def previous(self):
        self.i += -1
        if abs(self.i) > len(self.history):
            self.i = - len(self.history)
        return self.history[self.i]
    
    def next(self):
        self.i += 1
        if self.i == 0:
            return ""
        return self.history[self.i]
    
    def do_p(self, s):
        pass



class MRIConsole(object):
    """ Provides simple console function which allows 
        to manipulate MRI or targets in Python code. """
    
    NAME = "MRI Console"
    VERSION = "0.1.0"
    
    PROMPT1 = ">>> "
    PROMPT2 = "... "
    
    X = 350
    Y = 50
    WIDTH = 400
    HEIGHT = 200
    INPUT_HEIGHT = 25
    
    Consoles = [] # living consoles
    
    def get_console(mri):
        """ Get the console belonging to the mri instance. """
        consoles = MRIConsole.Consoles
        for console in consoles:
            if console.equal(mri):
                return console
        console = MRIConsole(mri)
        consoles.append(console)
        return console
    
    get_console = staticmethod(get_console)
    
    def _unregister(console):
        """ Remove from list of consoles living. """
        try:
            MRIConsole.Consoles.remove(console)
        except:
            pass
    
    _unregister = staticmethod(_unregister)
    
    SHORT_HELP = "Type console.help() to show help message."
    HELP = """ This is simple console for MRI tool, which allows you 
to manipulate targets without writing code into a file. 
These variables are pre-defined: 
  mri: MRI instance which is bound by the console.
  ctx: component context.
  uno: uno module.
  console: access to current console instance.
  create: function to create new instance of a service.
"""
    
    def __init__(self, mri):
        self.ctx = mri.ctx
        self.mri = mri
        self.env = {} # eval is in this environment
        self.frame = None
        self.text = None
        self.rich = None
        self.scroll = None
        self.input = None
        self.interpreter = None
        self.leading = False
        self._stdout = None
        self._stderr = None
        self.selection = Selection(4, 4)
        #self.selection2 = Selection(-1, -1)
        self.char_size = mri.config.char_size
        self.font_name = mri.config.font_name
        self.cursor = None
        self.history = History()
        
        self._init_interpreter()
        self._init_ui()
        self.set_prompt(self.leading)
        
        self.write("%s version %s.\n" % (self.NAME, self.VERSION))
        self.write(self.SHORT_HELP + "\n")
    
    def equal(self, mri):
        """ Check is the same instance of MRI. """
        return self.mri == mri
    
    def _init_interpreter(self):
        """ Initialize interpreter. """
        self._init_env()
        self.interpreter = code.InteractiveInterpreter(self.env)
        self.interpreter.write = self.write
    
    def _init_env(self):
        """ Initialize interpreter environment. """
        self.env.clear()
        env = self.env
        env["ctx"] = self.ctx
        env["mri"] = self.mri
        env["create"] = self.create
        env["uno"] = uno
        env["__doc__"] = MRIConsole.__doc__
        env["__name__"] = "__console__"
        env["console"] = self
    
    def clear(self):
        """ Clear output. """
        self.rich.setText("")
    
    def help(self):
        """ Print help message. """
        self.write(self.HELP)
    
    def create(self, name, args=None):
        """ Create service instance from its name and additional arguments if there. """
        if args:
            return self.ctx.getServiceManager().\
                createInstanceWithArgumentsAndContext(name, args, self.ctx)
        else:
            return self.ctx.getServiceManager().\
                createInstanceWithContext(name, self.ctx)
    
    def dispose(self):
        """ Helps to clear. """
        MRIConsole._unregister(self)
        self.interpreter = None
        self.env.clear()
        self.ctx = None
        self.mri = None
        self.frame = None
        self.text = None
        self.rich = None
        self.cursor = None
        self.selection = None
    
    def focus(self):
        """ Make front this frame. """
        self.frame.focusGained(FocusEvent())
    
    def restore_out(self):
        """ Restore stdout and stderror. """
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        self._stdout = None
        self._stderr = None
    
    def replace_out(self):
        """ Replace stdout and stderror. """
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def write(self, s):
        """ Write out the string to rich edit control. """
        is_maximum = False
        if self.scroll:
            is_maximum = (self.scroll.getValue() + self.scroll.getVisibleSize()) >= self.scroll.getMaximum()
        self.cursor.gotoRange(self.text.getEnd(), False)
        self.text.insertString(self.cursor, s, False)
        if self.scroll and is_maximum:
            self.scroll.setValue(self.scroll.getMaximum())
        # there is no way to move the cursor on richedit
    
    def set_prompt(self, leading, s=""):
        """ Show prompt. """
        if self.leading:
            prompt = self.PROMPT2
        else:
            prompt = self.PROMPT1
        self.input.setText(prompt + s)
        n = len(s) + len(prompt)
        self.selection.Min = n
        self.selection.Max = n
        self.input.setSelection(self.selection)
    
    def write_entry(self, entry):
        """ Set current input text. """
        self.set_prompt(self.leading, entry)
    
    def do_enter(self):
        """ Enter pushed in the input edit. """
        s = self.input.getText()
        self.write(s + "\n")
        if s.startswith(self.PROMPT1) or s.startswith(self.PROMPT2):
            s = s[4:]
        self.history.append(s)
        try:
            self.mri.set_mode(False)
            self.replace_out()
            self.leading = self.interpreter.runsource(s)
        except Exception as e:
            print(e)
        self.mri.set_mode(True)
        self.restore_out()
        self.set_prompt(self.leading)
        ui = self.mri.ui
        ui.reload_entry()
        ui.code_updated()
        if ui.tree:
            n = ui.pages.get_history_selected()
            ui.history_change(n)
    
    def do_previous(self):
        """ Get and set previous text from the history. """
        try:
            self.write_entry(self.history.previous())
        except:
            pass
    
    def do_next(self):
        """ Get and set next text from the history. """
        try:
            self.write_entry(self.history.next())
        except:
            pass
    
    def resize(self, width, height):
        """ Resized. """
        input_height = self.INPUT_HEIGHT
        cont = self.frame.getComponentWindow()
        gc = cont.getControl
        gc("rich").setPosSize(0, 0, width, height - input_height, PS_HEIGHT | PS_WIDTH)
        gc("input").setPosSize(0, height - input_height, width, 0, PS_Y | PS_WIDTH)
    
    def _init_ui(self):
        from mytools_Mri.ui.frame import create_window
        WIDTH = self.WIDTH
        HEIGHT = self.HEIGHT
        x = self.X
        y = self.Y
        create = self.create
        
        font_name = self.font_name
        char_size = self.char_size
        parent = self.mri.ui.frame.getContainerWindow()
        toolkit = parent.getToolkit()
    
        frame = create('com.sun.star.frame.Frame')
        window = create_window(toolkit, parent, WC_SIMPLE, "floatingwindow", 
            WA_BORDER | WA_SHOW | WA_SIZEABLE | WA_MOVEABLE | WA_CLOSEABLE, 
            x, y, WIDTH, HEIGHT)
        frame.initialize(window)
        frame.setTitle(self.NAME)
        
        cont = create('com.sun.star.awt.UnoControlContainer')
        cont_model = create('com.sun.star.awt.UnoControlContainerModel')
        cont.setModel(cont_model)
        cont.createPeer(toolkit,window)
        cont.setPosSize(0,0,WIDTH,HEIGHT,PS_POSSIZE)
        window.addWindowListener(WindowListener(self))
        
        frame.setComponent(cont, None)
        frame.addEventListener(ComponentWindowListener(self))
        
        input_model = create("com.sun.star.awt.UnoControlEditModel")
        input = create("com.sun.star.awt.UnoControlEdit")
        input_model.setPropertyValues(
            ("CharHeight", "FontName", "HideInactiveSelection"), (char_size, font_name, False))
        input.setPosSize(0, HEIGHT - self.INPUT_HEIGHT, WIDTH, self.INPUT_HEIGHT, PS_POSSIZE)
        input.setModel(input_model)
        
        edit_model = create("com.sun.star.form.component.RichTextControl")
        edit = create("com.sun.star.form.control.RichTextControl")
        edit_model.setPropertyValue("RichText", True)
        edit_model.setPropertyValues(
            ("Align", "CharFontName", "Border", "HardLineBreaks", "MultiLine", "ReadOnly", "VScroll"), 
            (0, font_name, 0, False, True, True, True))
        edit.setPosSize(0, 0, WIDTH, HEIGHT - self.INPUT_HEIGHT, PS_POSSIZE)
        edit.setModel(edit_model)
        
        input.addKeyListener(KeyListener(self))
        
        cont.addControl("input", input)
        cont.addControl("rich", edit)
        input.setFocus()
        
        self.text = edit_model.getText()
        self.rich = edit
        self.input = input
        self.frame = frame
        self.text.CharFontName = font_name
        self.text.CharHeight = char_size
        self.cursor = self.text.createTextCursor()
        self.cursor.CharFontName = font_name
        self.cursor.CharHeight = char_size
        # ToDo asian fonts
        from mytools_Mri.ui.frame import get_editvscrollbar
        self.scroll = get_editvscrollbar(self.rich)


def console(mri):
    """ Small Console
        Interactive console. """
    console = MRIConsole.get_console(mri)
    console.focus()

