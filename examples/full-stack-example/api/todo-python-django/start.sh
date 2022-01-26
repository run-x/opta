#!/bin/bash
# Copyright 2020 BigBitBus
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

python manage.py migrate
python manage.py collectstatic
# This is not recommended for production; look at uwsgi in front of the Django server
# One good approach is documented here: https://uwsgi.readthedocs.io/en/latest/tutorials/Django_and_nginx.html
python manage.py runserver 0.0.0.0:8000
