# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from ..web.route import Route
from ..schemas.version import VERSION_SCHEMA
from ..version import __version__
from aiohttp.web import HTTPConflict


class UploadHandler:

    @classmethod
    @Route.get(
        r"/upload",
        description="Manage upload of GNS3 images",
        api_version=None
    )
    def index(request, response):
        response.template("upload.html")

