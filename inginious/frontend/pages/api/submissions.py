# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Submissions """

import flask
from flask import current_app, request

from inginious.frontend.courses import Course
from inginious.frontend.pages.api._api_page import APIAuthenticatedPage, APINotFound, APIForbidden, APIInvalidArguments, APIError, \
    stream_json_array
from inginious.frontend.models.submission import Submission


streaming_threshold = 500

def _get_submissions(username, submission_manager, user_manager, courseid, taskid, submissionid=None):
    """
        Helper for the GET methods of the two following classes
    """

    try:
        course = Course.get(courseid)
    except:
        raise APINotFound("Course not found")

    if not user_manager.course_is_open_to_user(course, username, lti=False):
        raise APIForbidden("You are not registered to this course")

    try:
        task = course.get_task(taskid)
    except:
        raise APINotFound("Task not found")

    if submissionid is None:
        submissions = submission_manager.get_user_submissions(course, task, username)
    else:
        try:
            submissions = [submission_manager.get_submission(submissionid, user_check=False)]
        except:
            raise APINotFound("Submission not found")
        if submissions[0]["taskid"] != task.get_id() or submissions[0]["courseid"] != course.get_id():
            raise APINotFound("Submission not found")

    def serialize(submission):
        """
        Generator for stream_json_array() to stream the response instead of building the whole list in memory.
        """
        submission = submission_manager.get_feedback_from_submission(
            submission,
            show_everything=user_manager.has_staff_rights_on_course(course, username)
        )
        data = {
            "id": str(submission["id"]),
            "submitted_on": submission["submitted_on"].isoformat(),
            "status": submission["status"]
        }

        if submission["status"] == "done":
            data["grade"] = submission.grade
            data["result"] = submission.result
            data["feedback"] = submission.text
            data["problems_feedback"] = submission.problems

        return data

    if len(submissions) > streaming_threshold:
        return stream_json_array(serialize(s) for s in submissions)

    return 200, [serialize(s) for s in submissions]


class APISubmissionSingle(APIAuthenticatedPage):
    r"""
        Endpoint
          ::

            /api/v1/courses/[a-zA-Z_\-\.0-9]+/[a-zA-Z_\-\.0-9]+/my_submissions/[a-zA-Z_\-\.0-9]+

    """

    def API_GET(self, courseid, taskid, submissionid):  # pylint: disable=arguments-differ
        """
            List all the submissions that the connected user made. Returns list of the form

            ::

                [
                    {
                        "id": "submission_id1",
                        "submitted_on": "date",
                        "status" : "done",          #can be "done", "waiting", "error" (execution status of the task).
                        "grade": 0.0,
                        "result" : "success"        #only if status=done. Result of the execution.
                        "feedback": ""              #only if status=done. the HTML global feedback for the task
                        "problems_feedback":        #only if status=done. HTML feedback per problem. Some pid may be absent.
                        {
                            "pid1": "feedback1",
                            #...
                        }
                    }
                    #...
                ]

            If you use the endpoint /api/v0/courses/the_course_id/tasks/the_task_id/submissions/submissionid,
            this dict will contain one entry or the page will return 404 Not Found.

            The raw input submitted by the student is not included here. Use the dedicated
            /api/v1/submissions/<submissionid>/input endpoint to download it.
        """
        username = flask.g.user.username

        return _get_submissions(username, self.submission_manager, self.user_manager, courseid, taskid, submissionid)


