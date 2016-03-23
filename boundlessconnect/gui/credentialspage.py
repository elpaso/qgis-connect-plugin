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

from PyQt4.QtCore import QSettings

from pyplugin_installer.installer_data import reposGroup

from boundlessconnect import utils
from boundlessconnect.plugins import boundlessRepo

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'credentialspagebase.ui'))


class CredentialsPage(BASE, WIDGET):
    def __init__(self, parent=None):
        super(CredentialsPage, self).__init__(parent)
        self.setupUi(self)

        settings = QSettings()
        settings.beginGroup(reposGroup)
        authCfg = settings.value(boundlessRepo[0] + '/authcfg', '', unicode)
        settings.endGroup()

        self.mAuthSelector.setConfigId(authCfg)

        self.mAuthSelector.selectedConfigIdChanged.connect(self.updateAuthCfg)

    def updateAuthCfg(self, authCfgId):
        utils.setRepositoryAuth(authCfgId)
