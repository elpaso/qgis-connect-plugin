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

from pyplugin_installer.installer_data import reposGroup

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


    boundlessConnectTest = Test('Verify that Boundless Connect is the single plugin added to QGIS')
    boundlessConnectTest.addStep('Open Plugin Manager', _openPluginManager)
    boundlessConnectTest.addStep('Check that Boundless Connect listed in the Plugin Manager', isVerifyStep=True)

    return [boundlessConnectTest]


class BoundlessConnectTests(unittest.TestCase):

    def testBoundlessRepoAdded(self):
        '''Test that Boundless repository added to QGIS'''
        settings = QSettings()
        settings.beginGroup(reposGroup)
        self.assertTrue(boundlessRepo[0] in settings.childGroups())
        settings.endGroup()

        settings.beginGroup(reposGroup + '/' + boundlessRepo[0])
        url = settings.value('url', '', unicode)
        self.assertEqual(url, boundlessRepo[1])
        settings.endGroup()

    def testInstallFromZip(self):
        '''Test plugin installation from ZIP package'''
        pluginPath = os.path.join(testPath, 'data', 'helloworld.zip')
        result = utils.installFromZipFile(fileName)
        self.assertIsNone(result)


def unitTests():
    connectSuite = unittest.makeSuite(BoundlessConnectTests, 'test')
    _tests = []
    _tests.extend(connectSuite)

    return _tests


def _addRepository():
    utils.addBoundlessRepository()


def _openPluginManager():
    utils.showPluginManager()
