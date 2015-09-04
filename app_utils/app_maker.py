# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

import argparse
import buildtools
import MacOS
import os
import plistlib
import shutil


def make():
    flavors = 'diode', 'co2', 'valve', 'uv', 'experiment', 'view', 'bakedpy', 'remote_hardware_server'
    flavorstr = ', '.join(map(lambda x: '"{}"'.format(x), flavors))

    parser = argparse.ArgumentParser(description='Make a pychron application')
    parser.add_argument('-A', '--applications',
                        nargs=1,
                        type=str,
                        # default=['pychron', 'remote_hardware_server', 'bakeout'],
                        help='set applications to build. valid flavors {}'.format(flavorstr)),
    parser.add_argument('-v', '--version',
                        nargs=1,
                        type=str,
                        default=['1.0'],
                        help='set the version number e.g 1.0')

    parser.add_argument(
        '-r',
        '--root',
        type=str,
        nargs=1,
        default='.',
        help='set the root directory')

    parser.add_argument('-e', '--egg', action='store_true',
                        help='Do not make a python egg')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Do not make a python egg')
    args = parser.parse_args()
    apps = args.applications
    for name in apps:
        template = None
        if name in flavors:
            template = Template()
            template.root = args.root[0]

            template.version = args.version[0]
            template.name = name
            template.use_egg = not args.egg
            template.debug = args.debug

            if name in ('bakedpy',):
                template.root = args.root[0]
                #                template.version = args.version[0]
                #                template.name = name
                template.icon_name = '{}_icon.icns'.format(name)
                template.bundle_name = name
            elif name == 'remote_hardware_server':
                template.icon_name = 'remote_hardware_server_icon.icns'
                template.bundle_name = name
                template.packages = ['pychron.messaging',
                                     'pychron.messaging.handlers',
                                     'pychron.remote_hardware',
                                     'pychron.remote_hardware.errors',
                                     'pychron.core',
                                     'pychron.hardware.core',
                                     'pychron.core.helpers',
                                     'pychron.core.ui', 'pychron.core.ui.qt',
                                     'pychron.core.xml',
                                     'pychron.displays']
                template.modules = ['pychron.managers.remote_hardware_server_manager',
                                    'pychron.managers.manager',
                                    'pychron.paths',
                                    'pychron.file_defaults',
                                    'pychron.globals',
                                    'pychron.config_loadable',
                                    'pychron.version',
                                    'pychron.initialization_parser',
                                    'pychron.loggable',
                                    'pychron.viewable',
                                    'pychron.saveable',
                                    'pychron.rpc.rpcable',
                                    # 'pychron.hardware.core.checksum_helper',
                                    'pychron.utils',
                                    'pychron.application_controller']
            else:
                #                template = Template()


                template.icon_name = 'py{}_icon.icns'.format(name)
                template.bundle_name = 'py{}'.format(name)

        if template is not None:
            template.build()
        else:
            print "Invalid application flavor. Use {}".format(', '.join(map("'{}'".format, flavors)))


class Template(object):
    name = None
    icon_name = None
    root = None
    bundle_name = None
    version = None
    packages = None
    modules = None
    use_egg = True
    debug = False

    def build(self):
        root = os.path.realpath(self.root)

        dest = os.path.join(root, 'launchers',
                            '{}.app'.format(self.bundle_name),
                            'Contents')
        ins = Maker()
        ins.root = root
        ins.dest = dest
        ins.name = self.bundle_name
        ins.apppath = os.path.join(root, 'launchers',
                                   '{}.app'.format(self.bundle_name))
        ins.version = self.version

        op = os.path.join(root, 'launchers',
                          '{}.py'.format(self.bundle_name))
        # =======================================================================
        # build
        # =======================================================================

        ins.build_app(op)
        if not self.debug:
            if self.use_egg:
                ins.make_egg(self.packages, self.modules)
            else:
                ins.copy_source()
        # ins.make_migrate_repos()
        ins.make_argv()

        # =======================================================================
        # copy
        # =======================================================================
        icon_name = self.icon_name
        if icon_name is None:
            icon_name = ''

        ins.set_plist(dest, self.bundle_name, icon_name)

        icon_file = os.path.join(self.root,
                                 'resources', 'apps',
                                 icon_name)

        if os.path.isfile(icon_file):
            shutil.copyfile(icon_file,
                            os.path.join(dest, 'Resources', icon_name))


        #        for pn in ('start', 'stop'):
        #            ins.copy_resource(os.path.join(root,
        #                                           'resources', 'icons',
        #                                           '{}.png'.format(pn)))
        #copy entire icons dir
        # iroot = os.path.join(root, 'resources', 'icons')
        # for di in os.listdir(iroot):
        #     #            print di
        #     ins.copy_resource(os.path.join(iroot, di))

        # copy entire icons dir
        iroot = os.path.join(root, 'resources', 'icons')

        # make resource dirs
        for d in ('icons',):
            idest = os.path.join(dest, 'Resources', d)
            if not os.path.isdir(idest):
                os.mkdir(idest)

        includes = []
        icon_req = os.path.join(root, 'resources', 'icon_req.txt')
        if os.path.isfile(icon_req):
            with open(icon_req, 'r') as rfile:
                includes = [ri.strip() for ri in rfile.read().split('\n')]

        cnt, total = 0, 0
        for di in os.listdir(iroot):
            total += 1
            head,tail=os.path.splitext(di)
            if includes and head not in includes:
                continue

            cnt += 1
            ins.copy_resource(os.path.join(iroot, di), name='icons/{}'.format(di))

        print 'copied {}/{} icons'.format(cnt, total)
        # copy splashes and abouts
        for ni, nd in (('splash', 'splashes'), ('about', 'abouts')):
            sname = '{}_{}.png'.format(ni, self.name)
            ins.copy_resource(os.path.join(root, 'resources', nd, sname), name='icons/{}.png'.format(ni))

        # copy helper mod
        for a in ('helpers.py', 'ENV.txt'):
            m = os.path.join(self.root, 'launchers', a)
            ins.copy_resource(m)

        # for anaconda builds
        # copy qt.nib
        p = '/anaconda/python.app/Contents/Resources/qt_menu.nib'
        if not os.path.isdir(p):
            p = '{}/{}'.format(os.path.expanduser('~'),
                               'anaconda/python.app/Contents/Resources/qt_menu.nib')

        ins.copy_resource_dir(p)

        # =======================================================================
        # rename
        # =======================================================================
        ins.rename_app()


