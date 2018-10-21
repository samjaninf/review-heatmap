# -*- coding: utf-8 -*-

"""
This file is part of the Review Heatmap add-on for Anki

WebView link handlers and associated components

Copyright: (c) 2016-2018 Glutanimate <https://glutanimate.com/>
License: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import aqt

from aqt.qt import QWidget

from aqt import mw
from aqt.overview import Overview
from aqt.deckbrowser import DeckBrowser
from aqt.stats import DeckStats

from anki.hooks import wrap
from anki.find import Finder

from .libaddon.platform import ANKI21

from .gui.options import invokeOptionsDialog
from .gui.contrib import invokeContributionsDialog
from .gui.extra import invokeSnanki

from .config import config, heatmap_colors, heatmap_modes

__all__ = ["heatmapLinkHandler", "invokeBrowser", "findSeenOn",
           "addSeenFinder"]

# Link handler
######################################################################

def heatmapLinkHandler(self, url, _old=None):
    """Launches Browser when clicking on a graph subdomain"""
    if ":" in url:
        (cmd, arg) = url.split(":", 1)
    else:
        cmd, arg = url, ""
    if not cmd or cmd not in ("revhm_browse", "revhm_opts",
                              "revhm_contrib", "revhm_modeswitch",
                              "revhm_themeswitch", "revhm_snanki"):
        return None if not _old else _old(self, url)

    if isinstance(self, QWidget):
        parent = self
    else:
        parent = mw

    if cmd == "revhm_opts":
        invokeOptionsDialog(parent)
    elif cmd == "revhm_contrib":
        invokeContributionsDialog(parent)
    elif cmd == "revhm_browse":
        invokeBrowser(arg)
    elif cmd == "revhm_modeswitch":
        cycleHmModes()
    elif cmd == "revhm_themeswitch":
        cycleHmThemes()
    elif cmd == "revhm_snanki":
        invokeSnanki(parent=parent)
        
def cycleHmThemes():
    themes = list(heatmap_colors.keys())
    cur_idx = themes.index(config["synced"]["colors"])
    new_idx = (cur_idx + 1) % len(themes)
    config["synced"]["colors"] = themes[new_idx]
    config.save()

def cycleHmModes():
    modes = list(heatmap_modes.keys())
    cur_idx = modes.index(config["synced"]["mode"])
    new_idx = (cur_idx + 1) % len(modes)
    config["synced"]["mode"] = modes[new_idx]
    config.save()

def invokeBrowser(search):
    browser = aqt.dialogs.open("Browser", mw)
    browser.form.searchEdit.lineEdit().setText(search)
    if ANKI21:
        browser.onSearchActivated()
    else:
        browser.onSearch()

# Finder extensions
######################################################################

def findSeenOn(self, val):
    """Find cards seen on a specific day"""
    # self is find.Finder
    try:
        days = int(val[0])
    except ValueError:
        return
    days = max(days, 0)
    # upper cutoff set to dayCutOff x days ago
    cutoff2 = (self.col.sched.dayCutoff - 86400*days)*1000
    # lower cutoff set to 24 hours before upper cutoff
    cutoff1 = cutoff2 - 86400000
    # select cards that were seen at some point in that day
    # empty results expected when cards have been deleted since
    return ("c.id in (select cid from revlog where id between %d and %d)"
            % (cutoff1, cutoff2))

def addSeenFinder(self, col):
    """Add custom finder to search dictionary"""
    self.search["seen"] = self.findSeenOn


# Hooks
######################################################################


def initializeLinks():
    Overview._linkHandler = wrap(Overview._linkHandler, heatmapLinkHandler,
                                 "around")
    DeckBrowser._linkHandler = wrap(
        DeckBrowser._linkHandler, heatmapLinkHandler, "around")
    DeckStats._linkHandler = heatmapLinkHandler
    Finder.findSeenOn = findSeenOn
    Finder.__init__ = wrap(Finder.__init__, addSeenFinder, "after")
