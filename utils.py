# -*- coding: utf-8 -*-

"""
***************************************************************************
    utils.py
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
import glob

from PyQt4.QtCore import (QCoreApplication, QSettings, QDir, QFile)

from qgis.utils import iface, loadPlugin, startPlugin, updateAvailablePlugins, home_plugin_path

from pyplugin_installer.installer import QgsPluginInstaller
from pyplugin_installer.qgsplugininstallerinstallingdialog import QgsPluginInstallerInstallingDialog
from pyplugin_installer.installer_data import repositories, plugins
from pyplugin_installer.unzip import unzip

pluginPath = os.path.dirname(__file__)

reposGroup = '/Qgis/plugin-repos'
boundlessRepo = (QCoreApplication.translate('Boundless Central',
                                            'Boundless Plugins Repository'),
                 'https://qgis-ee.boundlessgeo.com/plugins/plugins.xml')


def addBoundlessRepository():
    """Add Boundless plugin repository to list of the available
       plugin repositories if it is not presented here
    """
    if isRepositoryInDirectory():
        return

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


def setRepositoryAuth(authConfigId):
    settings = QSettings()
    settings.beginGroup(reposGroup)
    for repo in settings.childGroups():
        url = settings.value(repo + '/url', '', unicode)
        if url == boundlessRepo[1]:
            settings.setValue(repo + '/authcfg', authConfigId)
    settings.endGroup()


def showPluginManager():
    """Show Plugin Manager with only Boundless plugins repository
    """
    installer = QgsPluginInstaller()

    repos = repositories.all().copy()
    for repo in repos:
        if repos[repo]['url'] == boundlessRepo[1]:
            continue
        else:
            repositories.remove(repo)

    plugins.clearRepoCache()
    installer.showPluginManagerWhenReady(2)
    repositories.load()
    for key in repositories.all():
        repositories.setRepositoryData(key, 'state', 3)


def installAllPlugins():
    """Install all available plugins from Boundless plugins repository
    """
    if isRepositoryInDirectory():
        installAllFromDirectory()
    else:
        installAllFromRepository()


def installAllFromRepository():
    """Install plugins from repository
    """
    installer = QgsPluginInstaller()

    repos = repositories.all().copy()
    for repo in repos:
        if repos[repo]['url'] == boundlessRepo[1]:
            continue
        else:
            repositories.remove(repo)

    installer.fetchAvailablePlugins(False)

    errors = []
    pluginsList = plugins.all().copy()
    for plugin in pluginsList:
        if pluginsList[plugin]['zip_repository'] == boundlessRepo[0]:
            dlg = QgsPluginInstallerInstallingDialog(iface.mainWindow(), plugins.all()[plugin])
            dlg.exec_()
            if dlg.result():
               errors.append(dlg.result())
            else:
                updateAvailablePlugins()
                loadPlugin(plugins.all()[plugin]['id'])
                plugins.getAllInstalled(testLoad=True)
                plugins.rebuild()
                if not plugins.all()[plugin]["error"]:
                    if startPlugin(plugins.all()[plugin]['id']):
                        settings = QSettings()
                        settings.setValue('/PythonPlugins/' + plugins.all()[plugin]['id'], True)

    installer.exportPluginsToManager()
    return errors


def installAllFromDirectory():
    """Install plugins from directory
    """
    errors = []

    installer = QgsPluginInstaller()

    mask = os.path.join(pluginPath, boundlessRepo[1]) + '/*.zip'
    for plugin in glob.glob(mask):
        print plugin

        pluginName = os.path.splitext(os.path.basename(plugin))[0]

        pluginDir = home_plugin_path
        if not QDir(pluginDir).exists():
            QDir().mkpath(pluginDir)

        # If the target directory already exists as a link,
        # remove the link without resolving
        QFile(pluginDir + unicode(QDir.separator()) + pluginName).remove()

        try:
            # Test extraction. If fails, then exception will be raised
            # and no removing occurs
            unzip(unicode(plugin), unicode(pluginDir))
            # Removing old plugin files if exist
            removeDir(QDir.cleanPath(pluginDir + '/' + pluginName))
            # Extract new files
            unzip(unicode(plugin), unicode(pluginDir))
        except:
            errors.append(plugin)

        updateAvailablePlugins()
        loadPlugin(pluginName)
        plugins.getAllInstalled(testLoad=True)
        plugins.rebuild()
        if startPlugin(pluginName):
            settings = QSettings()
            settings.setValue("/PythonPlugins/" + pluginName, True)

    installer.exportPluginsToManager()
    return errors


def isRepositoryInDirectory():
    """Return True if plugin repository is a plain directory
    """
    return os.path.isdir(os.path.join(pluginPath, boundlessRepo[1]))
