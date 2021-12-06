#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.


import os
import re
import sys
import subprocess

from setuptools import setup, Command
from setuptools.command.test import test as TestCommand

__version__ = ''
with open('linebot/__about__.py', 'r') as fd:
    reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
    for line in fd:
        m = reg.match(line)
        if m:
            __version__ = m.group(1)
            break


def _requirements():
    with open('requirements.txt', 'r') as fd:
        return [name.strip() for name in fd.readlines()]


def _requirements_test():
    with open('requirements-test.txt', 'r') as fd:
        return [name.strip() for name in fd.readlines()]


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


class CodegenCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        basedir = os.path.abspath(os.path.dirname(__file__))

        header = (
            "# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            "#\n"
            "#  *** DO NOT EDIT THIS FILE ***\n"
            "#\n"
            "#  1) Modify linebot/api.py\n"
            "#  2) Run `python setup.py codegen`\n"
            "#\n"
            "# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            "\n"
        )

        with open(f"{basedir}/linebot/api.py", "r") as original:
            source = original.read()
            import re

            async_source = header + source
            async_source = re.sub("    def (?!__init__)", "    async def ", async_source)
            async_source = re.sub("from .http_client import HttpClient, RequestsHttpClient", "", async_source)

            # Change the signature of the __init__.
            # self, channel_access_token
            async_source = re.sub(r"def __init__\(self, channel_access_token,",
                                  "def __init__(self, channel_access_token, async_http_client,",
                                  async_source)
            async_source = re.sub(r",\s*timeout=HttpClient.DEFAULT_TIMEOUT, http_client=RequestsHttpClient",
                                  "", async_source)
            async_source = re.sub(
                r"if http_client:\n"
                + r"\s*self.http_client = http_client\(timeout=timeout\)\n"
                + r"\s*else:\n"
                + r"\s*self.http_client = RequestsHttpClient\(timeout=timeout\)",
                "self.async_http_client = async_http_client", async_source)
            async_source = re.sub(
                r"\"\"\"__init__ method.*?\"\"\"\n",
                '"""__init__ method.' + "\n\n"
                + "    :param str channel_access_token: Your channel access token\n"
                + "    :param str endpoint: (optional) Default is https://api.line.me\n"
                + "    :param str data_endpoint: (optional) Default is https://api-data.line.me\n"
                + "\n\"\"\"\n"
                , async_source, flags=re.DOTALL)
            async_source = re.sub("'line-bot-sdk-python/'", '"line-bot-sdk-python-async/"', async_source)

            async_source = re.sub('"""linebot.api module."""', '"""linebot.async_api module."""', async_source)
            async_source = re.sub(
                "self.(_get|_post|_delete|_put)", "await self.\\1", async_source
            )
            async_source = re.sub(
                "self.http_client.(get|post|delete|put)", "await self.async_http_client.\\1", async_source
            )
            async_source = re.sub(
                "response.json", "await response.json", async_source
            )
            async_source = re.sub(
                "from .http_client import HttpClient, RequestsHttpClient",
                "from .async_http_client import AsyncHttpClient, AiohttpAsyncHttpClient", async_source
            )
            async_source = re.sub(
                "linebot.http_client.RequestsHttpClient", "linebot.async_http_client.AiohttpAsyncHttpClient",
                async_source
            )
            async_source = re.sub(
                "HttpClient.DEFAULT_TIMEOUT", "AsyncHttpClient.DEFAULT_TIMEOUT", async_source
            )
            async_source = re.sub(
                "RequestsHttpClient", "AiohttpAsyncHttpClient", async_source
            )
            async_source = re.sub(
                "Default is self.http_client.timeout", "Default is self.async_http_client.timeout", async_source
            )
            async_source = re.sub(
                "self.__check_error(response)", "await self.__check_error(response)", async_source
            )
            async_source = re.sub(
                "class LineBotApi",
                "class AsyncLineBotApi", async_source
            )
            async_source = re.sub("stream=(stream|False|True), ", "", async_source)

            with open(f"{basedir}/linebot/async_api.py", "w") as output:
                output.write(async_source)

            subprocess.check_call(
                [sys.executable, "-m", "black", f"{basedir}/linebot/async_api.py"],
            )


with open('README.rst', 'r') as fd:
    long_description = fd.read()

setup(
    name="line-bot-sdk",
    version=__version__,
    author="RyosukeHasebe",
    author_email="hsb.1014@gmail.com",
    maintainer="RyosukeHasebe",
    maintainer_email="hsb.1014@gmail.com",
    url="https://github.com/line/line-bot-sdk-python",
    description="LINE Messaging API SDK for Python",
    long_description=long_description,
    license='Apache License 2.0',
    packages=[
        "linebot", "linebot.models"
    ],
    python_requires=">=3.6.0",
    install_requires=_requirements(),
    tests_require=_requirements_test(),
    cmdclass={
        'test': PyTest,
        'codegen': CodegenCommand
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development"
    ]
)
