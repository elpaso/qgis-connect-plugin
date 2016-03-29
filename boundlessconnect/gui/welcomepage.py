# -*- coding: utf-8 -*-

"""
***************************************************************************
    welcomepage.py
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

from PyQt4 import uic

from boundlessconnect.utils import obsoletePlugins, isRepositoryInDirectory

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'welcomepagebase.ui'))


class WelcomePage(BASE, WIDGET):
    def __init__(self, parent=None):
        super(WelcomePage, self).__init__(parent)
        self.setupUi(self)

        # check for deprecated plugins and warn user
        plugins = obsoletePlugins()
        if len(plugins) > 0:
            msg = self.tr('<h2>Deprecated plugins found!</h2>')
            msg += self.tr('<p>We suggest to remove following plugins as they '
                           'are not supported anymore:</p>')
            msg += '<ul>'
            for p in plugins:
                msg += '<li>{}</li>'.format(p['name'])
            msg += '</ul>'

            self.infoBox.setHtml(msg)
        else:
            self.infoBox.hide()

    def nextId(self):
        if isRepositoryInDirectory():
            return 2
        else:
            return 1
