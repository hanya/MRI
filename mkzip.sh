#! /bin/sh

NAME=MRI
VERSION=`cat "VERSION"`

zip -9 -r -n pyc -o files/${NAME}-${VERSION}.oxt \
 META-INF/* *.xcu *.xcs MRI.py description.xml MRILib/* \
 descriptions/* dialogs/* help/* icons/* \
 notices/* web/* pythonpath/mytools_Mri/*.py \
 pythonpath/mytools_Mri/generators/*.py \
 pythonpath/mytools_Mri/ui/*.py macros/*.py \
 mri.uno.rdb \
 LICENSE CHANGES 
