# -*- coding: utf-8 -*-

"""
***************************************************************************
    passwordlineedit.py
    ---------------------
    Date                 : August 2016
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
__date__ = 'August 2016'
__copyright__ = '(C) 2016 Boundless, http://boundlessgeo.com'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QLineEdit, QToolButton, QIcon, QStyle

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class PasswordLineEdit(QLineEdit):
    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)

        self.setPlaceholderText(self.tr('Password'))
        self.setEchoMode(QLineEdit.Password)

        self.btnToggle = QToolButton(self)
        self.btnToggle.setIcon(QIcon(os.path.join(pluginPath, 'icons', 'hidden.svg')))
        self.btnToggle.setCheckable(True)
        self.btnToggle.setToolTip(self.tr('Toggle password visibility'))
        self.btnToggle.setCursor(Qt.ArrowCursor)
        self.btnToggle.setStyleSheet('QToolButton { border: none; padding: 0px; }')

        self.btnToggle.toggled.connect(self.togglePassword)

        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet('QLineEdit {{ padding-right: {}px; }} '.format(self.btnToggle.sizeHint().width() + frameWidth + 1))
        msz = self.minimumSizeHint()
        self.setMinimumSize(max(msz.width(), self.btnToggle.sizeHint().height() + frameWidth * 2 + 2),
                            max(msz.height(), self.btnToggle.sizeHint().height() + frameWidth * 2 + 2))

    def resizeEvent(self, event):
        sz = self.btnToggle.sizeHint()
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        self.btnToggle.move(self.rect().right() - frameWidth - sz.width(),
                           (self.rect().bottom() + 1 - sz.height())/2)

    def togglePassword(self, toggled):
        if toggled:
            self.setEchoMode(QLineEdit.Normal)
            self.btnToggle.setIcon(QIcon(os.path.join(pluginPath, 'icons', 'visible.svg')))
        else:
            self.setEchoMode(QLineEdit.Password)
            self.btnToggle.setIcon(QIcon(os.path.join(pluginPath, 'icons', 'hidden.svg')))
