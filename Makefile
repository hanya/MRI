
# requires SDK settigns
# compiles idl files into rdb file

RDB_NAME=mri.uno.rdb
IDL_FILE=./idl/mytools/Mri.idl
URD_FILE=./idl/Mri.urd


.PHONY : all
all : $(RDB_NAME)

include $(OO_SDK_HOME)/settings/std.mk

$(URD_FILE) : $(IDL_FILE)
	$(IDLC) -C -I. -I$(OO_SDK_HOME)/idl -O./idl $(IDL_FILE)


$(RDB_NAME) : $(URD_FILE)
	$(REGMERGE) $(RDB_NAME) /UCR $(URD_FILE)

