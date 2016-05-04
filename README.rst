Boundless Connect
=================
The Boundless Connect Plugin for QGIS allows user to access Boundless services and plugins.

The main goal of Boundless Connect Plugin for QGISis to help users setting up Boundless Plugin Repository and make it easier for them to install plugins and their components. The current version provides:

* First Run wizard for post-installation QGIS setup
* Support for local directory-based plugins repository
* Automated way of installing additional non-Boundless plugins
* Ability to install QGIS plugins from local ZIP packages

Documentation
-------------
The plugin is documented `here <http://boundlessgeo.github.io/qgis-plugins-documentation/connect/>`_.

Cloning this repository
-----------------------
This repository uses external repositories as submodules. Therefore in order to include the external repositories during cloning you should use the *--recursive* option:

``git clone --recursive http://github.com/boundlessgeo/qgis-connect-plugin.git``

Also, to update the submodules whenever there are changes in the remote repositories one should do:

``git submodule update --remote``
