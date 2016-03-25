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

from boundlessconnect.boundlessconnect_plugin import BoundlessConnectPlugin
from boundlessconnect.plugins import boundlessRepo
from boundlessconnect import utils

testPath = os.path.dirname(__file__)


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

    installAllTest = Test('Verify that Boundless Connect installs all Boundless plugins')
    installAllTest.addStep('Install all Boundless plugins', _installAllPlugins)
    installAllTest.addStep('Check that all Boundless plugins installed', _checkBoundlessPlugins)
    installAllTest.setIssueUrl("https://issues.boundlessgeo.com:8443/browse/QGIS-324")

    return [boundlessRepoTest, installAllTest]


class BoundlessConnectTests(unittest.TestCase):

    def testBoundlessRepoAdded(self):
        """Test that Boundless repository added to QGIS"""
        settings = QSettings()
        settings.beginGroup(reposGroup)
        self.assertTrue(boundlessRepo[0] in settings.childGroups())
        settings.endGroup()

        settings.beginGroup(reposGroup + '/' + boundlessRepo[0])
        url = settings.value('url', '', unicode)
        self.assertEqual(url, boundlessRepo[1])
        settings.endGroup()

    def testInstallFromZip(self):
        """Test plugin installation from ZIP package"""
        pluginPath = os.path.join(testPath, 'data', 'helloworld.zip')
        result = utils.installFromZipFile(pluginPath)
        self.assertIsNone(result)
        self.assertTrue('helloworld' in active_plugins)

    @classmethod
    def tearDownClass(cls):
        """Remove installed HelloWorld plugin"""
        if 'helloworld' in active_plugins:
            installer = QgsPluginInstaller()
            installer.uninstallPlugin('helloworld', quiet=True)

def unitTests():
    connectSuite = unittest.makeSuite(BoundlessConnectTests, 'test')
    _tests = []
    _tests.extend(connectSuite)

    return _tests


def _openPluginManager():
    utils.showPluginManager()


def _installAllPlugins():
    utils.installAllPlugins()


def _checkBoundlessPlugins():
    total = 0
    installed = 0
    for key in plugins.all():
        if plugins.all()[key]['zip_repository'] == boundlessRepo[0] or 'boundlessgeo' in plugins.all()[key]['code_repository']:
            total += 1
            print '*** FOUND BOUNDLESS', key
            if plugins.all()[key]['installed']:
                print '**** INSTALLED'
                installed += 1

    print "************ TOTAL/INSTALLED", total, installed

    assert (total == installed), 'Number of installed Boundless plugins does not match number of available BOundless plugins'
