# -*- coding: utf-8 -*-

"""
***************************************************************************
    firstrunwizard.py
    ---------------------
    Date                 : February 2016
    Copyright            : (C) 2016 Boundless, http://boundlessgeo.com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'February 2016'
__copyright__ = '(C) 2016 Boundless, http://boundlessgeo.com'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import httplib
import webbrowser
from urlparse import urlparse

from PyQt4 import uic

from PyQt4.QtGui import (QWizard,
                         QPixmap,
                         QDialog
                        )

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'firstrunwizardbase.ui'))

HELP_URL = "http://github.com/boundlessgeo/qgis-connect-plugin/blob/master/docs/source/usage.rst"

class FirstRunWizard(BASE, WIDGET):
    def __init__(self, parent=None):
        super(FirstRunWizard, self).__init__(parent)
        self.setupUi(self)

        self.setWizardStyle(QWizard.ClassicStyle)

        self.setPixmap(QWizard.LogoPixmap,
            QPixmap(os.path.join(pluginPath, 'icons', 'boundless.png')))
        self.setPixmap(QWizard.WatermarkPixmap,
            QPixmap(os.path.join(pluginPath, 'icons', 'boundless-full.png')))
        self.helpRequested.connect(self.showHelp)

    def showHelp(self):
        p = urlparse(HELP_URL)
        conn = httplib.HTTPConnection(p.netloc)
        conn.request('HEAD', p.path)
        resp = conn.getresponse()
        if resp.status < 400:
            url = HELP_URL
        else:
            url  = "file:///" + os.path.join(os.path.dirname(__file__), "help", "index.html").replace("\\","/")
        webbrowser.open_new(url)
    
    def accept(self):
        QDialog.accept(self)
