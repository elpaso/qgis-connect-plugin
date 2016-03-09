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
import zipfile

from PyQt4.QtCore import (QSettings,
                          QDir,
                          QFile)

from qgis.utils import (iface,
                        loadPlugin,
                        startPlugin,
                        updateAvailablePlugins,
                        home_plugin_path)

from pyplugin_installer.installer import QgsPluginInstaller
from pyplugin_installer.qgsplugininstallerinstallingdialog import QgsPluginInstallerInstallingDialog
from pyplugin_installer.installer_data import (reposGroup,
                                               repositories,
                                               plugins,
                                               removeDir)
from pyplugin_installer.unzip import unzip

from boundlessconnect.plugins import (boundlessRepo,
                                      localPlugins)

pluginPath = os.path.dirname(__file__)


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
    """Add auth to the repository
    """
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
    if isRepositoryInDirectory():
        pluginManageLocalRepo()
    else:
        installer = QgsPluginInstaller()
        installer.showPluginManagerWhenReady(2)


def pluginManageLocalRepo():
    """Open Plugin Manager and list only plugins from local repo
    """
    installer = QgsPluginInstaller()

    repositoryData = {'url': boundlessRepo[1],
                      'authcfg': ''
                     }
    repositories.mRepositories = {boundlessRepo[0]: repositoryData}

    localPlugins.getAllInstalled()
    localPlugins.load()
    localPlugins.rebuild()

    plugins.clearRepoCache()
    plugins.mPlugins = localPlugins.all()

    installer.exportPluginsToManager()
    iface.pluginManagerInterface().showPluginManager(2)


def installAllPlugins():
    """Install all available plugins from Boundless plugins repository
    """
    if isRepositoryInDirectory():
        installAllFromDirectory()
    else:
        installAllFromRepository()


def installAllFromRepository():
    """Install plugins from remote repository
    """
    installer = QgsPluginInstaller()
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
    """Install plugins from directory-based repository
    """
    errors = []

    installer = QgsPluginInstaller()

    mask = os.path.join(pluginPath, boundlessRepo[1]) + '/*.zip'
    for plugin in glob.glob(mask):
        result = installFromZipFile(plugin)
        if result is not None:
            errors.append(result)

    installer.exportPluginsToManager()
    return errors


def installFromZipFile(pluginPath):
    """Install and activate plugin from the specified package
    """
    result = None

    with zipfile.ZipFile(pluginPath, 'r') as zf:
        pluginName = os.path.split(zf.namelist()[0])[0]

    pluginFileName = os.path.splitext(os.path.basename(pluginPath))[0]

    pluginsDirectory = home_plugin_path
    if not QDir(pluginsDirectory).exists():
        QDir().mkpath(pluginsDirectory)

    # If the target directory already exists as a link,
    # remove the link without resolving
    QFile(os.path.join(pluginsDirectory, pluginFileName)).remove()

    try:
        # Test extraction. If fails, then exception will be raised
        # and no removing occurs
        unzip(unicode(pluginPath), unicode(pluginsDirectory))
        # Removing old plugin files if exist
        removeDir(QDir.cleanPath(os.path.join(pluginsDirectory, pluginFileName)))
        # Extract new files
        unzip(unicode(pluginPath), unicode(pluginsDirectory))
    except:
        result = QCoreApplication.translate('BoundlessConnect',
            'Failed to unzip the plugin package\n{}.\nProbably it is broken'.format(pluginPath))

    if result is None:
        updateAvailablePlugins()
        loadPlugin(pluginName)
        plugins.getAllInstalled(testLoad=True)
        plugins.rebuild()
        if startPlugin(pluginName):
            settings = QSettings()
            settings.setValue("/PythonPlugins/" + pluginName, True)

    return result


def isRepositoryInDirectory():
    """Return True if plugin repository is a plain directory
    """
    return os.path.isdir(os.path.join(pluginPath, boundlessRepo[1]))