class APISubmissions(APIAuthenticatedPage):
    r"""
        Endpoint
          ::

            /api/v1/courses/[a-zA-Z_\-\.0-9]+/[a-zA-Z_\-\.0-9]+/my_submissions

    """

    def API_GET(self, courseid, taskid):  # pylint: disable=arguments-differ
        """
            List all the submissions that the connected user made. Returns dicts in the form

            ::

                [
                    {
                        "id": "submission_id1",
                        "submitted_on": "date",
                        "status" : "done",          #can be "done", "waiting", "error" (execution status of the task).
                        "grade": 0.0,
                        "result" : "success"        #only if status=done. Result of the execution.
                        "feedback": ""              #only if status=done. the HTML global feedback for the task
                        "problems_feedback":        #only if status=done. HTML feedback per problem. Some pid may be absent.
                        {
                            "pid1": "feedback1",
                            #...
                        }
                    }
                    #...
                ]

            If you use the endpoint /api/v0/courses/the_course_id/tasks/the_task_id/submissions/submissionid,
            this dict will contain one entry or the page will return 404 Not Found.

            The raw input submitted by the student is not included here. Use the dedicated
            /api/v1/submissions/<submissionid>/input endpoint to download it.
        """
        username = flask.g.user.username

        return _get_submissions(username, self.submission_manager, self.user_manager, courseid, taskid)

    def API_POST(self, courseid, taskid):  # pylint: disable=arguments-differ
        """
            Creates a new submissions. Takes as (POST) input the key of the subproblems, with the value assigned each time.
            Allow for application/json input or multipart/form-data input. For file input problems, the form-data input is required.

            Returns

            - an error 400 Bad Request if all the input is not (correctly) given,
            - an error 403 Forbidden if you are not allowed to create a new submission for this task
            - an error 404 Not found if the course/task id not found
            - an error 500 Internal server error if the grader is not available,
            - 200 Ok, with {"submissionid": "the submission id"} as output.
        """

        try:
            course = Course.get(courseid)
        except:
            raise APINotFound("Course not found")

        username = flask.g.user.username

        if not self.user_manager.course_is_open_to_user(course, username, False):
            raise APIForbidden("You are not registered to this course")

        try:
            task = course.get_task(taskid)
        except:
            raise APINotFound("Task not found")

        self.user_manager.user_saw_task(username, courseid, taskid)

        # Verify rights
        if not self.user_manager.task_can_user_submit(course, task, username, False):
            raise APIForbidden("You are not allowed to submit for this task")

        if flask.request.is_json:
            user_input = flask.request.get_json()

        else:
            user_input = flask.request.form.copy()
            for problem in task.get_problems():
                pid = problem.get_id()
                if problem.input_type() == list:
                    user_input[pid] = flask.request.form.getlist(pid)
                elif problem.input_type() == dict:
                    user_input[pid] = flask.request.files.get(pid)
                else:
                    user_input[pid] = flask.request.form.get(pid)

        user_input = task.adapt_input_for_backend(user_input)

        if not task.input_is_consistent(user_input, current_app.config['ALLOWED_FILE_EXTENSIONS'],
                                        current_app.config['MAX_FILE_SIZE']):
            raise APIInvalidArguments()

        # Get debug info if the current user is an admin
        debug = self.user_manager.has_admin_rights_on_course(course, username)


        # Start the submission
        try:
            submissionid, _ = self.submission_manager.add_job(course, task, user_input, course.get_task_dispenser(), username, debug)
            return 200, {"submissionid": str(submissionid)}
        except Exception as ex:
            raise APIError(500, str(ex))


class APISubmissionsCourse(APIAuthenticatedPage):
    """
        Endpoints
            ::

                /api/v1/courses/[a-zA-Z_\-\.0-9]+/submissions

                /api/v1/courses/[a-zA-Z_\-\.0-9]+/[a-zA-Z_\-\.0-9]+/submissions
    """

    def API_POST(self, courseid, taskid
    =None):
        """
            List all the submissions from a course that were evaluated (done). Or all submissions for a particular task in case a task id is given.
            Only accessible to staff members of the course.
            Returns a 200 OK if the endpoint is reachable and the user has access to it.
            Returns 403 Forbidden if the user does not have access to the course/task.
            Returns 404 Not Found if the course does not exist.

            Returns list of the form :
            ::

                [
                    {
                        "id": "submission_id1",
                        "courseid": "submission_id1",
                        "taskid": "date",
                        "username" : ["user1", "user2", ...],          #list of users related to that submissions (multiple users in case of a group submission)
                        "submitted_on": "2026-06-23T15:01:44Z",     #date in the ISO 8601 format
                        "result" : "success"        #can be success, failure, crash (execution status of the task).
                        "grade": 0.0,
                        "stderr": "stderr output of the submission",
                        "stdout": "stdout output of the submission",
                    }
                ]

            The raw input submitted by the student (file contents, code, QCM answers, etc.) is not included in this
            list.
            Use the dedicated /api/v1/submissions/<submissionid>/input endpoint
            (accessible to staff members or to the author (or users in the group if a group submission) to download the
            raw input of one particular submission.

            This endpoint takes a token in the header (accessible from your account settings) and a JSON body with the following fields :
            - select: "all" (default), "best", "last" : select all submissions, the best submission per student, or the last submission per student
            - username: a list of usernames to filter the submissions. If none is provided (or it is empty), the submissions for all users are returned

            example of a call to this endpoint using curl: :
                curl -X POST "http://localhost:8080/api/v1/courses/tutorial/submissions"
                -H "Authorization: Bearer <token>"
                -H "Content-Type: application/json"  -d '{ "select": "last", "username" : ["user1"] }'

            Note: if the number of matching submissions exceeds an internal threshold (500), the response is streamed
            as a JSON array (chunked transfer-encoding) instead of being returned all at once, so that large
            courses/tasks do not need to be fully loaded in memory on the server, and clients can start processing
            submissions as they arrive.
        """

        username = flask.g.user.username

        try:
            course = Course.get(courseid)
        except:
            raise APINotFound("Course not found")
        try:
            _ = course.get_task(taskid) if taskid else None
        except:
            raise APINotFound("Task not found")

        if not self.user_manager.has_staff_rights_on_course(course, username, include_superadmins=True):
            raise APIForbidden("You cannot access this course")

        data = request.get_json(silent=True) or {}

        select = data.get("select", "all")
        usernames = data.get("username", None)

        if select not in ("all", "best", "last"):
            raise APIInvalidArguments()
        if usernames is not None and not isinstance(usernames, list):
            raise APIInvalidArguments()

        query = {"courseid": courseid, "status": "done"} if taskid is None else {"courseid": courseid, "taskid": taskid, "status": "done"}
        if usernames:
            query["username__in"] = usernames

        if select == "best":
            cursor = Submission.objects(**query) \
                .only("id", "courseid", "taskid", "username", "submitted_on", "result", "grade", "stderr", "stdout") \
                .order_by("-grade", "-submitted_on")
        else:  # select == "last" or select == "all"
            cursor = Submission.objects(**query) \
                .only("id", "courseid", "taskid", "username", "submitted_on", "result", "grade", "stderr", "stdout") \
                .order_by("-submitted_on")

        def serialize(s):
            return {
                "id": str(s.id),
                "courseid": s.courseid,
                "taskid": s.taskid,
                "username": s.username,
                "submitted_on": s.submitted_on.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "result": s.result,
                "grade": s.grade,
                "stderr": s.stderr,
                "stdout": s.stdout,
            }

        def submissions_iter():
            """
            Generator for stream_json_array() to stream the response instead of building the whole list in memory.
            Reject duplicate submissions for "best" and "last".
            """
            seen = set()
            for s in cursor:
                if select in ("best", "last"):
                    key = (tuple(sorted(s.username)), s.taskid)
                    if key in seen:
                        continue
                    seen.add(key)
                yield serialize(s)

        if cursor.count() > streaming_threshold:
            return stream_json_array(submissions_iter())

        return 200, list(submissions_iter())


