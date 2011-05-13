# PURPOSE: Makefile Demo Application of Quex
#
# ABSOLUTELY NO WARRANTY
#_______________________________________________________________________________
.PHONY: clean

ifndef QUEX_PATH
    $(error The environment variable QUEX_PATH is not defined!)
endif

include $(QUEX_PATH)/quex/code_base/core.mkd

# (*) SETUP ____________________________________________________________________
SOURCES  = tiny_lexer  tiny_lexer.cpp  tiny_lexer-token_ids  \
		   tiny_lexer-configuration
WSOURCES = tiny_wlexer tiny_wlexer.cpp tiny_wlexer-token_ids \
		   tiny_wlexer-configuration
# (*) COMPILER SETTINGS ________________________________________________________
#     (change COMPILER to whatever you use as compiler on the command line,
#      e.g. "make COMPILER=icpc" will use intel's c++ compiler)
ifdef ASSERTS_ENABLED_F
	CCFLAG_ASSERTS=# By default asserts are enabled
else 
	CCFLAG_ASSERTS=-DQUEX_OPTION_ASSERTS_DISABLED
endif
COMPILER = g++ -ggdb -Wall -pedantic 
CC = $(COMPILER) -c -I./ -I$(QUEX_PATH) $(CCFLAG_ASSERTS) \
	 # -DQUEX_OPTION_ASSERTS_DISABLED
	 # -DQUEX_OPTION_ASSERTS_WARNING_MESSAGE_DISABLED \
		 
LD = $(COMPILER) 

# (*) RULES ____________________________________________________________________
all: lexer wlexer

# -- char application
lexer: lexer.o tiny_lexer.o 
	$(LD) -o $@  lexer.o tiny_lexer.o 
          
stdinlexer: stdinlexer.o tiny_lexer.o 
	$(LD) -o $@  stdinlexer.o tiny_lexer.o 
          
$(SOURCES): simple.qx $(QUEX_CORE)
	quex -i simple.qx --engine tiny_lexer --token-policy single

# -- wchar_t application
wlexer: wlexer.o tiny_wlexer.o 
	$(LD) -o $@  wlexer.o tiny_wlexer.o 
          
$(WSOURCES): simple.qx $(QUEX_CORE)
	quex -i simple.qx --engine tiny_wlexer --bet wchar_t --token-policy single

# -- The general way to get .o from .cpp
%.o: %.cpp $(SOURCES) $(WSOURCES)
	$(CC) $< -o $@ 

# (*) HELPERS __________________________________________________________________
clean:	
	touch simple.qx
	rm -f wchar_t-example.txt # created by wlexer.cpp
	rm -f $(SOURCES)
	rm -f $(WSOURCES)
	rm -f *.o
	rm -f lexer stdinlexer wlexer
	rm -f lexer-token stdinlexer-token wlexer-token
	rm -f tiny_lexer-token tiny_wlexer-token
	rm -f *.bak
