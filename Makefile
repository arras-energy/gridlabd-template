SUFFIXES=

INSTALL=$(shell gridlabd --version=install)
TARGET=$(shell gridlabd template config get DATADIR)
SOURCE=$(subst $(INSTALL)/share/gridlabd/template,.,$(TARGET))

TEMPLATES=ica_analysis
FILES=$(foreach template,$(TEMPLATES),$(wildcard $(SOURCE)/$(template)/*))

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
