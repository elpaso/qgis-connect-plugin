# -*- coding: utf-8 -*-

"""
***************************************************************************
    credentialspage.py
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

from PyQt4.QtCore import Qt, QSettings
from PyQt4.QtGui import QLineEdit, QMessageBox

from qgis.core import QgsAuthManager, QgsAuthMethodConfig

from pyplugin_installer.installer_data import reposGroup

from boundlessconnect import utils
from boundlessconnect.plugins import boundlessRepoName, defaultRepoUrl

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'credentialspagebase.ui'))


class CredentialsPage(BASE, WIDGET):
    def __init__(self, parent=None):
        super(CredentialsPage, self).__init__(parent)
        self.setupUi(self)

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
            self.btnSave.setText(self.tr('Update'))

        self.chkShowPassword.stateChanged.connect(self.togglePasswordVisibility)
        self.btnSave.clicked.connect(self.saveCredentials)

    def togglePasswordVisibility(self, state):
        if state == Qt.Checked:
            self.lePassword.setEchoMode(QLineEdit.Normal)
        else:
            self.lePassword.setEchoMode(QLineEdit.Password)

    def saveCredentials(self):
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
                self.btnSave.setText(self.tr('Update'))
                QMessageBox.information(self, self.tr('Saved!'), self.tr('Credentials saved'))
            else:
                QMessageBox.information(self, self.tr('Error!'), self.tr('Unable to save credentials'))
        else:
            authConfig = QgsAuthMethodConfig()
            QgsAuthManager.instance().loadAuthenticationConfig(self.authId, authConfig, True)
            authConfig.setConfig('username', self.leLogin.text())
            authConfig.setConfig('password', self.lePassword.text())
            QgsAuthManager.instance().updateAuthenticationConfig(authConfig)
