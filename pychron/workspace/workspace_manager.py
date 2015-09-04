# ===============================================================================
# Copyright 2014 Jake Ross
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
# ============= enthought library imports =======================
from pyface.constant import OK
from pyface.directory_dialog import DirectoryDialog
from traits.api import Property, \
    Event, List, Str, cached_property, Instance
# ============= standard library imports ========================
import shutil
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import list_directory2, fileiter
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.paths import paths
from pychron.workspace.analysis import WorkspaceAnalysis
from pychron.workspace.index import IndexAdapter, Base
from pychron.workspace.tasks.views import DiffView




class Manifest(object):
    def __init__(self, p):
        p = self.filename(p)
        if not os.path.isfile(p):
            with open(p, 'w'):
                pass
        self.path = p

    @classmethod
    def exists(cls, p):
        return os.path.isfile(cls.filename(p))

    @classmethod
    def filename(cls, p):
        return os.path.join(p, '.MANIFEST')

    def add(self, name):
        with open(self.path, 'r') as rfile:
            exists = next((line for line in fileiter(rfile, strip=True)
                           if line == name), None)

        if not exists:
            with open(self.path, 'a') as wfile:
                wfile.write('{}\n'.format(name))

    def remove(self, name):
        with open(self.path, 'w') as wfile:
            for line in fileiter(self.path, strip=True):
                if line == name:
                    continue
                else:
                    wfile.write('{}\n'.format(line))

    @property
    def names(self):
        with open(self.path, 'r') as rfile:
            return list(fileiter(rfile, strip=True))


