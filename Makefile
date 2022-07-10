SUFFIXES=

INSTALL=$(shell gridlabd --version=install)
TARGET=$(shell gridlabd template config get DATADIR)
SOURCE=$(subst $(INSTALL)/share/gridlabd/template,.,$(TARGET))

TEMPLATES=ica_analysis
FILES=$(foreach template,$(TEMPLATES),$(wildcard $(SOURCE)/$(template)/*))

help:

build:
	./compile
	
install: $(subst ./,$(INSTALL)/share/gridlabd/template/,$(FILES))
	@echo Installed $(TEMPLATES) ok
# 	@echo TARGET=$(TARGET)
# 	@echo INSTALL=$(INSTALL)
# 	@echo SOURCE=$(SOURCE)
# 	@echo TEMPLATES=$(TEMPLATES)
# 	@echo FILES=$(FILES)

$(TARGET)/%: $(SOURCE)/%
	@mkdir -p $(dir $@) && cp -R $< $@

#!/bin/bash

COUNTRY=US
STATE=CA
ORG=SLAC
TEMPLATES=$(shell find $(COUNTRY)/$(STATE)/$(ORG) -type d -print -prune)
TESTDIR=autotest/models/gridlabd-4
TESTFILES=$(foreach GLM,$(shell find $(TESTDIR) -name '*.glm' -print),$(TESTDIR)/$(GLM))

validate: $(TESTFILES)

$(TESTDIR)/%.glm: %.glm
	$(foreach TEMPLATE,$(TEMPLATES),. validate.sh "$<" "$(TEMPLATE)")
