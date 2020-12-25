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

import cv2
import numpy as np
from blur_detection import dwt
from blur_detection import estimate_blur

phi = 0.5 * (1 + 5 ** 0.5)  # Golden ratio


def get_focus_score(focus_frame):
    """Returns a score that provide information about
    how focused is the provided camera frame

    Args:
        focus_frame ([numpy.ndarray]): camera frame

    Returns:
        [int]: how focused is the provided camera frame
    """
    if focus_frame.ndim == 3:
        focus_frame = cv2.cvtColor(focus_frame, cv2.COLOR_BGR2GRAY)

    score = dwt.low_res_score(focus_frame)
    return score


def gaussian_fitting(z, f):
    """Fit the autofocus function data according to the equation 16.5 in the
    textbook : 'Microscope Image Processing' by Q.Wu et al'
    z_max = gaussian_fitting((z1, z2, z3), (f1, f2 f3))
    where z1, z2 , z3 are points where the autofocus functions
    values f1, f2, f3 are measured
    """
    z1 = z[0]
    z2 = z[1]
    z3 = z[2]
    f1 = f[0]
    f2 = f[1]
    f3 = f[2]

    B = (np.log(f2) - np.log(f1)) / (np.log(f3) - np.log(f2))

    if (z3 - z2) == (z2 - z1):
        return 0.5 * (B * (z3 + z2) - (z2 + z1)) / (B - 1)
    else:
        return (
            0.5
            * (B * (z3 ** 2 - z2 ** 2) - (z2 ** 2 - z1 ** 2))
            / (B * (z3 - z2) - (z2 - z1))
        )


def parabola_fitting(z, f):
    """Fit the autofocus function data according to the equation 16.5 in the
    textbook : 'Microscope Image Processing' by Q.Wu et al'
    parabola_fitting((z1, z2, z3), (f1, f2 f3))
    where z1, z2 , z3 are points where the autofocus functions
    values f1, f2, f3 are measured
    """
    z1 = z[0]
    z2 = z[1]
    z3 = z[2]
    f1 = f[0]
    f2 = f[1]
    f3 = f[2]

    E = (f2 - f1) / (f3 - f2)

    if (z3 - z2) == (z2 - z1):
        return 0.5 * (E * (z3 + z2) - (z2 + z1)) / (E - 1)
    else:
        return (
            0.5
            * (E * (z3 ** 2 - z2 ** 2) - (z2 ** 2 - z1 ** 2))
            / (E * (z3 - z2) - (z2 - z1))
        )


def fibs(n=None):
    """A generator, (thanks to W.J.Earley) that returns the fibonacci series """
    a, b = 0, 1
    yield 0
    yield 1
    if n is not None:
        for _ in range(1, n):
            b = b + a
            a = b - a
            yield (b)
    else:
        while True:
            b = b + a
            a = b - a
            yield (b)


def smallfib(m):
    """Return N such that fib(N) >= m """
    n = 0
    for fib in fibs(m):
        if fib >= m:
            return n
        n = n + 1


def fib(n):
    """Evaluate the n'th fibonacci number """
    return (phi ** n - (-phi) ** (-n)) / (5 ** 0.5)
