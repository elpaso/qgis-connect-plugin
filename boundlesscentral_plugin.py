# -*- coding: utf-8 -*-

"""
***************************************************************************
    boundlesscentral_plugin.py
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

from PyQt4.QtCore import (QCoreApplication, QSettings, QLocale, QTranslator)
from PyQt4.QtGui import QMessageBox

from qgis.core import QGis

from boundlesscentral.gui.firstrunwizard import FirstRunWizard
from boundlesscentral import utils

pluginPath = os.path.dirname(__file__)


class BoundlessCentralPlugin:
    def __init__(self, iface):
        self.iface = iface

        self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)

        overrideLocale = QSettings().value('locale/overrideFlag', False, bool)
        if not overrideLocale:
            locale = QLocale.system().name()[:2]
        else:
            locale = QSettings().value('locale/userLocale', '')

        qmPath = '{}/i18n/boundlesscentral_{}.qm'.format(pluginPath, locale)

        if os.path.exists(qmPath):
            self.translator = QTranslator()
            self.translator.load(qmPath)
            QCoreApplication.installTranslator(self.translator)

        self.iface.initializationCompleted.connect(self.startFirstRunWizard)

    def initGui(self):
        if int(self.qgsVersion) < 20800:
            qgisVersion = '{}.{}.{}'.format(
                self.qgsVersion[0], self.qgsVersion[2], self.qgsVersion[3])
            QMessageBox.warning(
                self.iface.mainWindow(),
                self.tr('Boundless Central'),
                self.tr('QGIS {} detected.\nThis version of  Boundless '
                        'Central plugin requires at least QGIS 2.8.0. '
                        'Plugin will not be enabled.'.format(qgisVersion)))
            return None

        # Add Boundless plugin repository to list of the available
        # plugin repositories if it is not presented here
        utils.addBoundlessRepository()

    def unload(self):
        pass

    def startFirstRunWizard(self):
        settings = QSettings('Boundless', 'BoundlessCentral')
        firstRun = settings.value('firstRun', True, bool)
        settings.setValue('firstRun', False)

        if firstRun:
            wzrd = FirstRunWizard()
            if wzrd.exec_():
                authId = wzrd.mPageCredentials.mAuthSelector.configId()
                installAll = wzrd.mPagePlugins.rbAutoInstall.isChecked()

                if authId != '':
                    utils.setRepositoryAuth(authId)

                if installAll:
                    utils.installAllPlugins()
                else:
                    utils.showPluginManager()

    def tr(self, text):
        return QCoreApplication.translate('Boundless Central', text)

