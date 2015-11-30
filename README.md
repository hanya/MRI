
MRI
====
MRI is an object introspection tool for OpenOffice.org. 

## Requirements
* Version 1.1.3 supports OpenOffice.org version 3.0 - 3.3.
* Version 1.2.X supports Apache OpenOffice 3.4 - 4.0 or later.
* MRI is written in Python, which is required to execute PyUNO bridge 
installation.

## Packaging
Compiling is not required but files have to be packed into 
OXT package. zip command is required to make package.

```
 > mkzip.sh
```

Help files are converted from Markdown syntax to xhp format. 
Mikasa is used for this task.

```
 > python mikasa.py -i mytools.mri
```
