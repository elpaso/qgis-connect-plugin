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
import shutil
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
from pyplugin_installer.version_compare import compareVersions
from pyplugin_installer.unzip import unzip

from boundlessconnect.plugins import (boundlessRepoName,
                                      defaultRepoUrl,
                                      repoUrlFile,
                                      firstRunPluginsPath,
                                      oldPlugins,
                                      localPlugins)

pluginPath = os.path.dirname(__file__)


def addBoundlessRepository():
    """Add Boundless plugin repository to list of the available
       plugin repositories if it is not presented here
    """
    settings = QSettings('Boundless', 'BoundlessConnect')
    repoUrl = settings.value('repoUrl', '', unicode)

    if repoUrl == '':
        setRepositoryUrl()

    if isRepositoryInDirectory():
        return

    settings = QSettings('Boundless', 'BoundlessConnect')
    repoUrl = settings.value('repoUrl', '', unicode)

    needUrlChange = False
    if 'qgis.boundlessgeo.com' in repoUrl and repoUrl.startswith('http:'):
        newRepoUrl = repoUrl.replace('http', 'https')
        settings.setValue('repoUrl', newRepoUrl)
        needUrlChange = True

    settings = QSettings()
    settings.beginGroup(reposGroup)
    hasBoundlessRepository = False
    for repo in settings.childGroups():
        url = settings.value(repo + '/url', '', unicode)
        if url == repoUrl:
            hasBoundlessRepository = True
    # Boundless repository not found, so we add it to the list
    if not hasBoundlessRepository:
        settings.setValue(boundlessRepoName + '/url', repoUrl)
        settings.setValue(boundlessRepoName + '/authcfg', '')
    if needUrlChange:
        settings.setValue(boundlessRepoName + '/url', newRepoUrl)
        settings.setValue(boundlessRepoName + '/authcfg', '')
    settings.endGroup()


def setRepositoryAuth(authConfigId):
    """Add auth to the repository
    """
    settings = QSettings('Boundless', 'BoundlessConnect')
    repoUrl = settings.value('repoUrl', '', unicode)

    settings = QSettings()
    settings.beginGroup(reposGroup)
    for repo in settings.childGroups():
        url = settings.value(repo + '/url', '', unicode)
        if url == repoUrl:
            settings.setValue(repo + '/authcfg', authConfigId)
    settings.endGroup()


def showPluginManager(boundlessOnly):
    """Show Plugin Manager with all plugins. This includes plugins from
    Official QGIS plugins repository and plugins from Boundless plugins
    repository (local or remote).
    If boundlessOnly=True, it will only show Boundless plugins
    """
    installer = QgsPluginInstaller()

    initPluginManager(installer, boundlessOnly)

    iface.pluginManagerInterface().showPluginManager(2)
    # Restore repositories, as we don't want to keep local repo in cache
    repositories.load()


def initPluginManager(installer, boundlessOnly=False):
    """Prepare plugin manager content
    """
    settings = QSettings('Boundless', 'BoundlessConnect')
    repoUrl = settings.value('repoUrl', '', unicode)

    if installer.statusLabel:
        iface.mainWindow().statusBar().removeWidget(installer.statusLabel)

    # Load plugins from remote repositories and export repositories
    # to Plugin Manager
    installer.fetchAvailablePlugins(False)
    installer.exportRepositoriesToManager()

    # If Boundless repository is a local directory, add plugins
    # from it to Plugin Manager
    if isRepositoryInDirectory():
        repositoryData = {'url': repoUrl,
                          'authcfg': ''
                         }
        repositories.mRepositories.update({boundlessRepoName: repositoryData})

        localPlugins.getAllInstalled()
        localPlugins.load()
        localPlugins.rebuild()

        plugins.mPlugins.update(localPlugins.all())

    if boundlessOnly:
        for pluginName, pluginDesc in plugins.mPlugins.items():
            if not isBoundlessPlugin(pluginDesc):
                del plugins.mPlugins[pluginName]

    # Export all plugins to Plugin Manager
    installer.exportPluginsToManager()
    if installer.statusLabel:
        iface.mainWindow().statusBar().removeWidget(installer.statusLabel)


