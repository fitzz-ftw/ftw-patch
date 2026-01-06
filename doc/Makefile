# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
AUTOSUMMERYDIR = $(SOURCEDIR)/devel/api
PYTHON=python

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile htmlpure html coverage doctest test

htmlpure:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

html: 
	@$(SPHINXBUILD) -M coverage "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	@$(SPHINXBUILD) -M dirhtml "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

coverage:
	@$(SPHINXBUILD) -M coverage "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: api-json

api-json:  
	@echo "INFO: Starte schlanken Build zum Generieren der Gemini API JSON..."  
	# Nutzt den schnellsten Builder ('dummy'), um die Sphinx-Umgebung zu befüllen.  
	$(SPHINXBUILD) -b dummy "$(SOURCEDIR)" "$(BUILDDIR)/dummy_api_export"  
	@echo "SUCCESS: API JSON erstellt. Datei liegt unter: \$(BUILDDIR)/api-json/gemini_api_data.json"


.PHONY: html-coverage-full

# Ziel: Generiert Coverage-Berichte, die vollständige HTML-Doku UND die gemini\_api\_data.json  
html-coverage-full:  
	@echo "INFO: Starte COVERAGE-Check..."  
	# 1. Führt den Coverage-Build zuerst aus, um die Berichtsdatei zu erstellen.  
	$(SPHINXBUILD) -b coverage "$(SOURCEDIR)" "$(BUILDDIR)/coverage"  
	  
	@echo "INFO: Starte HTML-Build (inkl. Gemini API JSON Export)..."  
	# 2. Führt den HTML-Build aus. Er liest den Coverage-Bericht ein und 
	# löst den JSON-Hook aus.  
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"  
	  
	@echo "SUCCESS: Build abgeschlossen."  
	@echo "Berichte liegen unter: $(BUILDDIR)/coverage"  
	@echo "HTML-Doku liegt unter: $(BUILDDIR)/html"  
	@echo "JSON-API liegt unter: $(BUILDDIR)/api-json/gemini_api_data.json"


.PHONY: clean
clean:
	rm -r $(BUILDDIR)
	rm $(AUTOSUMMERYDIR)/*.rst




# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