class APISubmissionInput(APIAuthenticatedPage):
    r"""
        Endpoint
          ::

            /api/v1/submissions/<submissionid>/input

    """

    def GET(self, submissionid):
        """
            Download the raw input of a single submission.

            Unlike the other submissions endpoints, this one does not go through the standard JSON
            conversion: it directly returns the raw content of the submission's input.

            The input is returned as-is (Content-Type: application/octet-stream): it is the single BSON-encoded
            blob that is stored for in the database. Accessible to any user listed in the submission's "username" field
            (any member of a group submission), or to a staff member of the course.

            The input is formatted as follows, with additional metadata and the different problems' input :
            {
                "@username" : "user1",
                "@email" : "user1@email.com",
                "@lang" : "en",
                "@time": "2026-06-23 15:01:44.706579+00:00",
                "@attempts": "5",
                "@random": [],
                "@state": "",

                "code_problem": "print(\"Hello world!\")",
                "file_problem": {
                    "filename": "file1.zip",
                    "value": "sDBBQAVcbcAWpn2wFoAQAAYi9maXp6YnV6e......DQAH4NsBagbcAWrg2wFqdXgLAAEE6AMAAAToAwAAUEsFBgAAAAAEAAQAVgEAAEACAAAAAA=="
                    },
                "qcm_problem": {
                    # number of the selected answer for each question, starting from 0.
                    "qcm1": "0",
                    "qcm2": "2",
                    "qcm3": "1",
                    ...
            }

            Returns 403 Forbidden if the user is not allowed to access this submission, and 404 Not Found if the
            course/task/submission does not exist.
        """
        try:
            return self._verify_authentication(self._get_input, (submissionid,), {})
        except APIError as error:
            return error.send()

    def _get_input(self, submissionid):
        username = flask.g.user.username

        try:
            submission = self.submission_manager.get_submission(submissionid, user_check=False)
        except:
            raise APINotFound("Submission not found")

        if submission is None:
            raise APINotFound("Submission not found")

        course = Course.get(submission.courseid)
        is_staff = self.user_manager.has_staff_rights_on_course(course, username, include_superadmins=True)
        is_owner = username in submission.username
        if not (is_staff or is_owner):
            raise APIForbidden("You are not allowed to access this submission")

        submission.input.seek(0)

        def submission_generator():
            while True:
                chunk = submission.input.read(64 * 1024) # 64 KB chunks
                if not chunk:
                    break
                yield chunk

        response = flask.Response(submission_generator(), mimetype="application/octet-stream")
        response.headers["Content-Disposition"] = 'attachment; filename="{}.bson"'.format(submissionid)
        return response


