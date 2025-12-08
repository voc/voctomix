BLUEPRINTS := $(shell git ls-files | grep "\.blp$$" | sed 's/\.blp$$/.ui/')

.PHONY: blueprint
blueprint: $(BLUEPRINTS)

%.ui: %.blp
	blueprint-compiler compile --output $@ $<
