# -*- coding: utf-8 -*-

"""
***************************************************************************
    installer.py
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
import glob

from PyQt4.QtCore import QFile, QIODevice, QObject
from PyQt4.QtGui import QApplication, QCursor
from PyQt4.QtXml import QDomDocument

from qgis.utils import iface, home_plugin_path, startPlugin, unloadPlugin, loadPlugin, reloadPlugin
from pyplugin_installer.installer_data import reposGroup, seenPluginGroup, translatableAttributes, removeDir

from boundlesscentral.plugins import plugins


class PluginInstaller(QObject):
    def __init__(self):
        QObject.__init__(self)

        plugins.getAllInstalled()

    def fetchAvailablePlugins(self, reloadMode):
        plugins.getAllInstalled()
        plugins.load()
        plugins.rebuild()

    def exportPluginsToManager(self):
        iface.pluginManagerInterface().clearPythonPluginMetadata()

        for key in plugins.all():
            plugin = plugins.all()[key]
            iface.pluginManagerInterface().addPluginMetadata({
                'id': key,
                'plugin_id': plugin['plugin_id'] or '',
                'name': plugin['name'],
                'description': plugin['description'],
                'about': plugin['about'],
                'category': plugin['category'],
                'tags': plugin['tags'],
                'changelog': plugin['changelog'],
                'author_name': plugin['author_name'],
                'author_email': plugin['author_email'],
                'homepage': plugin['homepage'],
                'tracker': plugin['tracker'],
                'code_repository': plugin['code_repository'],
                'version_installed': plugin['version_installed'],
                'library': plugin['library'],
                'icon': plugin['icon'],
                'readonly': plugin['readonly'] and 'true' or 'false',
                'installed': plugin['installed'] and 'true' or 'false',
                'available': plugin['available'] and 'true' or 'false',
                'status': plugin['status'],
                'error': plugin['error'],
                'error_details': plugin['error_details'],
                'experimental': plugin['experimental'] and 'true' or 'false',
                'deprecated': plugin['deprecated'] and 'true' or 'false',
                'version_available': plugin['version_available'],
                'zip_repository': plugin['zip_repository'],
                'download_url': plugin['download_url'],
                'filename': plugin['filename'],
                'downloads': plugin['downloads'],
                'average_vote': plugin['average_vote'],
                'rating_votes': plugin['rating_votes'],
                'pythonic': 'true'
            })

        iface.pluginManagerInterface().reloadModel()

    def reloadAndExportData(self):
        self.fetchAvailablePlugins(reloadMode=True)
        self.exportPluginsToManager()

    def showPluginManagerWhenReady(self, *params):
        self.fetchAvailablePlugins(reloadMode=False)
        self.exportPluginsToManager()

        # Finally, show the Plugin Manager window
        tabIndex = -1
        if len(params) == 1:
            indx = unicode(params[0])
            if indx.isdigit() and int(indx) > -1 and int(indx) < 7:
                tabIndex = int(indx)
        iface.pluginManagerInterface().showPluginManager(tabIndex)

    def onManagerClose(self):
        plugins.updateSeenPluginsList()

    def installPlugin(self, key, quiet=False):
        error = False
        infoString = ('', '')
        plugin = plugins.all()[key]
        previousStatus = plugin['status']

        if not plugin:
            return

        if plugin['status'] == 'newer' and not plugin['error']:
            if QMessageBox.warning(iface.mainWindow(),
                                   self.tr('QGIS Python Plugin Installer'),
                                   self.tr('Are you sure you want to '
                                           'downgrade the plugin to the '
                                           'latest available version? The '
                                           'installed one is newer!'),
                                   QMessageBox.Yes,
                                   QMessageBox.No) == QMessageBox.No:
                return

        if not QDir(os.path.join(home_plugin_path, key)).exists():
            error = True
            infoString = (self.tr('Plugin has disappeared'),
                          self.tr("The plugin seems to have been installed "
                                  "but I don't know where. Probably the "
                                  "plugin package contained a wrong named "
                                  "directory.\nPlease search the list of "
                                  "installed plugins. I'm nearly sure you'll "
                                  "find the plugin there, but I just can't "
                                  "determine which of them it is. It also "
                                  "means that I won't be able to determine "
                                  "if this plugin is installed and inform "
                                  "you about available updates. However the "
                                  "plugin may work. Please contact the "
                                  "plugin author and submit this issue."))
            QApplication.setOverrideCursor(Qt.WaitCursor)
            plugins.getAllInstalled()
            plugins.rebuild()
            self.exportPluginsToManager()
            QApplication.restoreOverrideCursor()
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            updateAvailablePlugins()
            loadPlugin(plugin['id'])
            plugins.getAllInstalled(testLoad=True)
            plugins.rebuild()
            plugin = plugins.all()[key]
            if not plugin['error']:
                if previousStatus in ['not installed', 'new']:
                    infoString = (self.tr('Plugin installed successfully'), '')
                    if startPlugin(plugin['id']):
                        settings = QSettings()
                        settings.setValue('/PythonPlugins/' + plugin['id'], True)
                else:
                    settings = QSettings()
                    if settings.value('/PythonPlugins/' + key, False, bool):
                        reloadPlugin(key)
                        infoString = (self.tr('Plugin reinstalled successfully'), '')
                    else:
                        unloadPlugin(key)
                        loadPlugin(key)
                        infoString = (self.tr('Plugin reinstalled successfully'),
                                      self.tr('Python plugin reinstalled.\nYou need to restart QGIS in order to reload it.'))
                if quiet:
                    infoString = (None, None)
                QApplication.restoreOverrideCursor()
            else:
                QApplication.restoreOverrideCursor()
                if plugin['error'] == 'incompatible':
                    message = self.tr("The plugin is not compatible with this version of QGIS. It's designed for QGIS versions:")
                    message += ' <b>' + plugin['error_details'] + '</b>'
                elif plugin['error'] == 'dependent':
                    message = self.tr('The plugin depends on some components missing on your system. You need to install the following Python module in order to enable it:')
                    message += '<b> ' + plugin['error_details'] + '</b>'
                else:
                    message = self.tr('The plugin is broken. Python said:')
                    message += '<br><b>' + plugin['error_details'] + '</b>'
                dlg = QgsPluginInstallerPluginErrorDialog(iface.mainWindow(), message)
                dlg.exec_()
                if dlg.result():
                    # Revert installation
                    pluginDir = os.path.join(home_plugin_path, plugin['id'])
                    result = removeDir(pluginDir)
                    if QDir(pluginDir).exists():
                        error = True
                        infoString = (self.tr('Plugin uninstall failed'), result)
                        try:
                            exec ('sys.path_importer_cache.clear()')
                            exec ('import %s' % plugin["id"])
                            exec ('reload (%s)' % plugin["id"])
                        except:
                            pass
                    else:
                        try:
                            exec ('del sys.modules[%s]' % plugin['id'])
                        except:
                            pass
                    plugins.getAllInstalled()
                    plugins.rebuild()

            self.exportPluginsToManager()

        if infoString[0]:
            level = error and QgsMessageBar.CRITICAL or QgsMessageBar.INFO
            msg = '<b>%s:</b>%s' % (infoString[0], infoString[1])
            iface.pluginManagerInterface().pushMessage(msg, level)

    def uninstallPlugin(self, key, quiet=False):
        if key in plugins.all():
            plugin = plugins.all()[key]
        else:
            plugin = plugins.localCache[key]

        if not plugin:
            return

        if not quiet:
            warning = self.tr('Are you sure you want to uninstall the '
                              'following plugin?\n{})'.format(plugin['name']))
            if plugin['status'] == 'orphan' and not plugin['error']:
                warning += '\n\n' + self.tr("Warning: this plugin isn't available in any accessible repository!")
            if QMessageBox.warning(iface.mainWindow(),
                                   self.tr('QGIS Python Plugin Installer'),
                                   warning,
                                   QMessageBox.Yes,
                                   QMessageBox.No) == QMessageBox.No:
                return

        # Unload the plugin
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            unloadPlugin(key)
        except:
            pass

        pluginDir = os.path.join(home_plugin_path, plugin['id'])
        result = removeDir(pluginDir)
        if result:
            QApplication.restoreOverrideCursor()
            msg = '<b>{}:</b>{}'.format(self.tr('Plugin uninstall failed'), result)
            iface.pluginManagerInterface().pushMessage(msg, QgsMessageBar.CRITICAL)
        else:
            # Safe remove
            try:
                unloadPlugin(plugin['id'])
            except:
                pass

            try:
                exec ('plugins[%s].unload()' % plugin['id'])
                exec ('del plugins[%s]' % plugin['id'])
            except:
                pass

            try:
                exec ('del sys.modules[%s]' % plugin['id'])
            except:
                pass

            plugins.getAllInstalled()
            plugins.rebuild()
            self.exportPluginsToManager()
            QApplication.restoreOverrideCursor()
            iface.pluginManagerInterface().pushMessage(self.tr('Plugin uninstalled successfully'), QgsMessageBar.INFO)
