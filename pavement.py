# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import xmlrpclib
import zipfile

from paver.easy import *


options(
    plugin = Bunch(
        name = 'boundlessconnect',
        source_dir = path('boundlessconnect'),
        package_dir = path('.'),
        tests = ['test'],
        excludes = [
            '*.pyc',
            '.git',
            '*.pro'
        ],
        # skip certain files inadvertently found by exclude pattern globbing
        skip_exclude = []
    ),

    plugin_server = Bunch(
        server = 'qgis.boundlessgeo.com',
        port = 80,
        protocol = 'http',
        end_point = '/RPC2/'
    )
)


@task
def setup():
    """Empty: to ensure we use the same build/install procedure for all our plugins"""
    pass


@task
def install(options):
    """Install plugin to QGIS plugin directory
    """
    plugin_name = options.plugin.name
    src = path(__file__).dirname() / plugin_name
    dst = path('~').expanduser() / '.qgis2' / 'python' / 'plugins' / plugin_name
    src = src.abspath()
    dst = dst.abspath()
    if hasattr(src, 'symlink'):
        src.symlink(dst)
    else:
        dst.rmtree()
        src.copy(dst)


@task
def install_devtools():
    """Install development tools
    """
    try:
        import pip
    except:
        error('FATAL: Unable to import pip, please install it first!')
        sys.exit(1)

    pip.main(['install', '-r', 'requirements-dev.txt'])


@task
#@needs(['createhelp'])
@cmdopts([
    ('tests', 't', 'Package tests with plugin'),
])
def package(options):
    """Create plugin package
    """
    package_file = options.plugin.package_dir / ('%s.zip' % options.plugin.name)
    with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        if not hasattr(options.package, 'tests'):
            options.plugin.excludes.extend(options.plugin.tests)
        _make_zip(zf, options)
    return package_file


@task
def createhelp(options):
    """Generate plugin documentation and add it to plugin
    """
    plugin_name = options.plugin.name
    docsPath = './docs'
    cwd = os.getcwd()
    os.chdir(docsPath)
    sh('make html')
    os.chdir(cwd)
    src = path(__file__).dirname() / 'docs' / 'build' / 'html'
    dst = path(__file__).dirname() / plugin_name / 'help'
    src = src.abspath()
    dst = dst.abspath()
    dst.rmtree()
    src.copytree(dst)

@task
@cmdopts([
    ('user=', 'u', 'upload user'),
    ('passwd=', 'p', 'upload password'),
    ('server=', 's', 'alternate server'),
    ('end_point=', 'e', 'alternate endpoint'),
    ('port=', 't', 'alternate port'),
])
def upload(options):
    """Upload the package to the server
    """
    package_file = package(options)
    user = getattr(options, 'user', None),
    passwd = getattr(options, 'passwd', None)
    if not user or not passwd:
        raise BuildFailure('Provide user and passwd options to upload task')
    # create URL for XML-RPC calls
    s = options.plugin_server
    server = getattr(options, 'server', None)
    end_point = getattr(options, 'end_point', None)
    port = getattr(options, 'port', None)
    if server == None:
        server = s.server
    if end_point == None:
        end_point = s.end_point
    if port == None:
        port = s.port
    uri = '%s://%s:%s@%s:%s%s' % (s.protocol, options['user'],
                                  options['passwd'], server, port, end_point)
    info('Uploading to %s', uri)
    server = xmlrpclib.ServerProxy(uri, verbose=False)
    try:
        pluginId, versionId = server.plugin.upload(
            xmlrpclib.Binary(package_file.bytes()))
        info('Plugin ID: %s', pluginId)
        info('Version ID: %s', versionId)
        package_file.unlink()
    except xmlrpclib.Fault, err:
        error('A fault occurred')
        error('Fault code: %d', err.faultCode)
        error('Fault string: %s', err.faultString)
    except xmlrpclib.ProtocolError, err:
        error('Protocol error')
        error('%s : %s', err.errcode, err.errmsg)
        if err.errcode == 403:
            error('Invalid name and password?')


@task
@consume_args
def pep8(args):
    """Check code for PEP8 violations
    """
    try:
        import pep8
    except:
        error('pep8 not found! Run "paver install_devtools".')
        sys.exit(1)

    # Errors to ignore
    ignore = ['E203', 'E121', 'E122', 'E123', 'E124', 'E125', 'E126', 'E127',
        'E128', 'E402']
    styleguide = pep8.StyleGuide(ignore=ignore,
                                 exclude=['*/ext-libs/*', '*/ext-src/*'],
                                 repeat=True, max_line_length=79,
                                 parse_argv=args)
    styleguide.input_dir(options.plugin.source_dir)
    info('===== PEP8 SUMMARY =====')
    styleguide.options.report.print_statistics()


@task
@consume_args
def autopep8(args):
    """Format code according to PEP8
    """
    try:
        import autopep8
    except:
        error('autopep8 not found! Run "paver install_devtools".')
        sys.exit(1)

    if any(x not in args for x in ['-i', '--in-place']):
        args.append('-i')

    args.append('--ignore=E261,E265,E402,E501')
    args.insert(0, 'dummy')

    cmd_args = autopep8.parse_args(args)

    excludes = ('ext-lib', 'ext-src')
    for p in options.plugin.source_dir.walk():
        if any(exclude in p for exclude in excludes):
            continue

        if p.fnmatch('*.py'):
            autopep8.fix_file(p, options=cmd_args)


@task
@consume_args
def pylint(args):
    """Check code for errors and coding standard violations
    """
    try:
        from pylint import lint
    except:
        error('pylint not found! Run "paver install_devtools".')
        sys.exit(1)

    if not 'rcfile' in args:
        args.append('--rcfile=pylintrc')

    args.append(options.plugin.source_dir)
    lint.Run(args)


def _make_zip(zipFile, options):
    excludes = set(options.plugin.excludes)
    skips = options.plugin.skip_exclude

    src_dir = options.plugin.source_dir
    exclude = lambda p: any([path(p).fnmatch(e) for e in excludes])
    def filter_excludes(root, items):
        if not items:
            return []
        # to prevent descending into dirs, modify the list in place
        for item in list(items):  # copy list or iteration values change
            itempath = path(os.path.relpath(root)) / item
            if exclude(item) and item not in skips:
                debug('Excluding %s' % itempath)
                items.remove(item)
        return items

    for root, dirs, files in os.walk(src_dir):
        for f in filter_excludes(root, files):
            relpath = os.path.relpath(root)
            zipFile.write(path(root) / f, path(relpath) / f)
        filter_excludes(root, dirs)
