UNAME := $(shell uname)

PREFIX=	/usr
PREFIX=	$(DESTDIR)/usr
BIN=	$(PREFIX)/bin
MANDIR=$(PREFIX)/share/man

SRC=	icc2ps.c xgetopt.c
LIB=	-llcms
CFLAGS+=	-O3

# _XOPEN_SOURCE is required for swab() but undefines strcasecmp(), so add _GNU_SOURCE as well:
CFLAGS+= -D_XOPEN_SOURCE -D_GNU_SOURCE

INSTALL=install
ifeq ($(UNAME),SunOS)
    INSTALL=/usr/ucb/install
    CC=gcc
endif

.SUFFIXES: .1 .1in

all: foo2zjs-icc2ps man

foo2zjs-icc2ps: $(SRC) $(LIB)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SRC) $(LIB) -lm -o $@ $(LDFLAGS)

install: all
	$(INSTALL) -c foo2zjs-icc2ps $(BIN)

man:	foo2zjs-icc2ps.1

.1in.1: 
	-rm -f $*.1
	MODver=$(VERSION); \
	../includer-man -v DEF1=$(OLDGROFF) $*.1in | sed > $*.1 \
	    -e "s@\$${URLOAK}@$(URLOAK)@" \
	    -e "s@\$${URLZJS}@$(URLZJS)@" \
	    -e "s@\$${URLHP}@$(URLHP)@" \
	    -e "s@\$${URLXQX}@$(URLXQX)@" \
	    -e "s@\$${URLLAVA}@$(URLLAVA)@" \
	    -e "s@\$${URLQPDL}@$(URLQPDL)@" \
	    -e "s@\$${URLSLX}@$(URLSLX)@" \
	    -e "s@\$${URLHC}@$(URLHC)@" \
	    -e "s/\$${MODver}/$$MODver/"
	chmod a-w $*.1

install-man: man
	$(INSTALL) -d -m 755 $(MANDIR)
	$(INSTALL) -d -m 755 $(MANDIR)/man1/
	$(INSTALL) -c -m 644 foo2zjs-icc2ps.1 $(MANDIR)/man1/

clean:
	rm -f *.o foo2zjs-icc2ps *.1

foo2zjs-icc2ps: icc34.h

regress: all
	@./foo2zjs-icc2ps a b 2>&1 | grep "little cms P"
	@for i in ../icm/*.icm; do \
	    b=`basename $$i`; \
	    ./foo2zjs-icc2ps -o $$i -t0 | grep -v Created >$$b.ps; \
	    md5sum $$b.ps; \
	done
	@rm -f *icm.ps
