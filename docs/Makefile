# Minimal Sphinx makefile — build the docs with `make -C docs html`.

SPHINXBUILD   ?= ../.venv/bin/sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: html clean

html:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"

clean:
	rm -rf "$(BUILDDIR)"
