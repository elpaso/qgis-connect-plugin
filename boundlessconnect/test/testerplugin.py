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
import unittest

from PyQt4.QtCore import QSettings

from qgis.utils import active_plugins
from pyplugin_installer.installer import QgsPluginInstaller
from pyplugin_installer.installer_data import reposGroup, plugins

from boundlessconnect.plugins import boundlessRepoName
from boundlessconnect import utils

testPath = os.path.dirname(__file__)

installedPlugins = []

def functionalTests():
    try:
        from qgistester.test import Test
        from qgistester.utils import *
    except:
        return []


    boundlessRepoTest = Test('Verify that Boundless Connect can start Plugin Manager')
    boundlessRepoTest.addStep('Check that OpenGeo Explorer listed in Plugin Manager as well as plugins from QGIS repository',
                                prestep=_openPluginManager, isVerifyStep=True)
    boundlessRepoTest.setIssueUrl("https://issues.boundlessgeo.com:8443/browse/QGIS-325")

    return [boundlessRepoTest]


class BoundlessConnectTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global installedPlugins
        installedPlugins[:] = []
        for key in plugins.all():
            if plugins.all()[key]['zip_repository'] == boundlessRepoName or \
                    'boundlessgeo' in plugins.all()[key]['code_repository'] and\
                    plugins.all()[key]['installed']:
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

    def testInstallAll(self):
        """Test that Connect installs all Boundless plugins"""
        utils.installAllPlugins()

        total = 0
        installed = 0
        for key in plugins.all():
            if plugins.all()[key]['zip_repository'] == boundlessRepoName or \
                    'boundlessgeo' in plugins.all()[key]['code_repository']:
                total += 1
                if plugins.all()[key]['installed']:
                    installed += 1

        assert (total == installed), 'Number of installed Boundless plugins does not match number of available Boundless plugins'

    @classmethod
    def tearDownClass(cls):
        """Remove installed HelloWorld plugin"""
        installer = QgsPluginInstaller()
        if 'connecttest' in active_plugins:
            installer.uninstallPlugin('connecttest', quiet=True)

        global installedPlugins
        for key in plugins.all():
            if plugins.all()[key]['zip_repository'] == boundlessRepoName or \
                    'boundlessgeo' in plugins.all()[key]['code_repository'] and \
                    key not in installedPlugins:
                installer.uninstallPlugin(key, quiet=True)


def unitTests():
    connectSuite = unittest.makeSuite(BoundlessConnectTests, 'test')
    _tests = []
    _tests.extend(connectSuite)

    return _tests


def _openPluginManager():
    utils.showPluginManager()


def _installAllPlugins():
    utils.installAllPlugins()
