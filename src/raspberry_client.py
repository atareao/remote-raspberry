#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
# This file is part of remote-raspberry
#
# Copyright (c) 2020 Lorenzo Carbonell Cerezo <a.k.a. atareao>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE

import paramiko
from comun import _

class RaspberryClient():
    def __init__(self, hostname, port, username, password=None, keyfile=None):
        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password
        self._keyfile = keyfile
        self._connected = False
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        if not self._hostname:
            raise Exception(_('Hostname must be set'))
            return
        if not self._port:
            raise Exception(_('Port must be set'))
            return
        if not self._username:
            raise Exception(_('Username must be set'))
            return
        if not self._keyfile and not self._password:
            raise Exception(_('Password or keyfile must be set'))
            return
        try:
            if self._keyfile:
                self._client.connect(self._hostname, self._port,
                                     username=self._username,
                                     key_filename=self._keyfile)
            elif self._password:
                self._client.connect(self._hostname, self._port,
                                     username=self._username,
                                     password=self._password)
            self._connected = True
        except paramiko.ssh_exception.AuthenticationException:
            raise Exception(_('Authentication failed'))
        except paramiko.ssh_exception.BadAuthenticationType:
            raise Exception(_('Bad authentication type'))
        except paramiko.ssh_exception.BadHostKeyException:
            raise Exception(_('Bad host key'))
        except:
            raise Exception(_('Unknown exception'))

    def is_connected(self):
        return self._connected

    def disconnect(self):
        self._client.close()

    def read_file(self, remote_filename):
        string_builder = ''
        try:
            sftp_client = self._client.open_sftp()
            remote_file = sftp_client.open(remote_filename)
            for line in remote_file:
                string_builder += line + '\n'
            if string_builder.endswith('\n'):
                string_builder = string_builder[:-1]
        except Exception as exception:
            print(exception)
        finally:
            remote_file.close()
        return string_builder

    def exec_command(self, command):
        string_builder = ''
        try:
            (stdin, stdout, stderr) = self._client.exec_command(command)
            for line in stdout.readlines():
                string_builder += line + '\n'
            if string_builder.endswith('\n'):
                string_builder = string_builder[:-1]
        except Exception as exception:
            print(exception)
        return string_builder

    def __del__(self):
        self.disconnect()


if __name__ == '__main__':
    raspberryClient = RaspberryClient('raspberrypi.local', 22, 'test',
                                      'contraseña')
    raspberryClient.connect()
    print(raspberryClient.is_connected())
    del raspberryClient
    raspberryClient = RaspberryClient('raspberrypi.local', 22, 'test',
                                      keyfile='/home/lorenzo/.ssh/id_rsa.pub')
    raspberryClient.connect()
    print(raspberryClient.is_connected())
