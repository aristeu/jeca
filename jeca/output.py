# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import sys

def formatted_output(lines):
    if sys.stdout.isatty():
        max_width = {}
        for line in lines:
            counter = 0
            for column in line:
                size = len(column)
                if counter in max_width:
                        if size > max_width[counter]:
                            max_width[counter] = size
                else:
                    max_width[counter] = size
                counter = counter + 1
        for line in lines:
            counter = 0
            for column in line:
                f = "{:<%i} " % max_width[counter]
                sys.stdout.write(f.format(column))
                counter = counter + 1
                sys.stdout.write(" ")
            sys.stdout.write("\n")
    else:
        for line in lines:
            new_line = True
            for column in line:
                if new_line == True:
                    new_line = False
                else:
                    sys.stdout.write("\t")
                sys.stdout.write(column)
            sys.stdout.write("\n")