class PychronTemplate(Template):
    pass


class Maker(object):
    root = None
    dest = None
    version = None
    name = None

    def copy_resource(self, src, name=None):
        if os.path.isfile(src):
            if name is None:
                name = os.path.basename(src)
            shutil.copyfile(src,
                            self._resource_path(name))
        else:
            print '++++++++++++++++++++++ Not a valid Resource {} +++++++++++++++++++++++'.format(src)

    def copy_resource_dir(self, src, name=None):
        if os.path.exists(src):
            if name is None:
                name = os.path.basename(src)
            shutil.copytree(src, self._resource_path(name))
        else:
            print '++++++++++++++++++++++ Not a valid Resource {} +++++++++++++++++++++++'.format(src)

    def _resource_path(self, name):
        return os.path.join(self.dest, 'Resources', name)

    def make_migrate_repos(self):

        root = self.root
        p = os.path.join(root, 'pychron', 'database', 'migrate')
        shutil.copytree(p, self._resource_path('migrate_repositories'))

    def copy_source(self):
        shutil.copytree(os.path.join(self.root, 'pychron'), self._resource_path('pychron'))

    def make_egg(self, pkgs=None, modules=None):

        from setuptools import setup, find_packages

        if pkgs is None:
            pkgs = find_packages(self.root,
                                 exclude=('launchers',
                                          'tests',
                                          'test',
                                          'test.*',
                                          'sandbox',
                                          'sandbox.*',
                                          '*.sandbox',
                                          'app_utils'))
        if modules is None:
            modules = []

        setup(name='pychron',
              script_args=('bdist_egg',),
              py_modules=modules,
              #                           '-b','/Users/argonlab2/Sandbox'),
              # version=self.version,
              packages=pkgs)

        # eggname = 'pychron-{}-py2.7.egg'.format(self.version)
        eggname = 'pychron-0.0.0-py2.7.egg'
        # make the .pth file
        with open(os.path.join(self.dest,
                               'Resources',
                               'pychron.pth'), 'w') as rfile:
            rfile.write('{}\n'.format(eggname))

        egg_root = os.path.join(self.root, 'dist', eggname)
        shutil.copyfile(egg_root,
                        self._resource_path(eggname))

        # remove build dir/dist
        for di in ('build', 'dist', 'pychron.egg-info'):
            p = os.path.join(self.root, di)
            print 'removing entire {} dir {}'.format(di, p)
            shutil.rmtree(p)

    def make_argv(self):
        argv = '''
import os
execfile(os.path.join(os.path.split(__file__)[0], "{}.py"))
'''.format(self.name)

        p = self._resource_path('__argvemulator_{}.py'.format(self.name))
        with open(p, 'w') as rfile:
            rfile.write(argv)

    def set_plist(self, dest, bundle_name, icon_name):
        info_plist = os.path.join(dest, 'Info.plist')
        tree = plistlib.readPlist(info_plist)

        tree['CFBundleIconFile'] = icon_name
        tree['CFBundleDisplayName'] = bundle_name
        tree['CFBundleName'] = bundle_name
        plistlib.writePlist(tree, info_plist)

    def build_app(self, filename):
        print filename
        template = buildtools.findtemplate()
        dstfilename = None
        rsrcfilename = None
        raw = 0
        extras = []
        verbose = None
        destroot = ''

        cr, tp = MacOS.GetCreatorAndType(filename)
        if tp == 'APPL':
            buildtools.update(template, filename, dstfilename)
        else:
            buildtools.process(template, filename, dstfilename, 1,
                               rsrcname=rsrcfilename, others=extras, raw=raw,
                               progress=verbose, destroot=destroot)

    def rename_app(self):
        old = self.apppath
        new = os.path.join(os.path.dirname(old),
                           '{}_{}.app'.format(self.name, self.version))
        i = 1
        #        print old, new
        while 1:
            #        for i in range(3):
            try:
                os.rename(old, new)
                break
            except OSError, e:
                # print 'exception', e
                name = new[:-4]
                bk = '{}_{:03d}bk.app'.format(name, i)
                print '{} already exists. backing it up as {}'.format(new, bk)
                try:
                    os.rename(new, bk)
                except OSError:
                    i += 1


if __name__ == '__main__':
    make()
