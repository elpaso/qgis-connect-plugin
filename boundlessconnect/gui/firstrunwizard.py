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

from PyQt4 import uic
from PyQt4.QtCore import QUrl
from PyQt4.QtGui import (QWizard,
                         QPixmap,
                         QDialog,
                         QDesktopServices,
                         QMessageBox
                        )

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'firstrunwizardbase.ui'))

HELP_URL = "https://connect.boundlessgeo.com/docs/desktop/plugins/connect/usage.html#first-run-wizard"

class FirstRunWizard(BASE, WIDGET):
    def __init__(self, parent=None):
        super(FirstRunWizard, self).__init__(parent)
        self.setupUi(self)

        self.setWizardStyle(QWizard.ClassicStyle)

        self.helpRequested.connect(self.showHelp)

    def showHelp(self):
        if not QDesktopServices.openUrl(QUrl(HELP_URL)):
            QMessageBox.warning(self, self.tr('Error'), self.tr('Can not open help URL in browser'))

    def accept(self):
        QDialog.accept(self)
