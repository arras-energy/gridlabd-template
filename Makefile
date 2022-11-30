# Makefile

.NOTPARALLEL:

help:
	@echo "Syntax: make TARGETS ... [OPTIONS ...]"
	@echo "Targets:"
	@echo "  validate   perform validation tests"
	@echo "Options:"
	@echo "  LIMIT='timeout TIME'"
	@echo "  VERBOSE=yes"
	@echo "  DEBUG=yes"

OPTIONS=
ifeq ($(VERBOSE),yes)
OPTIONS += --verbose
endif
ifeq ($(DEBUG),yes)
OPTIONS += --debug
endif

validate:
	@time -p ./validate.sh

clean:
	@rm -rf test validate.txt validate.tar.gz stderr stdout
