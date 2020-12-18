TEMPLATES=$(shell find . -name .index -exec ./index \{\} \;)

all: $(patsubst %,%.zip,$(TEMPLATES))

%.zip: %
	( cd $? ; zip ../$$(basename $@) $$(basename $?)* )
