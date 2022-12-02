# Makefile

.NOTPARALLEL:

help:
	@echo "Syntax: make TARGETS ... [OPTIONS ...]"
	@echo "Targets:"
	@echo "  clean      cleanup old test results"
	@echo "  models     update test models"
	@echo "  report     update validation data report"
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
	@git submodule sync
	@git submodule update --init --recursive --force --checkout --remote

validate:
	@./validate.sh $(OPTIONS)

clean:
	@rm -rf test validate.txt validate.tar.gz stderr stdout

report: data report/Validation_Report.pdf

data:
	python3 report/make_table.py US/CA/SLAC/loadfactor/autotest/models/gridlabd-4/*/*/loads.csv > report/loadfactor_loads.tex
	python3 report/make_table.py US/CA/SLAC/ica_analysis/autotest/models/gridlabd-4/*/*/solar_capacity.csv > report/ica_analysis_solar_capacity.tex
	python3 report/make_table.py US/CA/SLAC/ica_analysis/autotest/models/gridlabd-4/*/*/violation_details.csv > report/ica_analysis_violation_details.tex
	touch report/Validation_report.tex

%.pdf: %.tex
	(cd $(shell dirname $?); pdflatex -halt-on-error $(shell basename $?)) 1>$?.out 2>$?.err
	(cd $(shell dirname $?); pdflatex -halt-on-error $(shell basename $?)) 1>>$?.out 2>>$?.err
