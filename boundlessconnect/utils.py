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
import ConfigParser

from PyQt4.QtCore import (QSettings,
                          QDir,
                          QFile)

from qgis.core import QgsApplication
from qgis.utils import (iface,
                        loadPlugin,
                        startPlugin,
                        reloadPlugin,
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
                                      firstRunPluginsPath,
                                      deprecatedPlugins,
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
        settings.setValue(boundlessRepo[0] + '/authcfg', '')
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
    """Show Plugin Manager with all plugins. This includes plugins from
    Official QGIS plugins repository and plguins from Boundless plugins
    repository (local or remote)
    """
    installer = QgsPluginInstaller()

    initPluginManager(installer)

    iface.pluginManagerInterface().showPluginManager(2)
    # Restore repositories, as we don't want to keep local repo in cache
    repositories.load()


def initPluginManager(installer):
    """Open Plugin Manager and list only plugins from local repo
    """
    # Load plugins from remote repositories and export repositories
    # to Plugin Manager
    installer.fetchAvailablePlugins(reloadMode=False)
    installer.exportRepositoriesToManager()

    # If Boundless repository is a local directory, add plugins
    # from it to Plugin Manager
    if isRepositoryInDirectory():
        repositoryData = {'url': boundlessRepo[1],
                          'authcfg': ''
                         }
        repositories.mRepositories.update({boundlessRepo[0]: repositoryData})

        localPlugins.getAllInstalled()
        localPlugins.load()
        localPlugins.rebuild()

        plugins.mPlugins.update(localPlugins.all())

    # Export all plugins to Plugin Manager
    installer.exportPluginsToManager()


def installAllPlugins():
    """Install all available plugins from Boundless plugins repository
    """
    if isRepositoryInDirectory():
        pluginsDirectory = os.path.join(pluginPath, boundlessRepo[1])
        installAllFromDirectory(pluginsDirectory)
    else:
        installAllFromRepository()


def installAllFromRepository():
    """Install Boundless plugins from remote repository
    """
    installer = QgsPluginInstaller()
    installer.fetchAvailablePlugins(False)

    errors = []
    pluginsList = plugins.all().copy()
    for plugin in pluginsList:
        if isBoundlessPlugin(pluginsList[plugin]):
            if (pluginsList[plugin]['installed'] and pluginsList[plugin]['deprecated']) or \
                    not pluginsList[plugin]['deprecated'] and \
                    pluginsList[plugin]["zip_repository"] != '':
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


def installAllFromDirectory(pluginsPath):
    """Install plugins from directory-based repository
    """
    errors = []

    installer = QgsPluginInstaller()

    mask = pluginsPath + '/*.zip'

    for plugin in glob.glob(mask):
        result = installFromZipFile(plugin)
        if result is not None:
            errors.append(result)

    installer.exportPluginsToManager()
    return errors


def installFromStandardPath():
    """Also install all plugins from "standard" location
    """
    dirName = os.path.join(QgsApplication.qgisSettingsDirPath(), firstRunPluginsPath)
    if os.path.isdir(dirName):
        installAllFromDirectory(dirName)


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

        settings = QSettings()
        # Reload plugin if it was already activated, start otherwise
        if settings.value('/PythonPlugins/' + pluginName, False, bool):
            reloadPlugin(pluginName)
        else:
            if startPlugin(pluginName):
                settings.setValue('/PythonPlugins/' + pluginName, True)

    return result


def isRepositoryInDirectory():
    """Return True if plugin repository is a plain directory
    """
    return os.path.isdir(os.path.join(pluginPath, boundlessRepo[1]))


def isBoundlessPlugin(plugin):
    """Return true if plugin is Boundless plugin
    """
    if plugin['zip_repository'] == boundlessRepo[0] or \
            'boundless' in plugin['code_repository']:
        return True
    else:
        return False


def obsoletePlugins():
    """Return list of installed deprecated Boundless plugins
    """
    installer = QgsPluginInstaller()
    installer.fetchAvailablePlugins(False)

    deprecated = []
    for plugin in plugins.all():
        if isBoundlessPlugin(plugins.all()[plugin]):
            if plugins.all()[plugin]['installed'] and \
                    (plugins.all()[plugin]['deprecated'] or
                    plugin in deprecatedPlugins):
                deprecated.append(plugins.all()[plugin])

    return deprecated


def connectVersion():
    cfg = ConfigParser.SafeConfigParser()
    cfg.read(os.path.join(pluginPath, 'metadata.txt'))
    version = cfg.get('general', 'version').split('.')
    version = ''.join(version)
    return version
