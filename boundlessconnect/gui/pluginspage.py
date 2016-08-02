# -*- coding: utf-8 -*-

"""
***************************************************************************
    pluginspage.py
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

from PyQt4 import uic
from PyQt4.QtCore import QSettings, QFileInfo
from PyQt4.QtGui import QFileDialog

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'pluginspagebase.ui'))


class PluginsPage(BASE, WIDGET):
    def __init__(self, parent=None):
        super(PluginsPage, self).__init__(parent)
        self.setupUi(self)

        self.svgLogo.load(os.path.join(pluginPath, 'icons', 'boundless-logo.svg'))

        self.rbInstallFromZip.toggled.connect(self.toggleSelector)
        self.btnBrowse.clicked.connect(self.selectFile)

        self.toggleSelector(False)

    def toggleSelector(self, checked):
        self.leFileName.setEnabled(checked)
        self.btnBrowse.setEnabled(checked)

    def selectFile(self):
        settings = QSettings('Boundless', 'BoundlessConnect')
        lastDirectory = settings.value('lastPluginDirectory', '.')

        fileName = QFileDialog.getOpenFileName(self,
                                               self.tr('Open file'),
                                               lastDirectory,
                                               self.tr('Plugin packages (*.zip *.ZIP)'))

        if fileName == '':
            return

        self.leFileName.setText(fileName)

        settings.setValue('lastPluginDirectory',
            QFileInfo(fileName).absoluteDir().absolutePath())
