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

from PyQt4.QtCore import (QCoreApplication, QSettings, QLocale, QTranslator, QFileInfo)
from PyQt4.QtGui import (QMessageBox, QAction, QIcon, QFileDialog)

from qgis.core import QGis
from qgis.gui import QgsMessageBar

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

        self.actionRunWizard = QAction(
            self.tr('First Run wizard'), self.iface.mainWindow())
        self.actionRunWizard.setIcon(
            QIcon(os.path.join(pluginPath, 'icons', 'boundless.png')))
        self.actionRunWizard.setWhatsThis(
            self.tr('Run wizard to perform post-installation setup'))
        self.actionRunWizard.setObjectName('actionRunWizard')

        self.actionPluginFromZip = QAction(
            self.tr('Install plugin from ZIP'), self.iface.mainWindow())
        self.actionPluginFromZip.setIcon(
            QIcon(os.path.join(pluginPath, 'icons', 'plugin.png')))
        self.actionPluginFromZip.setWhatsThis(
            self.tr('Install plugin from ZIP file stored on disk'))
        self.actionPluginFromZip.setObjectName('actionPluginFromZip')

        self.iface.addPluginToMenu(
            self.tr('Boundless Central'), self.actionRunWizard)
        self.iface.addPluginToMenu(
            self.tr('Boundless Central'), self.actionPluginFromZip)

        self.actionRunWizard.triggered.connect(self.runWizardAndProcessResults)
        self.actionPluginFromZip.triggered.connect(self.installPlugin)

        # If Boundless repository is a directory, add menu entry
        # to start modified Plugin Manager which works with local repositorys
        if utils.isRepositoryInDirectory():
            self.actionPluginManager = QAction(
                self.tr('Manage plugins (local folder)'), self.iface.mainWindow())
            self.actionPluginManager.setIcon(
                QIcon(os.path.join(pluginPath, 'icons', 'plugin.png')))
            self.actionPluginManager.setWhatsThis(
                self.tr('Manage and install plugins from local repository'))
            self.actionPluginManager.setObjectName('actionPluginManager')

            self.iface.addPluginToMenu(
                self.tr('Boundless Central'), self.actionPluginManager)

            self.actionPluginManager.triggered.connect(self.pluginManagerLocal)


        # Add Boundless plugin repository to list of the available
        # plugin repositories if it is not presented here
        utils.addBoundlessRepository()

    def unload(self):
        self.iface.removePluginMenu(
            self.tr('Boundless Central'), self.actionRunWizard)
        self.iface.removePluginMenu(
            self.tr('Boundless Central'), self.actionPluginFromZip)

        if utils.isRepositoryInDirectory():
            self.iface.removePluginMenu(
                self.tr('Boundless Central'), self.actionPluginManager)

    def startFirstRunWizard(self):
        settings = QSettings('Boundless', 'BoundlessCentral')
        firstRun = settings.value('firstRun', True, bool)
        settings.setValue('firstRun', False)

        if firstRun:
            self.runWizardAndProcessResults()

    def installPlugin(self):
        settings = QSettings('Boundless', 'BoundlessCentral')
        lastDirectory = settings.value('lastPluginDirectory', '.')

        fileName = QFileDialog.getOpenFileName(self.iface.mainWindow(),
                                               self.tr('Open file'),
                                               lastDirectory,
                                               self.tr('Plugin packages (*.zip *.ZIP)'))

        if fileName == '':
            return

        result = utils.installFromZipFile(fileName)
        if result is None:
            self._showMessage(self.tr('Plugin installed successfully'),
                              QgsMessageBar.SUCCESS)
        else:
            self._showMessage(result, QgsMessageBar.WARNING)

        settings.setValue('lastPluginDirectory',
            QFileInfo(fileName).absoluteDir().absolutePath())

    def pluginManagerLocal(self):
        utils.showPluginManager()

    def runWizardAndProcessResults(self):
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

    def _showMessage(self, message, level=QgsMessageBar.INFO):
        self.iface.messageBar().pushMessage(
            message, level, self.iface.messageTimeout())

    def tr(self, text):
        return QCoreApplication.translate('Boundless Central', text)
