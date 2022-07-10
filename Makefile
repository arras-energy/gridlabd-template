# Makefile

.NOTPARALLEL:

help:
	@echo "Syntax: make TARGETS ... [OPTIONS ...]"
	@echo "Targets:"
	@echo "  validate   perform validation tests"
	@echo "Options:"
	@echo "  LIMIT='timeout TIME'"
	@echo "  VERBOSE=yes"

OPTIONS=
ifeq ($(VERBOSE),yes)
OPTIONS += --debug
endif

TESTDIR=autotest/models/gridlabd-4
TESTFILES=$(foreach GLM,$(shell find $(TESTDIR) -name '*.glm' -print),$(TESTDIR)/$(GLM))

validate: clean models $(TESTFILES)
	@cat validate.txt

models:
	@git submodule sync
	@git submodule update --init --recursive

clean:
	@rm -rf test validate.txt

$(TESTDIR)/%.glm: %.glm
	@$(foreach TEMPLATE,$(foreach ORG,$(shell grep -v ^\# .orgs),$(shell find $(ORG) -type d -print -prune)),$(LIMIT) ./validate.sh $(OPTIONS) "$<" "$(TEMPLATE)") >> validate.txt
