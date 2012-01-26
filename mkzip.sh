#! /bin/sh

NAME=MRI
VERSION=1.1.0

zip -9 -r -n pyc -o ${NAME}-${VERSION}.oxt \
 META-INF/* *.xcu *.xcs *.py description.xml MRILib/* \
 descriptions/* dialogs/* help/* icons/* \
 notices/* web/* pythonpath/mytools_Mri/*.py \
 pythonpath/mytools_Mri/generators/*.py \
 pythonpath/mytools_Mri/ui/*.py macros/*.py \
 LICENSE CHANGES 
