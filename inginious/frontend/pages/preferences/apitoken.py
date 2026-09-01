# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" API token page """
from flask import session, request, render_template
import datetime
import zoneinfo
from datetime import timezone

from inginious.frontend.pages.utils import INGIniousAuthPage
from inginious.frontend.models import User, APIToken
from inginious.frontend.user_manager import UserManager
from inginious.frontend.accessible_time import parse_date
from inginious.frontend.pages.jwt_utils import encode_jwt



class APITokenPage(INGIniousAuthPage):
    """ Page to view or generate an API token for the user """

    def GET_AUTH(self):
        """ GET request """


        return self.show_page()

    def POST_AUTH(self):
        """ POST request, generates a new token for the user """


        user = User.objects(username=session["username"]).first()

        # generate and save a new token in a single request
        if "save" in request.form:
            description = request.form.get("description")

            if description == "" :
                return self.show_page(errors=["Description is required to generate a token."])

            expires_in = request.form.get("expires_in", "")

            if expires_in == "custom":
                custom_date = request.form.get("custom_expiration")
                try:
                    expiration = parse_date(custom_date, default=None)
                except (TypeError, ValueError, zoneinfo.ZoneInfoNotFoundError):
                    return self.show_page(errors=["Please provide a valid custom expiration date."])

                now = datetime.datetime.now(tz=timezone.utc)
                if expiration <= now:
                    return self.show_page(errors=["The expiration date must be in the future."])
            else:
                try:
                    days = int(expires_in)
                except (TypeError, ValueError):
                    return self.show_page(errors=["Please select a valid expiration duration."])

                expiration = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(days=days)

            payload = {
                "username": user.username,
                "exp": expiration.timestamp(),
            }
            token = encode_jwt(payload)

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