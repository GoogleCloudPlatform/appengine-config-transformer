# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import setuptools
import os

# Compute the package tree of yaml_conversion since distutils doesn't do it
# for us.
packages = []
base = os.path.dirname(__file__) or '.'
for root, dirs, files in os.walk(os.path.join(base, 'yaml_conversion')):
    if '__init__.py' in files:
        packages.append('.'.join(root[len(base) + 1:].split(os.path.sep)))

setuptools.setup(
    name="appengine-config-transformer",
    version="0.1",
    description="Tool for converting between YAML and JSON representations.",
    packages=packages,
    py_modules=['convert_yaml'],
    entry_points={'console_scripts': ['convert_yaml=convert_yaml:main']},
)
