"""
Copyright (C) 2020 Mauro Riva

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests


def set_move_motor(m5stack_host, mtype, step, mdir):
    try:
        url = f"http://{m5stack_host}/move/{mtype}/{step}/{mdir}"
        r = requests.get(url)
        done = True if r.json()["status"] == "true" else False
        position = r.json()["position"]
    except:
        done = False
        position = 0

    return done, position


def get_motor_status(m5stack_host, mtype):
    url = f"http://{m5stack_host}/status/{mtype}"
    status = requests.get(url).json()
    return status
