PREFIX  ?= $(HOME)/.local
BINDIR  ?= $(PREFIX)/bin
APPDIR  ?= $(PREFIX)/share/applications
ICONDIR ?= $(PREFIX)/share/icons/hicolor/scalable/apps

# Package version. Bumped with every release alongside VERSION in utc_clock.py
# -- two places, both set to the same string as the v* tag.
VERSION ?= 0.1.0
MAINTAINER ?= xjmzx <admin@jmzx.uk>
DIST_DIR := dist
PKG_NAME := utc-clock_$(VERSION)_all
PKG_DIR  := build/$(PKG_NAME)

# Linux icons crop the grid margin. The masters carry the art in an 824 square
# on a 1024 canvas (Apple's grid, ICONS.md), which fills 80.5% of the tile --
# visibly smaller in the dock than Yaru's own icons, which fill 89%. Cropping to
# this viewBox gets the same 89% out of the master with no re-export. The .icns
# and the .ico keep the full canvas.
LINUX_VIEWBOX ?= 49 49 926 926

DESKTOP_OUT := $(APPDIR)/utc-clock.desktop

.PHONY: help run check install uninstall deb clean-deb version

help:
	@echo "Targets:"
	@echo "  make run        launch UTC Clock without installing"
	@echo "  make check      syntax-check the Python source"
	@echo "  make install    copy script + desktop entry under PREFIX"
	@echo "                  (default PREFIX=$$HOME/.local; sudo PREFIX=/usr/local for system-wide)"
	@echo "  make uninstall  remove what 'install' put down"
	@echo "  make deb        build dist/utc-clock_$(VERSION)_all.deb"
	@echo "  make version V=x.y.z  set the version in both places"

run:
	python3 utc_clock.py

check:
	python3 -m py_compile utc_clock.py
	@if command -v desktop-file-validate >/dev/null 2>&1; then \
		tmp=$$(mktemp --suffix=.desktop); \
		sed -e 's|@BINDIR@|/tmp|g' -e 's|@ICONDIR@|/tmp|g' \
		    utc-clock.desktop.in > $$tmp; \
		desktop-file-validate $$tmp && echo "desktop file ok"; \
		rm -f $$tmp; \
	fi
	@echo "syntax ok"

install:
	install -d $(DESTDIR)$(BINDIR) $(DESTDIR)$(APPDIR) $(DESTDIR)$(ICONDIR)
	install -m 0755 utc_clock.py $(DESTDIR)$(BINDIR)/utc_clock.py
	@# Linux fill: crop the grid margin on the way in (see LINUX_VIEWBOX).
	sed '1s|viewBox="[^"]*"|viewBox="$(LINUX_VIEWBOX)"|' icon.svg > $(DESTDIR)$(ICONDIR)/utc-clock.svg
	chmod 0644 $(DESTDIR)$(ICONDIR)/utc-clock.svg
	@# The .desktop records the FINAL paths, not the staged ones, so a DESTDIR
	@# build still points at $(PREFIX) once dpkg unpacks it.
	sed -e 's|@BINDIR@|$(BINDIR)|g' \
	    -e 's|@ICONDIR@|$(ICONDIR)|g' \
	    utc-clock.desktop.in > $(DESTDIR)$(DESKTOP_OUT)
	chmod 0644 $(DESTDIR)$(DESKTOP_OUT)
	@# Refresh the caches on a real user install only -- skip when staging into
	@# DESTDIR (make deb), where dpkg triggers own them.
	@if [ -z "$(DESTDIR)" ] && command -v update-desktop-database >/dev/null 2>&1; then \
		update-desktop-database $(APPDIR) >/dev/null 2>&1 || true; \
	fi
	@if [ -z "$(DESTDIR)" ] && command -v gtk-update-icon-cache >/dev/null 2>&1; then \
		gtk-update-icon-cache -f -t $(PREFIX)/share/icons/hicolor >/dev/null 2>&1 || true; \
	fi
	@echo "installed to $(PREFIX)"
	@echo "  script  -> $(BINDIR)/utc_clock.py"
	@echo "  desktop -> $(DESKTOP_OUT)"

uninstall:
	rm -f $(BINDIR)/utc_clock.py
	rm -f $(ICONDIR)/utc-clock.svg
	rm -f $(DESKTOP_OUT)
	@if command -v update-desktop-database >/dev/null 2>&1; then \
		update-desktop-database $(APPDIR) >/dev/null 2>&1 || true; \
	fi
	@if command -v gtk-update-icon-cache >/dev/null 2>&1; then \
		gtk-update-icon-cache -f -t $(PREFIX)/share/icons/hicolor >/dev/null 2>&1 || true; \
	fi
	@echo "uninstalled from $(PREFIX)"

# Package the same files `install` lays down into a .deb, by staging them under
# DESTDIR and writing a control file over the top -- the pattern pong and
# bpm-tapper use. Architecture is `all`: a Python script, not a compiled binary.
deb:
	rm -rf $(PKG_DIR)
	mkdir -p $(PKG_DIR)/DEBIAN $(DIST_DIR)
	$(MAKE) install DESTDIR=$(CURDIR)/$(PKG_DIR) PREFIX=/usr
	@printf '%s\n' \
	  "Package: utc-clock" \
	  "Version: $(VERSION)" \
	  "Section: utils" \
	  "Priority: optional" \
	  "Architecture: all" \
	  "Depends: python3 (>= 3.8), python3-tk" \
	  "Maintainer: $(MAINTAINER)" \
	  "Homepage: https://github.com/xjmzx/utc-clock" \
	  "Description: Always-on UTC clock" \
	  " A small always-on clock reading UTC, for work that spans time zones" \
	  " and for anything timestamped in UTC rather than local time." \
	  > $(PKG_DIR)/DEBIAN/control
	dpkg-deb --root-owner-group --build $(PKG_DIR) $(DIST_DIR)/$(PKG_NAME).deb
	@echo ""
	@echo "Built: $(DIST_DIR)/$(PKG_NAME).deb"
	@echo "Install with: sudo apt install ./$(DIST_DIR)/$(PKG_NAME).deb"

clean-deb:
	rm -rf build $(DIST_DIR)

# Keep the two version strings in step: the Makefile's VERSION (which names the
# .deb) and the one the app shows in its own about line.
version:
	@test -n "$(V)" || { echo "usage: make version V=0.1.1" >&2; exit 2; }
	@sed -i.bak -E 's/^VERSION \?= .*/VERSION ?= $(V)/' Makefile && rm -f Makefile.bak
	@sed -i.bak -E 's/^VERSION = ".*"/VERSION = "$(V)"/' utc_clock.py && rm -f utc_clock.py.bak
	@echo "version set to $(V) in both places:"
	@git diff --stat -- Makefile utc_clock.py
