# -*- coding: utf-8 -*-

"""
***************************************************************************
    testerplugin.py
    ---------------------
    Date                 : March 2016
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
__date__ = 'March 2016'
__copyright__ = '(C) 2016 Boundless, http://boundlessgeo.com'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import json
import unittest
import ConfigParser

from PyQt4.QtCore import QSettings

from qgis.core import QgsApplication

from qgis.utils import active_plugins, home_plugin_path, unloadPlugin
from pyplugin_installer.installer import QgsPluginInstaller
from pyplugin_installer.installer_data import reposGroup, plugins, removeDir

from boundlessconnect.plugins import boundlessRepoName, repoUrlFile
from boundlessconnect import utils

testPath = os.path.dirname(__file__)

originalVersion = None
installedPlugins = []

def functionalTests():
    try:
        from qgistester.test import Test
    except:
        return []

    openPluginManagerTest = Test('Verify that Boundless Connect can start Plugin Manager')
    openPluginManagerTest.addStep('Check that OpenGeo Explorer listed in Plugin Manager as well as plugins from QGIS repository',
                                prestep=lambda: _openPluginManager(False), isVerifyStep=True)
    openPluginManagerTest.setIssueUrl("https://issues.boundlessgeo.com:8443/browse/QGIS-325")

    openPluginManagerBoundlessOnlyTest = Test('Verify that Boundless Connect can start Plugin Manager only with Boundless plugins')
    openPluginManagerBoundlessOnlyTest.addStep('Check that Plugin manager is open and contains only Boundless plugins',
                                prestep=lambda: _openPluginManager(True), isVerifyStep=True)
    openPluginManagerBoundlessOnlyTest.setIssueUrl("https://issues.boundlessgeo.com:8443/browse/QGIS-325")

    coreConnectUpdateTest = Test('Test updating core Connect plugin via Plugin Manager')
    coreConnectUpdateTest.addStep('Downgrade installed Connect plugin', lambda: _downgradePlugin('boundlessconnect'))
    coreConnectUpdateTest.addStep('Check that Connect plugin is upgradable',
                                  prestep=lambda: _openPluginManager(True), isVerifyStep=True)
    coreConnectUpdateTest.addStep('Upgrade Connect plugin')
    coreConnectUpdateTest.addStep('Check that Connect plugin updated, loaded from user folder and has latest version', isVerifyStep=True)
    coreConnectUpdateTest.setIssueUrl("https://issues.boundlessgeo.com:8443/browse/QGIS-602")
    coreConnectUpdateTest.setCleanup(lambda: _restoreVersion('boundlessconnect'))

    return [openPluginManagerTest, openPluginManagerBoundlessOnlyTest, coreConnectUpdateTest]


class BoundlessConnectTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global installedPlugins
        installedPlugins[:] = []
        for key in plugins.all():
            if utils.isBoundlessPlugin(plugins.all()[key]) and plugins.all()[key]['installed']:
                installedPlugins.append(key)

    def testBoundlessRepoAdded(self):
        """Test that Boundless repository added to QGIS"""
        settings = QSettings('Boundless', 'BoundlessConnect')
        repoUrl = settings.value('repoUrl', '', unicode)

        settings = QSettings()
        settings.beginGroup(reposGroup)
        self.assertTrue(boundlessRepoName in settings.childGroups())
        settings.endGroup()

        settings.beginGroup(reposGroup + '/' + boundlessRepoName)
        url = settings.value('url', '', unicode)
        self.assertEqual(url, repoUrl)
        settings.endGroup()

    def testInstallFromZip(self):
        """Test plugin installation from ZIP package"""
        pluginPath = os.path.join(testPath, 'data', 'connecttest.zip')
        result = utils.installFromZipFile(pluginPath)
        self.assertIsNone(result), 'Error installing plugin: {}'.format(result)
        self.assertTrue('connecttest' in active_plugins), 'Plugin not activated'

        unloadPlugin('connecttest')
        result = removeDir(os.path.join(home_plugin_path, 'connecttest'))
        self.assertFalse(result), 'Plugin directory not removed'
        result = utils.installFromZipFile(pluginPath)
        self.assertIsNone(result), 'Error installing plugin: {}'.format(result)
        self.assertTrue('connecttest' in active_plugins), 'Plugin not activated after reinstallation'

    def testIsBoundlessCheck(self):
        """Test that Connect detects Boundless plugins"""
        with open(os.path.join(testPath, 'data', 'samplepluginsdict.json')) as f:
            pluginsDict = json.load(f)
        count = len([key for key in pluginsDict if utils.isBoundlessPlugin(pluginsDict[key])])
        self.assertEqual(8, count)

    def testCustomRepoUrl(self):
        """Test that Connect read custom repository URL and apply it"""
        settings = QSettings('Boundless', 'BoundlessConnect')
        oldRepoUrl = settings.value('repoUrl', '', unicode)

        settings.setValue('repoUrl', 'test')
        self.assertEqual('test', settings.value('repoUrl'))

        fName = os.path.join(QgsApplication.qgisSettingsDirPath(), repoUrlFile)
        with open(fName, 'w') as f:
            f.write('[general]\nrepoUrl=http://dummyurl.com')
        utils.setRepositoryUrl()

        self.assertTrue('http://dummyurl.com', settings.value('repoUrl', '', unicode))
        settings.setValue('repoUrl', oldRepoUrl)

    def testInstallAll(self):
        """Test that Connect installs all Boundless plugins"""
        utils.installAllPlugins()

        total = 0
        installed = 0
        for key in plugins.all():
            if utils.isBoundlessPlugin(plugins.all()[key]):
                total += 1
                if plugins.all()[key]['installed']:
                    installed += 1

        assert (total == installed), 'Number of installed Boundless plugins does not match number of available Boundless plugins'

    @classmethod
    def tearDownClass(cls):
        # Remove installed HelloWorld plugin
        installer = QgsPluginInstaller()
        if 'connecttest' in active_plugins:
            installer.uninstallPlugin('connecttest', quiet=True)

        # Also remove other installed plugins
        global installedPlugins
        for key in plugins.all():
            if utils.isBoundlessPlugin(plugins.all()[key]) and key not in installedPlugins:
                installer.uninstallPlugin(key, quiet=True)


def unitTests():
    connectSuite = unittest.makeSuite(BoundlessConnectTests, 'test')
    _tests = []
    _tests.extend(connectSuite)

    return _tests


def _openPluginManager(boundlessOnly):
    utils.showPluginManager(boundlessOnly)


def _installAllPlugins():
    utils.installAllPlugins()


def _downgradePlugin(pluginName, corePlugin=True):
    if corePlugin:
        metadataPath = os.path.join(QgsApplication.pkgDataPath(), 'python', 'plugins', pluginName, 'metadata.txt')
    else:
        metadataPath = os.path.join(QgsApplication.qgisSettingsDirPath()(), 'python', 'plugins', pluginName, 'metadata.txt')

    cfg = ConfigParser.SafeConfigParser()
    cfg.read(metadataPath)
    global originalVersion
    originalVersion = cfg.get('general', 'version')
    cfg.set('general', 'version', '0.0.1')
    with open(metadataPath, 'wb') as f:
        cfg.write(f)


def _restoreVersion(pluginName, corePlugin=True):
    if corePlugin:
        metadataPath = os.path.join(QgsApplication.pkgDataPath(), 'python', 'plugins', pluginName, 'metadata.txt')
    else:
        metadataPath = os.path.join(QgsApplication.qgisSettingsDirPath()(), 'python', 'plugins', pluginName, 'metadata.txt')

    cfg = ConfigParser.SafeConfigParser()
    cfg.read(metadataPath)
    global originalVersion
    cfg.set('general', 'version', originalVersion)
    with open(metadataPath, 'wb') as f:
        cfg.write(f)

    originalVersion = None
