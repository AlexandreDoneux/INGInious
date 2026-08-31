# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" API token page """
from flask import current_app, session, request, render_template
import jwt
import datetime
from datetime import timezone

from inginious.frontend.pages.utils import INGIniousAuthPage
from inginious.frontend.models import User, APIToken
from inginious.frontend.user_manager import UserManager



class APITokenPage(INGIniousAuthPage):
    """ Page to view or generate an API token for the user """

    def GET_AUTH(self):
        """ GET request """


        return self.show_page()

    def POST_AUTH(self):
        """ POST request, generates a new token for the user """

        api_jwt_secret = current_app.config.get('API_JWT_SECRET')
        api_jwt_algorithm = current_app.config.get('API_JWT_ALGORITHM')
        api_jwt_lifetime = datetime.timedelta(days=current_app.config.get('API_JWT_LIFETIME'))

        user = User.objects(username=session["username"]).first()

        # generate and save a new token in a single request
        if "save" in request.form:
            description = request.form.get("description")

            if description == "" :
                return self.show_page(errors=["Description is required to generate a token."])

            expiration = datetime.datetime.now(tz=timezone.utc) + api_jwt_lifetime
            payload = {
                "username": user.username,
                "exp": expiration.timestamp(),
            }
            token = jwt.encode(payload, api_jwt_secret, algorithm=api_jwt_algorithm)

            new_token = APIToken(token=UserManager.hash_password(token), expires=expiration, description=description)
            user.apitokens[new_token.token_id] = new_token
            user.save()

            return self.show_page(generated_token=token)

        # invalidates a token
        if "delete" in request.form:
            token_id_to_delete = request.form.get('token_id')
            user.apitokens.pop(token_id_to_delete, None)
            user.save()


        return self.show_page()

    def show_page(self, generated_token=None, errors=None):
        """ Prepares and shows the course marketplace """
        if errors is None:
            errors = []

        user = User.objects(username=session["username"]).first()
        # Exclude the token hash from the data sent to the template
        token_list = [
            {"token_id": token.token_id, "description": token.description, "expires": token.expires}
            for token in user.apitokens.values()
        ]

        return render_template("apitoken.html", errors=errors, generated_token=generated_token, token_list=token_list)