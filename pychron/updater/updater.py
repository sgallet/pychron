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
from datetime import datetime, timedelta
import os
import urllib2
from apptools.preferences.preference_binding import bind_preference
import sys
from git import GitCommandError
from traits.api import HasTraits, Button, Bool, Str, Property, List
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.datetime_tools import get_datetime
from pychron.core.ui.progress_dialog import myProgressDialog
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.paths import r_mkdir
from pychron.updater.branch_view import ManageBranchView
from pychron.updater.commit_view import CommitView, UpdateGitHistory, ManageCommitsView


class Updater(Loggable):
    check_on_startup = Bool
    branch = Str
    remote = Str
    _repo = None
    _editable = False

    all_branches = List
    branches = List
    delete_enabled = Property(depends_on='edit_branch')
    edit_branch = Str
    delete_button = Button('Delete')
    build_button = Button
    checkout_branch_button = Button

    def bind_preferences(self):
        for a in ('check_on_startup', 'branch', 'remote'):
            bind_preference(self, a, 'pychron.update.{}'.format(a))

    def test_origin(self):
        if self.remote:
            return self._validate_origin(self.remote)

    def manage_branches(self):
        self._refresh_branches()
        v = ManageBranchView(model=self)
        v.edit_traits(kind='livemodal')

    def manage_version(self):
        repo = self._get_working_repo()

        txt = ''
        try:
            txt = repo.git.rev_list('origin/{}'.format(self.branch),
                                    since=datetime.now() - timedelta(weeks=30),
                                    branches=self.branch)
        except GitCommandError:
            try:
                txt = repo.git.rev_list(self.branch,
                                        since=datetime.now() - timedelta(weeks=30),
                                        branches=self.branch)
            except GitCommandError:
                pass

        commits = txt.split('\n')
        local_commit, remote_commit = self._get_local_remote_commits()

        hexsha = self._get_selected_hexsha(commits, local_commit, remote_commit,
                                           view_klass=ManageCommitsView,
                                           auto_select=False,
                                           tags=repo.tags,
                                           # pass to model
                                           show_behind=False, )
        if hexsha:
            self._checkout(hexsha)

    def check_for_updates(self, inform=False):
        branch = self.branch
        remote = self.remote
        if remote and branch:
            if self._validate_origin(remote):
                if self._validate_branch(branch):
                    lc, rc = self._check_for_updates()
                    hexsha = self._out_of_date(lc, rc)
                    if hexsha:
                        origin = self._repo.remotes.origin
                        self.debug('pulling changes from {} to {}'.format(origin.url, branch))

                        self._repo.git.pull(origin, hexsha)

                        self._build(branch, rc)
                        if self.confirmation_dialog('Restart?'):
                            os.execl(sys.executable, *([sys.executable] + sys.argv))
                    elif hexsha is None:
                        if inform:
                            self.information_dialog('Application is up-to-date')
                    else:
                        self.info('User chose not to update at this time')
            else:
                self.warning_dialog('{} not a valid Github Repository. Unable to check for updates'.format(remote))

    def build(self):
        lc = self._get_local_commit()
        self._build(self.branch, lc)

    # private
    # handlers
    def _checkout_branch_button_fired(self):
        self._checkout(self.branch)
        self._refresh_branches()

    def _build_button_fired(self):
        b = self.branch
        repo = self._get_working_repo()
        branch = getattr(repo.branches, b)
        branch.checkout()
        self.debug('Build button branch name={}, commit={}'.format(b, branch.commit))
        self._build(b, branch.commit)

    def _delete_button_fired(self):
        repo = self._get_working_repo()
        repo.delete_head(self.edit_branch)
        self._refresh_branches()

    def _refresh_branches(self):
        repo = self._get_working_repo()
        rnames = [ri.name for ri in repo.remotes.origin.refs]
        rnames = filter(lambda x: x.startswith('origin/release'), rnames)
        branches = [bi.name for bi in repo.branches] + ['origin/master', 'origin/develop'] + rnames
        self.all_branches = branches

        branches = [bi for bi in branches if bi != self.branch]
        self.branches = branches

    def _checkout(self, branch_name, hexsha=None):
        if hexsha is None:
            hexsha = 'HEAD'
        else:
            branch_name = '{}-{}'.format(branch_name, hexsha[:7])

        repo = self._get_working_repo()
        try:
            branch = getattr(repo.branches, branch_name)
        except AttributeError:
            branch = repo.create_head(branch_name, commit=hexsha)

        branch.checkout()
        self.branch = branch_name

    def _get_dest_root(self):
        p = os.path.abspath(__file__)
        self.debug(p)
        while 1:
            self.debug(p)
            if os.path.basename(p) == 'Contents':
                break
            else:
                p = os.path.dirname(p)
            if len(p) == 1:
                break
        return p

    def _build(self, branch, commit):

        # get the version number from version.py
        version = self._extract_version()

        pd = myProgressDialog(max=5200,
                              title='Builing Application. '
                                    'Version={} Branch={} ({})'.format(version, branch, commit.hexsha[:7]),
                              can_cancel=False)
        pd.open()
        pd.change_message('Building application')

        self.info('building application. version={}'.format(version))
        self.debug('building egg from {}'.format(self._repo.working_dir))

        dest = self._get_dest_root()
        self.debug('moving egg to {}'.format(dest))

        from pychron.updater.packager import make_egg, copy_resources

        pd.change_message('Building Application')
        with pd.stdout():
            make_egg(self._repo.working_dir, dest, 'pychron', version)
            # build egg and move into destination
            if dest.endswith('Contents'):
                make_egg(self._repo.working_dir, dest, 'pychron', version)

                self.debug('------------- egg complete ----------------')

            pd.change_message('Copying Resources')
            if dest.endswith('Contents'):
                copy_resources(self._repo.working_dir, dest, self.application.shortname)
            self.debug('------------- copy resources complete -----------')

    def _extract_version(self):
        import imp

        p = os.path.join(self._repo.working_dir, 'pychron', 'version.py')
        ver = imp.load_source('version', p)
        return ver.__version__

    def _fetch(self, branch):
        repo = self._get_working_repo()
        origin = repo.remotes.origin
        try:
            repo.git.fetch(origin, branch)
        except GitCommandError, e:
            self.warning('Failed to fetch. {}'.format(e))

    def _validate_branch(self, name):
        """
        check that the repo's branch is name

        if not ask user if its ok to checkout branch
        :param name:
        :return:
        """

        repo = self._get_working_repo()
        active_branch_name = repo.active_branch.name
        if active_branch_name != name:
            self.warning('branches do not match')
            if self.confirmation_dialog(
                    'The branch specified in Preferences does not match the branch in the build directory.\n'
                    'Preferences branch: {}\n'
                    'Build branch: {}\n'
                    'Do you want to proceed?'.format(name, active_branch_name)):
                self.info('switching from branch: {} to branch: {}'.format(active_branch_name, name))
                self._fetch(name)
                branch = self._get_branch(name)

                branch.checkout()

                return True
        else:
            self._fetch(name)
            return True

    def _validate_origin(self, name):
        try:
            cmd = 'https://github.com/{}'.format(name)
            urllib2.urlopen(cmd)
            return True
        except BaseException:
            return

    def _check_for_updates(self):
        branchname = self.branch
        self.debug('checking for updates on {}'.format(branchname))
        local_commit, remote_commit = self._get_local_remote_commits()

        self.debug('local  commit ={}'.format(local_commit))
        self.debug('remote commit ={}'.format(remote_commit))
        self.application.set_revisions(local_commit, remote_commit)
        return local_commit, remote_commit

    def _out_of_date(self, lc, rc):
        if rc and lc != rc:
            self.info('updates are available')
            if not self.confirmation_dialog('Updates are available. Install and Restart?'):
                return False

            txt = self._repo.git.rev_list('--left-right', '{}...{}'.format(lc, rc))
            commits = [ci[1:] for ci in txt.split('\n')]
            return self._get_selected_hexsha(commits, lc, rc)

    def _get_branch(self, name):
        repo = self._get_working_repo()
        try:
            branch = getattr(repo.heads, name)
        except AttributeError:
            oref = repo.remotes.origin.refs[name]
            branch = repo.create_head(name, commit=oref.commit)
        return branch

    def _get_local_remote_commits(self):

        repo = self._get_working_repo()

        branchname = self.branch

        origin = repo.remotes.origin
        try:
            oref = origin.refs[branchname]
            remote_commit = oref.commit
        except IndexError:
            remote_commit = None

        branch = self._get_branch(branchname)

        local_commit = branch.commit
        return local_commit, remote_commit

    def _get_local_commit(self):
        repo = self._get_working_repo()
        branchname = self.branch
        branch = getattr(repo.heads, branchname)
        return branch.commit

    def _get_selected_hexsha(self, commits, lc, rc, view_klass=None, auto_select=True,
                             tags=None, **kw):
        if view_klass is None:
            view_klass = CommitView

        lha = lc.hexsha[:7] if lc else ''
        rha = rc.hexsha[:7] if rc else ''
        ld = get_datetime(float(lc.committed_date)).strftime('%m-%d-%Y')

        rd = get_datetime(float(rc.committed_date)).strftime('%m-%d-%Y') if rc else ''

        n = len(commits)
        h = UpdateGitHistory(n=n, branchname=self.branch,
                             local_commit='{} ({})'.format(ld, lha),
                             head_hexsha=lc.hexsha,
                             latest_remote_commit='{} ({})'.format(rd, rha),
                             **kw)

        repo = self._repo
        commits = [repo.commit(i) for i in commits]
        h.set_items(commits, auto_select=auto_select)
        if tags:
            h.set_tags(tags)

        cv = view_klass(model=h)
        info = cv.edit_traits()
        if info.result:
            if h.selected:
                return h.selected.hexsha

    def _get_working_repo(self):
        if not self._repo:
            from git import Repo

            p = paths.build_repo
            if not os.path.isdir(p):
                r_mkdir(p)
                url = 'https://github.com/{}.git'.format(self.remote)
                repo = Repo.clone_from(url, p)
            else:
                repo = Repo(p)
            self._repo = repo
        return self._repo

    def _get_delete_enabled(self):
        return not (self.branch == self.edit_branch or self.edit_branch.startswith('origin'))

# ============= EOF =============================================



