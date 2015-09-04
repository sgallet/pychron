# # ===============================================================================
# # Copyright 2013 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# # ===============================================================================
#
# # ============= enthought library imports =======================
# from pyface.action.action import Action
# from pyface.tasks.action.task_action import TaskAction
#
# # ============= standard library imports ========================
# # ============= local library imports  ==========================
# from pychron.envisage.resources import icon
#
#
# class VCSAction(Action):
#     pass
#
# class PushVCSAction(VCSAction):
#     image = icon('arrow_up.png')
#     name='Push'
#     def perform(self, event):
#         app=event.task.window.application
#         task=app.open_task('pychron.processing.vcs')
#         task.initiate_push()
#
#
# class PullVCSAction(Action):
#     name='Pull'
#     image = icon('arrow_down.png')
#
#     def perform(self, event):
#         app = event.task.window.application
#         task = app.open_task('pychron.processing.vcs')
#         task.initiate_pull()
#
#
# class CommitVCSAction(TaskAction):
#     name='Commit'
#     method='commit'
#
#
# class ShareVCSAction(TaskAction):
#     name='Share'
#     method='share'
#
# class MigrateProjectRepositoriesAction(TaskAction):
#     name='Migrate'
#     method='migrate_project_repositories'
#
# # ============= EOF =============================================
#