class WorkspaceManager(GitRepoManager):
    index_db = Instance(IndexAdapter)
    # test = Button
    # selected = Any
    dclicked = Event
    repo_updated = Event

    branches = List
    commits = List

    selected_text = Str
    # selected_commits = List
    active = False

    def make_analyses(self, ans):
        self.debug('make analyses')
        def func(ai):
            p = os.path.join(self.path, '{}.yaml'.format(ai.record_id))
            w = WorkspaceAnalysis()
            w.sync(p)
            return w

        return [func(ai) for ai in ans]

    def _open_directory_dialog(self, **kw):
        dialog = DirectoryDialog(action='open', **kw)
        if dialog.open() == OK:
            r = dialog.path
            return r

    def open_workspace(self):
        self.debug('open workspace')
        p = os.path.join(paths.workspace_root_dir, 'test')
        if not os.path.isdir(p):
            p = self._open_directory_dialog(default_directory=paths.workspace_root_dir)

        if p:
            self.open_repo(p)

    def _validate_diff(self):
        return self.selected.endswith('.yaml')

    def _diff_view_factory(self, l, r):
        dd = self._calculate_diff_dict(l, r)
        dv = DiffView(l.summary, r.summary, dd)
        return dv

    def open_repo(self, name, root=None):

        self.active = True
        super(WorkspaceManager, self).open_repo(name, root)

        e = Manifest.exists(self.path)
        # init manifest object
        self._manifest = Manifest(self.path)
        if not e:
            self.add(self._manifest.path, msg='Added manifest file')

        self.update_gitignore('.index.db')
        self.index_db = IndexAdapter(path=os.path.join(self.path, '.index.db'))
        self.index_db.connect()
        self.index_db.create_all(Base.metadata)

        self.create_branch('develop')
        self.checkout_branch('develop')

    def load_branches(self):
        self.branches = [bi.name for bi in self._repo.branches]

    def create_branch(self, name):
        super(WorkspaceManager, self).create_branch(name)
        self.load_branches()

    def find_existing(self, names):
        return [os.path.splitext(ni)[0] for ni in self._manifest.names if ni in names]

    def add_to_manifest(self, path):
        self._manifest.add(os.path.basename(path))

    def add_manifest_to_index(self):
        p = self._manifest.path
        index = self.index
        index.add([p])

    def commit_manifest(self):
        p = self._manifest.path
        self._add_to_repo(p, msg='Updated manifest')

    def add_analysis(self, path, commit=True, message=None, **kw):
        """
            path: absolute path to flat file
            commit: commit changes
            message: message to use for commit


            1. copy file at path to the repository
            2. add record to index

        """

        repo = self._repo
        # copy file to repo
        dest = os.path.join(repo.working_dir, os.path.basename(path))
        if not os.path.isfile(dest):
            shutil.copyfile(path, dest)

        # add to master changeset
        index = repo.index
        index.add([dest])
        if commit:
            if message is None:
                message = 'added record {}'.format(path)
            index.commit(message)

        self.repo_updated = True

    def add_analysis_to_index(self, ai):
        # add to sqlite index
        im = self.index_db
        im.add(repo=self._repo.working_dir,
               identifier=ai.identifier,
               aliquot=ai.aliquot,
               increment=ai.increment,
               cleanup=ai.cleanup,
               duration=ai.duration,
               extract_value=ai.extract_value,
               uuid=ai.uuid,
               measurement_script=ai.measurement_script_name,
               extraction_script=ai.extraction_script_name,
               mass_spectrometer=ai.mass_spectrometer,
               extract_device=ai.extract_device,
               material=ai.material,
               sample=ai.sample,
               project=ai.project,
               irradiation=ai.irradiation,
               irradiation_level=ai.irradiation_level,
               irradiation_position=ai.irradiation_pos,
               tag = ai.tag,
               position = ai.position,
               analysis_timestamp = ai.analysis_timestamp,
               analysis_type = ai.analysis_type)

    def modify_analysis(self, path, message=None, branch='develop'):
        """
        commit the modification to path to the working branch
        """
        self.checkout_branch(branch)
        index = self.index
        index.add([path])
        if message is None:
            message = 'modified record {}'.format(os.path.relpath(path, self.path))
        index.commit(message)

    def _load_file_text(self, new):
        with open(new, 'r') as rfile:
            self.selected_text = rfile.read()

    def _calculate_diff_dict(self, left, right):
        left = self.get_commit(left.hexsha)
        right = self.get_commit(right.hexsha)

        ds = left.diff(right, create_patch=True)

        attrs = ['age', 'age_err',
                 'age_err_wo_j', 'age_err_wo_j_irrad',
                 'ar39decayfactor',
                 'ar37decayfactor',
                 'j', 'j_err',
                 'tag',
                 'material', 'sample',
                 ('constants', 'abundance_sensitivity', 'atm4036', 'lambda_k'),
                 ('production_ratios', 'Ca_K', 'Cl_K'),
                 ('interference_corrections', 'ca3637', 'ca3637_err', 'ca3837', 'ca3837_err', 'ca3937', 'ca3937_err',
                  'cl3638', 'cl3638_err',
                  'k3739', 'k3739_err', 'k3839', 'k3839_err', 'k4039', 'k4039_err')]

        if not isinstance(attrs, (tuple, list)):
            attrs = (attrs, )

        attr_diff = []
        for ci in ds.iter_change_type('M'):
            try:
                a = ci.a_blob.data_stream
            except Exception, e:
                print 'a', e
                continue

            try:
                b = ci.b_blob.data_stream
            except Exception, e:
                print 'b', e
                continue

            ayd = yaml.load(a)
            byd = yaml.load(b)

            # use the first analysis only
            ayd = ayd[ayd.keys()[0]]
            byd = byd[byd.keys()[0]]

            def func(ad, bd, attr):
                try:
                    av = ad[attr]
                except KeyError:
                    av = None

                try:
                    bv = bd[attr]
                except KeyError:
                    bv = None

                attr_diff.append((attr, av, bv))

            for attr in attrs:
                if isinstance(attr, (list, tuple)):
                    subdict = attr[0]
                    sa, sb = ayd[subdict], byd[subdict]
                    for ai in attr[1:]:
                        func(sa, sb, ai)
                else:
                    func(ayd, byd, attr)

            aisos = ayd['isotopes']
            bisos = byd['isotopes']
            for aisod in aisos:
                name = aisod['name']

                bisod = next((b for b in bisos if b['name'] == name), None)
                av = aisod['value']
                bv = bisod['value'] if bisod else 0
                attr_diff.append((name, av, bv))
                for a in ('baseline', 'baseline_err', 'blank',
                          'blank_err', 'ic_factor', 'ic_factor_err', 'fit'):
                    av, bv = aisod[a], bisod[a]
                    attr_diff.append(('{} {}'.format(name, a), av, bv))

        return attr_diff

    # handlers
    def _selected_hook(self, new):
        if new:
            self._load_file_text(new)

    def _dclicked_fired(self, new):
        if new:
            self.load_file_history(new)

    def _selected_branch_changed(self, new):
        if new:
            self.checkout_branch(new)


class ArArWorkspaceManager(WorkspaceManager):
    nanalyses = Property(depends_on='path, repo_updated')

    @cached_property
    def _get_nanalyses(self):
        return len(list_directory2(self.path, extension='.yaml'))

        # ============= EOF =============================================
        # def schema_diff(self, attrs):
        # """
        # show the diff for the given schema keyword `attr` between the working and master
        # """
        # repo = self._repo
        # master_commit = repo.heads.master.commit
        # working_commit = repo.heads.working.commit
        #
        #     ds = working_commit.diff(master_commit, create_patch=True)
        #     # ds = working_commit.diff(master_commit)
        #
        #     if not isinstance(attrs, (tuple, list)):
        #         attrs = (attrs, )
        #
        #     attr_diff = {}
        #     for ci in ds.iter_change_type('M'):
        #         a = ci.a_blob.data_stream
        #
        #         ayd = yaml.load(a)
        #         # print 'a', a.read()
        #         b = ci.b_blob.data_stream
        #
        #         byd = yaml.load(b)
        #         for attr in attrs:
        #
        #             try:
        #                 av = ayd[attr]
        #             except KeyError:
        #                 av = None
        #
        #             try:
        #                 bv = byd[attr]
        #             except KeyError:
        #                 bv = None
        #
        #             attr_diff[attr] = av == bv, av, bv
        #
        #     return attr_diff