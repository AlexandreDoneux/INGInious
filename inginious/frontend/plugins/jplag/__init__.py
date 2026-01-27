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

""" A plugin that uses JPlag to detect similar code """

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")


def add_admin_menu(course):  # pylint: disable=unused-argument
    """ Add a menu for jplag analyze in the administration """
    return ('../../jplagselecttask/' + course.get_id() + '/', '<i class="fa fa-search fa-fw"></i>&nbsp; JPlag')

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


def init(plugin_manager, config):
    """ Init the plugin """

    server = config.get('host')
    port = config.get('port')
    path = config.get('path')
    _logger = logging.getLogger("inginious.webapp.plugins.jplagselectpage")

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
            list_of_sub_id = []
            x = request.form
            template_file = request.files['templateFile']
            old_sub_file = request.files['archiveFile']
            exclude_file = request.files['excludeFile']
            for key in x:
                value = x[key]
                if value == "on" and key != 'nextyear' and key != 'addarchives':
                    list_of_sub_id.append(key)

            subs = [self.submission_manager.get_submission(x, False) for x in list_of_sub_id]

            config = load_json_or_yaml("configuration.yaml") # TODO : change way to access task_directory, or even not use task_directory at all. We previously used the backup directory
            archive = get_submission_archive(subs, open(config["tasks_directory"] + "/test.tar", "wb+")) # tester temporairement avec dossier de tâches

            r = requests.post('http://' + server + ':' + str(port) + '/' + path,
                              files={'sub.tar': archive,
                                     'courseId': courseid,
                                     'taskId': taskid,
                                     'lang': x['selectLang'] if 'selectLang' in x else 'Python',
                                     'template': template_file.read() if template_file is not None else '',
                                     'archi': old_sub_file.read() if old_sub_file is not None else '',
                                     'exclude': exclude_file.read() if exclude_file is not None else '',
                                     'percentage': x['percentage'] if 'percentage' in x else 1,
                                     'nyear': x['nextyear'] if 'nextyear' in x else "no",
                                     'check_archives': x['addarchives'] if 'addarchives' in x else "no"})
            if r.status_code == 200:
                return render_template("jplag/templates/jplagresult.html", template_folder=PATH_TO_TEMPLATES,
                                                   url=r.content.decode('UTF-8'))
            else:
                return r.content.decode('utf-8')

            archive.close()

    plugin_manager.add_page("/jplag/<courseid>/<taskid>", JPLAGPage.as_view("jplagpage"))
    plugin_manager.add_page("/jplagselecttask/<courseid>/", JPLAGSelectPage.as_view("jplagselectpage"))
    plugin_manager.add_hook('course_admin_menu', add_admin_menu)
    plugin_manager.add_template_prefix("jplag", PATH_TO_PLUGIN)
