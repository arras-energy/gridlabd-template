# Makefile

.NOTPARALLEL:

help:
	@echo "Syntax: make TARGETS ... [OPTIONS ...]"
	@echo "Targets:"
	@echo "  help       display this help information"
	@echo "  validate   perform validation tests"
	@echo "Options:"
	@echo "  VERBOSE=yes"
	@echo "  DEBUG=yes"

OPTIONS=
ifeq ($(VERBOSE),yes)
OPTIONS+=--verbose
endif
ifeq ($(DEBUG),yes)
OPTIONS+=--debug
endif

models:
	git submodule sync
	git submodule update --init --recursive --force --checkout --remote

validate:
	@./validate.sh $(OPTIONS)

clean:
	@rm -rf test validate.txt validate.tar.gz stderr stdout
