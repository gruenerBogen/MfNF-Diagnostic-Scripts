GZIP=gzip -f
ASCIIDOC=asciidoctor -b manpage

MANPAGES=bad_finder.1.gz tex_macro_finder.1.gz

.PHONY: man
man: $(MANPAGES)

%.gz : %
	$(GZIP) $<

%.1: %.1.adoc
	$(ASCIIDOC) -b manpage -d manpage $<

%.5: %.5.adoc
	$(ASCIIDOC) -b manpage -d manpage $<
