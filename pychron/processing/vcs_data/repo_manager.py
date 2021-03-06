#===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from cStringIO import StringIO
from git.exc import GitCommandError

from traits.api import Any, Directory

#============= standard library imports ========================
import os
from git import Repo, Diff
# from dulwich.repo import Repo

#============= local library imports  ==========================
from pychron.loggable import Loggable


class RepoManager(Loggable):
    """
        manage a local git repository

    """

    _repo=Any
    root=Directory

    def add_repo(self, localpath):
        """
            add a blank repo at ``localpath``
        """
        repo, existed=self._add_repo(localpath)
        self._repo=repo
        self.root=localpath
        return existed

    def create_remote(self, url, name='origin', repo=None):
        repo=self._get_repo(repo)
        if repo:
            #only create remote if doesnt exist
            if not hasattr(repo.remotes, name):
            #     url='{}:jir812@{}:{}.git'.format(user, host, repo_name)
                repo.create_remote(name, url)
                pass

    #git protocol
    def pull(self, repo=None, branch='master', remote='origin', handled=True):
        """
            fetch and merge
        """
        repo = self._get_repo(repo)
        remote=self._get_remote(repo, remote)
        if remote:
            try:
                repo.git.pull(remote, branch)
            except GitCommandError, e:
                self.debug(e)
                if not handled:
                    raise e

    def push(self, repo=None, branch='master', remote='origin'):
        repo=self._get_repo(repo)

        rr = self._get_remote(repo, remote)
        if rr:
            repo.git.push(remote,branch)

    def commit(self, msg, repo=None):
        index=self._get_repo_index(repo)
        if index:
            index.commit(msg)

    def add(self, p, msg=None, **kw):
        if msg is None:
            name=p.replace(self.root,'')
            if name.startswith('/'):
                name=name[1:]

            msg='added {}'.format(name)

        self._add_to_repo(p, msg, **kw)

    #repo manager protocol
    def get_local_changes(self, repo=None):
        repo=self._get_repo(repo)
        diff_str=repo.git.diff( '--full-index')
        patches=map(str.strip, diff_str.split('diff --git'))
        patches=['\n'.join(p.split('\n')[2:]) for p in patches[1:]]

        diff_str=StringIO(diff_str)
        diff_str.seek(0)
        index=Diff._index_from_patch_format(repo, diff_str)

        return index, patches

    def get_untracked(self):
        return self._repo.untracked_files

    def is_dirty(self, repo=None):
        repo=self._get_repo(repo)
        return repo.is_dirty()

    #private

    def _add_to_repo(self, p, msg, repo=None, commit=True):
        # repo=self._get_repo(repo)
        # if repo:
        index=self._get_repo_index(repo)
        if index:
            # name = os.path.basename(p)
            index.add([p])
            if commit:
                index.commit(msg)

    def _get_remote(self,repo, remote):
        repo=self._get_repo(repo)
        if repo:
            return getattr(repo.remotes, remote)

    def _get_repo_index(self, repo):
        repo=self._get_repo(repo)
        if repo:
            return repo.index

    def _get_repo(self, repo):
        if repo is None:
            # repo=self.root
            repo = self._repo
        # repo=Repo(repo)
        return repo

    def _add_repo(self, root):
        existed=True
        if not os.path.isdir(root):
            os.mkdir(root)
            existed=False

        gitdir=os.path.join(root, '.git')
        if not os.path.isdir(gitdir):
            repo = Repo.init(root)
            existed = False
        else:
            repo = Repo(root)

        return repo, existed

#============= EOF =============================================
