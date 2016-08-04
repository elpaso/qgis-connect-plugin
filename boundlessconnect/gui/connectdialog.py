# -*- coding: utf-8 -*-

"""
***************************************************************************
    connectdialog.py
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
from PyQt4.QtCore import QUrl, QSettings
from PyQt4.QtGui import (QDialog,
                         QDesktopServices,
                         QMessageBox
                        )

from qgis.core import QgsAuthManager, QgsAuthMethodConfig

from pyplugin_installer.installer_data import reposGroup

from boundlessconnect import utils
from boundlessconnect.plugins import boundlessRepoName

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'connectdialogbase.ui'))

HELP_URL = "https://connect.boundlessgeo.com/docs/desktop/plugins/connect/usage.html#first-run-wizard"

class ConnectDialog(BASE, WIDGET):
    def __init__(self, parent=None):
        super(ConnectDialog, self).__init__(parent)
        self.setupUi(self)

        self.svgLogo.load(os.path.join(pluginPath, 'icons', 'boundless-logo.svg'))

        settings = QSettings()
        settings.beginGroup(reposGroup)
        self.authId = settings.value(boundlessRepoName + '/authcfg', '', unicode)
        settings.endGroup()

        if self.authId != '':
            authConfig = QgsAuthMethodConfig()
            QgsAuthManager.instance().loadAuthenticationConfig(self.authId, authConfig, True)
            username = authConfig.config('username')
            password = authConfig.config('password')
            self.leLogin.setText(username)
            self.lePassword.setText(password)

        self.buttonBox.helpRequested.connect(self.showHelp)

    def showHelp(self):
        if not QDesktopServices.openUrl(QUrl(HELP_URL)):
            QMessageBox.warning(self, self.tr('Error'), self.tr('Can not open help URL in browser'))

    def accept(self):
        if self.leLogin.text() == '' or self.lePassword.text() == '':
            QDialog.accept(self)

        if self.authId == '':
            authConfig = QgsAuthMethodConfig('Basic')
            authId = QgsAuthManager.instance().uniqueConfigId()
            authConfig.setId(authId)
            authConfig.setConfig('username', self.leLogin.text())
            authConfig.setConfig('password', self.lePassword.text())
            authConfig.setName('Boundless Connect Portal')

            settings = QSettings('Boundless', 'BoundlessConnect')
            authConfig.setUri(settings.value('repoUrl', '', unicode))

            if QgsAuthManager.instance().storeAuthenticationConfig(authConfig):
                utils.setRepositoryAuth(authId)
            else:
                QMessageBox.information(self, self.tr('Error!'), self.tr('Unable to save credentials'))
        else:
            authConfig = QgsAuthMethodConfig()
            QgsAuthManager.instance().loadAuthenticationConfig(self.authId, authConfig, True)
            authConfig.setConfig('username', self.leLogin.text())
            authConfig.setConfig('password', self.lePassword.text())
            QgsAuthManager.instance().updateAuthenticationConfig(authConfig)

        QDialog.accept(self)
