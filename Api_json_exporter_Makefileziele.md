Gerne, hier sind die beiden **Makefile**\-Ziele, die Sie benötigen, um den vollständigen Qualitäts-Build (HTML \+ Coverage \+ JSON-API) und den schnellen JSON-Export auszulösen.

Diese Ziele ersetzen Ihre bisherigen Build-Kommandos und nutzen den **api\_json\_exporter.py**\-Hook.

## ---

**🛠️ Makefile-Ziele für Build und Daten-Export**

Stellen Sie sicher, dass Ihre Makefile die Standardvariablen **SPHINXBUILD**, **SOURCEDIR**, und **BUILDDIR** definiert hat.

### **1\. 🚀 api-json: Schneller JSON-API Export**

Dieses Ziel ist für das schnellstmögliche Update der KI-Wissensbasis gedacht. Es verwendet den **dummy**\-Builder, um den build-finished-Hook auszulösen, ohne die zeitaufwendige HTML-Generierung abzuwarten.

Makefile

\# Makefile \- JSON API ONLY  
**.PHONY**: api-json

api-json:  
	@echo "INFO: Starte schlanken Build zum Generieren der Gemini API JSON..."  
	\# Nutzt den schnellsten Builder ('dummy'), um die Sphinx-Umgebung zu befüllen.  
	\$(SPHINXBUILD) -b dummy "\$(SOURCEDIR)" "\$(BUILDDIR)/dummy\_api\_export"  
	@echo "SUCCESS: API JSON erstellt. Datei liegt unter: \$(BUILDDIR)/api-json/gemini\_api\_data.json"

### ---

**2\. 🏆 html-coverage-full: Vollständiger Qualitäts-Build**

Dies ist Ihr primäres Ziel für die Qualitätssicherung und das finale Rendering. Es führt zuerst den Coverage-Check und dann den HTML-Build durch (der automatisch die JSON-API generiert).

Makefile

\# Makefile \- FULL BUILD (HTML \+ COVERAGE \+ JSON API)  
**.PHONY**: html-coverage-full

\# Ziel: Generiert Coverage-Berichte, die vollständige HTML-Doku UND die gemini\_api\_data.json  
html-coverage-full:  
	@echo "INFO: Starte COVERAGE-Check..."  
	\# 1\. Führt den Coverage-Build zuerst aus, um die Berichtsdatei zu erstellen.  
	\$(SPHINXBUILD) -b coverage "\$(SOURCEDIR)" "\$(BUILDDIR)/coverage"  
	  
	@echo "INFO: Starte HTML-Build (inkl. Gemini API JSON Export)..."  
	\# 2\. Führt den HTML-Build aus. Er liest den Coverage-Bericht ein und löst den JSON-Hook aus.  
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"  
	  
	@echo "SUCCESS: Build abgeschlossen."  
	@echo "Berichte liegen unter: $(BUILDDIR)/coverage"  
	@echo "HTML-Doku liegt unter: $(BUILDDIR)/html"  
	@echo "JSON-API liegt unter: $(BUILDDIR)/api-json/gemini\_api\_data.json"

Mit diesen Zielen ist Ihr Build-Prozess nun **vollständig optimiert** für Ihren Qualitäts-Workflow und die KI-Integration\!