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

"""
Docker server module.
"""

import asyncio
import logging
import aiohttp
import urllib
import json

log = logging.getLogger(__name__)

from ..base_manager import BaseManager
from ..project_manager import ProjectManager
from .docker_vm import DockerVM
from .docker_error import DockerError


class Docker(BaseManager):

    _VM_CLASS = DockerVM

    def __init__(self):
        super().__init__()
        self._server_url = '/var/run/docker.sock'
        self._connected = False
        # Allow locking during ubridge operations
        self.ubridge_lock = asyncio.Lock()

    @asyncio.coroutine
    def connector(self):
        if not self._connected:
            try:
                self._connector = aiohttp.connector.UnixConnector(self._server_url)
                self._connected = True
                yield from self.query("GET", "info")
            except (aiohttp.errors.ClientOSError, FileNotFoundError):
                self._connected = False
                raise DockerError("Can't connect to docker daemon")
        return self._connector

    def __del__(self):
        if self._connected:
            self._connector.close()

    @asyncio.coroutine
    def query(self, method, path, data={}, params={}):
        """
        Make a query to the docker daemon and decode the request

        :param method: HTTP method
        :param path: Endpoint in API
        :param data: Dictionnary with the body. Will be transformed to a JSON
        :param params: Parameters added as a query arg
        """
        response = yield from self.http_query(method, path, data=data, params=params)
        body = yield from response.read()
        if len(body):
            body = json.loads(body.decode("utf-8"))
        log.debug("Query Docker %s %s params=%s data=%s Response: %s", method, path, params, data, body)
        return body

    @asyncio.coroutine
    def http_query(self, method, path, data={}, params={}):
        """
        Make a query to the docker daemon

        :param method: HTTP method
        :param path: Endpoint in API
        :param data: Dictionnary with the body. Will be transformed to a JSON
        :param params: Parameters added as a query arg
        :returns: HTTP response
        """
        data = json.dumps(data)
        url = "http://docker/" + path
        response = yield from aiohttp.request(
            method,
            url,
            connector=(yield from self.connector()),
            params=params,
            data=data,
            headers={"content-type": "application/json", },
        )
        if response.status >= 300:
            body = yield from response.read()
            try:
                body = json.loads(body.decode("utf-8"))["message"]
            except ValueError:
                pass
            log.debug("Query Docker %s %s params=%s data=%s Response: %s", method, path, params, data, body)
            raise DockerError("Docker has returned an error: {}".format(body))
        return response

    @asyncio.coroutine
    def websocket_query(self, path, params={}):
        """
        Open a websocket connection

        :param path: Endpoint in API
        :param params: Parameters added as a query arg
        :returns: Websocket
        """

        url = "http://docker/" + path
        connection = yield from aiohttp.ws_connect(url,
                                                   connector=(yield from self.connector()),
                                                   origin="http://docker",
                                                   autoping=True)
        return connection

    @asyncio.coroutine
    def list_images(self):
        """Gets Docker image list.

        :returns: list of dicts
        :rtype: list
        """
        images = []
        for image in (yield from self.query("GET", "images/json", params={"all": 0})):
            for tag in image['RepoTags']:
                if tag != "<none>:<none>":
                    images.append({'image': tag})
        return sorted(images, key=lambda i: i['image'])
