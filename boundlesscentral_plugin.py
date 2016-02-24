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
from pyplugin_installer.installer import QgsPluginInstaller
from pyplugin_installer.installer_data import repositories

pluginPath = os.path.dirname(__file__)

reposGroup = '/Qgis/plugin-repos'
qgisRepoUrl = 'http://plugins.qgis.org/plugins'
boundlessRepo = (QCoreApplication.translate('Boundless Central',
                                            'Boundless Plugins Repository'),
                 'https://qgis-ee.boundlessgeo.com/plugins/plugins.xml')


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

        self.iface.initializationCompleted.connect(self.showPluginManager)

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
        settings = QSettings()
        settings.beginGroup(reposGroup)
        hasBoundlessRepository = False
        for repo in settings.childGroups():
            url = settings.value(repo + '/url', '', unicode)
            if url == boundlessRepo[1]:
                hasBoundlessRepository = True
        # Boundless repository not found, so we add it to the list
        if not hasBoundlessRepository:
            settings.setValue(boundlessRepo[0] + '/url', boundlessRepo[1])
        settings.endGroup()

    def unload(self):
        pass

    def showPluginManager(self):
        # Show Plugin Manager with Boundless plugins on first run
        settings = QSettings('Boundless', 'BoundlessCentral')
        firstRun = settings.value('firstRun', True, bool)
        settings.setValue('firstRun', False)

        installer = QgsPluginInstaller()

        if firstRun:
            repos = repositories.all().copy()
            for repo in repos:
                if repos[repo]['url'] == boundlessRepo[1]:
                    continue
                else:
                    repositories.remove(repo)

            installer.showPluginManagerWhenReady(2)
            repositories.load()
            for key in repositories.all():
                repositories.setRepositoryData(key, 'state', 3)

    def tr(self, text):
        return QCoreApplication.translate('Boundless Central', text)
