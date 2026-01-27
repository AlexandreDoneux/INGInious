# -*- coding: utf-8 -*-
#
#   Copyright (c) 2017 Ludovic Taffin
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#   JPLAG plugin for INGInious
import os
import io
import logging
import requests
import tarfile

from flask import request, render_template
from werkzeug.exceptions import NotFound

from inginious.frontend.pages.course_admin.utils import INGIniousAdminPage
from inginious.common.base import load_json_or_yaml
from inginious.frontend.courses import Course
from inginious.frontend.models import Submission
from inginious.client.client_sync import ClientSync

""" A plugin that uses JPlag to detect similar code """

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")


def add_admin_menu(course):  # pylint: disable=unused-argument
    """ Add a menu for jplag analyze in the administration """
    return ('jplagselectpage', '<i class="fa fa-search fa-fw"></i>&nbsp; JPlag')

def get_submission_archive(submissions, archive_file):
    file_to_put = {}

    # Build unique base paths per submission
    file_to_put = {}
    for submission in submissions:
        # generate all paths where the submission must belong
        for base_path in submission.username:
            path, i = base_path, 1
            while path in file_to_put:
                path = base_path + "-" + str(i)
                i += 1
            file_to_put[path] = submission

    # Create the final tar.gz
    with tarfile.open(fileobj=archive_file, mode="w:gz") as tar:

        for base_path, submission in file_to_put.items():

            # If the submission has an archive attached
            if submission.archive:
                # Read FileField contents into memory
                archive_bytes = submission.archive.read()
                archive_buffer = io.BytesIO(archive_bytes)

                # Open the submission's archive
                with tarfile.open(fileobj=archive_buffer, mode="r:*") as subtar:
                    for member in subtar.getmembers():
                        # Skip directories without content
                        subfile = subtar.extractfile(member)
                        if subfile is None:
                            continue

                        # Rewrite the path inside the combined archive
                        member.name = f"{base_path}/archive/{member.name}"

                        tar.addfile(member, subfile)

    # Reset cursor so caller can read it
    archive_file.seek(0)
    return archive_file


def init(plugin_manager, client, config):
    """ Init the plugin """

    server = config.get('host')
    port = config.get('port')
    path = config.get('path')
    _logger = logging.getLogger("inginious.webapp.plugins.jplagselectpage")

    # building jplag container


    class JPLAGSelectPage(INGIniousAdminPage):

        def GET_AUTH(self, courseid):
            """GET REQUEST"""
            _logger.info("Starting JPlag selection")
            try:
                course = Course.get(courseid)
            except:
                raise NotFound(description=_("Course not found."))

            tasks = course.get_tasks()
            _logger.info("Rendering task selection")
            return render_template("jplag/templates/jplag_select_task.html", template_folder=PATH_TO_TEMPLATES,
                                               course=courseid, tasks=tasks)

    class JPLAGPage(INGIniousAdminPage):
        """ A JPlag page """

        def GET_AUTH(self, courseid, taskid):
            """GET REQUEST"""

            subs_qs = Submission.objects(courseid=courseid, taskid=taskid).order_by('submitted_on')
            subs = [s.to_mongo().to_dict() for s in subs_qs]
            res = {elem['username'][0]: elem for elem in subs}

            return render_template("jplag/templates/jplagselector.html", template_folder=PATH_TO_TEMPLATES, subs=res)

        def POST_AUTH(self, courseid, taskid):
            """ POST REQUEST """
           # for the moment try to run a basic job with a specific environment,

            client_sync = ClientSync(client)

            course = None
            task = None
            task_input = {'@attempts': '1', '@email': 'superadmin@inginious.org', '@lang': 'en', '@random': (), '@state': '', '@time': '2026-02-02 16:00:46.922800+00:00', '@username': 'superadmin', 'thecode': 'print("hey")'}
            # task_input => inputdata :  contains user data, task data (attempts, submission time, random values, etc), and the code inputted by the user for the task
            # use input_data as a way to pass parameters to the jplag ?

            result, grade, problems, tests, custom, state, archive, stdout, stderr = client_sync.new_job(0, course,
                                                                                                         task,
                                                                                                         task_input,
                                                                                                         "jplag",
                                                                                                         "Plugin - JPLAG")

            print(result)


            # temporary render. Page will need to be made better
            return render_template("jplag/templates/jplagresult.html", template_folder=PATH_TO_TEMPLATES,url="")

    plugin_manager.add_page("/jplag/<courseid>/<taskid>", JPLAGPage.as_view("jplagpage"))
    plugin_manager.add_page("/jplagselecttask/<courseid>/", JPLAGSelectPage.as_view("jplagselectpage"))
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    plugin_manager.add_template_prefix("jplag", PATH_TO_PLUGIN)