def installAllPlugins():
    """Install all available plugins from Boundless plugins repository
    """
    settings = QSettings('Boundless', 'BoundlessConnect')
    repoUrl = settings.value('repoUrl', '', unicode)

    if isRepositoryInDirectory():
        pluginsDirectory = os.path.abspath(repoUrl)
        installAllFromDirectory(pluginsDirectory)
    else:
        installAllFromRepository()


def installAllFromRepository():
    """Install Boundless plugins from remote repository
    """
    installer = QgsPluginInstaller()
    initPluginManager(installer)

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
    """Install plugins from specified directory
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
        shutil.rmtree(dirName)


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

        plugin = plugins.all()[pluginName]
        previousStatus = plugin['status']

        settings = QSettings()

        if previousStatus in ["not installed", "new"]:
            if startPlugin(pluginName):
                settings.setValue('/PythonPlugins/' + pluginName, True)
        else:
            # Reload plugin if it was already activated, start otherwise
            if settings.value('/PythonPlugins/' + pluginName, False, bool):
                reloadPlugin(pluginName)
            else:
                unloadPlugin(pluginName)
                loadPlugin(pluginName)


        #~ settings = QSettings()
        #~ # Reload plugin if it was already activated, start otherwise
        #~ if settings.value('/PythonPlugins/' + pluginName, False, bool):
            #~ reloadPlugin(pluginName)
        #~ else:
            #~ if startPlugin(pluginName):
                #~ settings.setValue('/PythonPlugins/' + pluginName, True)

    return result


def isRepositoryInDirectory():
    """Return True if plugin repository is a plain directory
    """
    settings = QSettings('Boundless', 'BoundlessConnect')
    repoUrl = settings.value('repoUrl', '', unicode)

    return repoUrl != '' and os.path.isdir(os.path.abspath(repoUrl))


def isBoundlessPlugin(plugin):
    """Return true if plugin is Boundless plugin
    """
    if plugin['zip_repository'] == boundlessRepoName or \
            'boundless' in plugin['code_repository']:
        return True
    else:
        return False


def deprecatedPlugins():
    """Return list of installed deprecated Boundless plugins
    """
    installer = QgsPluginInstaller()
    initPluginManager(installer)

    deprecated = []
    for plugin in plugins.all():
        if isBoundlessPlugin(plugins.all()[plugin]):
            if plugins.all()[plugin]['installed'] and \
                    (plugins.all()[plugin]['deprecated'] or
                    plugin in oldPlugins):
                deprecated.append(plugins.all()[plugin])

    return deprecated


def checkPluginsStatus():
    """
    """
    installer = QgsPluginInstaller()
    initPluginManager(installer)

    availablePlugins = []
    installedPlugins = []
    updateNeeded = False
    for plugin in plugins.all():
        if isBoundlessPlugin(plugins.all()[plugin]):
            if plugins.all()[plugin]['installed']:
                if compareVersions(plugins.all()[plugin]["version_available"],
                                   plugins.all()[plugin]["version_installed"]) == 1:
                    updateNeeded = True
                installedPlugins.append(plugin)
            else:
                if not plugins.all()[plugin]['deprecated'] and not plugin in oldPlugins:
                    availablePlugins.append(plugin)

    allInstalled = len(availablePlugins) == 0

    return (updateNeeded, allInstalled)


def connectVersion():
    cfg = ConfigParser.SafeConfigParser()
    cfg.read(os.path.join(pluginPath, 'metadata.txt'))
    version = cfg.get('general', 'version').split('.')
    version = ''.join(version)
    return version


def setRepositoryUrl():
    fName = os.path.join(QgsApplication.qgisSettingsDirPath(), repoUrlFile)
    if os.path.exists(fName):
        cfg = ConfigParser.SafeConfigParser()
        cfg.read(fName)
        url = cfg.get('general', 'repoUrl')
        os.remove(fName)
    else:
        url = defaultRepoUrl

    settings = QSettings('Boundless', 'BoundlessConnect')
    settings.setValue('repoUrl', url)
