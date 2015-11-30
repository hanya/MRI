
# Bundled Macros

After version 1.0.0, MRI has macro support and it has bundled macros which can be executed though Macros - bundle.py entry in the main menu. The module of bundled macros includes not only used as macro but some macros which is used in the main menu.

This document describes about each bundled macros which can be executed in macro menu.

## Inspect Elements of Index Container
Inspects all elements of the current index container if com.sun.star.container.XIndexAccess interface is supported.

## Inspect Elements of Named Container
Inspects all elements of the current named container if com.sun.star.container.XNameAccess interface is supported.

## Inspect Elements of Enumeration Container
Inspects all elements of the current enumeration container. The target have to be supported by com.sun.star.container.XEnumerationAccess or com.sun.star.container.XEnumeration interface.

## Inspect Elements of Sequence
Inspects all element of the current one-dimensional sequence.

## Inspect Accessible Children
Try to inspect all children in the accessible hierarchy. This macro may freeze your office.

## Inspect Data Sequence of Chart
Execute with chart document as a target which supports com.sun.star.chart.ChartDocument service. All data sequences will be inspected.

## Diff
Compare current target with another one which is take from another MRI instance.

## Diff in History
Compare current target with another one which is chosen in the history.

## Modifiable Configuration
The configuration target created with Targets - Configuration entry of the main menu is not modifiable. But one which is created by this entry is modifiable and updatable.

## Import Macros
Users can keep their own macro files in the directory specified by the configuration of MRI. This macro entry allows you to distribute your macro for other MRI users. 

Importer allows to load py, zip, tar.gz and tar.bz2 files and extract files into your macros directory.

Make a copy of your macro and make an archive for macro package in zip, tar.gz or tar.bz2 format. If you put README file into your archive, it is shown during deployment of your package.

## Reload Property Values
Force to reload property values on current inspected target. If you change the property value of the target from somewhere, choose this entry to update property values.

## Reload Macros Menu
Regenerate macros menu. Macros menu is statically created and it does not check file modification, so please choose this entry to reload macro file. This entry is useful for macro editors.

## Reload Current Code Generator
Reload generator module which is used to generate code now. This entry allows you to reload modification on generator code, is useful for editors of code generators.

## Small Console
This macro allows you to do something interactively with MRI or targets in Python. 

Following variables are prepared to access something.

* console: console itself.
* ctx: component context.
* create: This is a function which takes one string as service name to instantiate. Additionally, tuple of initialize arguments can be passed.
* uno: uno.py
* mri: MRI instance.
* \_\_name__: \_\_console\_\_
* \_\_doc\_\_: text for console.help()

The mri variable holds current target in its current instance variable. You can access it as follows: 

```
>>> obj = mri.current.target
```

The target instance variable keeps real target.
