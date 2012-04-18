#!/usr/bin/env python
#
# Copyright (C) 2010-2012 Red Hat, Inc.
#
# libvirt-test-API is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranties of
# TITLE, NON-INFRINGEMENT, MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# This module help form new lists from original list generated by module parser,
# the purpose is to get useful information about a testrun.

class Mapper(object):

    def __init__(self, testcases_list):
        self.testcases_list = testcases_list

    def module_casename_func_map(self):
        """ generate a new list of dictionary
            change key from module:casename to module:casename:func
            if clean flag is set, key will be module:casename:func:clean
        """
        new_case_list = []

        for testcase in self.testcases_list:
            case = {}
            mod_case = testcase.keys()[0]
            if ":" in mod_case:
                casename = mod_case.split(":")[1]
                func = casename

            if mod_case == 'sleep':
                new_case_list.append(testcase)
                continue

            if mod_case == 'clean':
                if not new_case_list:
                    return None

                previous_case = new_case_list.pop()
                key = previous_case.keys()[0] + ':clean'
                case[key] = previous_case.values()[0]
                new_case_list.append(case)
                continue

            cases_params = testcase.values()[0]
            case[mod_case + ":" + func] = cases_params
            new_case_list.append(case)

        return new_case_list

    def module_casename_func_noflag(self):
        """remove sleep and clean data
           generate a new data format
        """
        new_case_list = []
        for testcase in self.testcases_list:
            case = {}
            mod_case = testcase.keys()[0]

            if mod_case == 'sleep' or mod_case == 'clean':
                continue

            func = mod_case.split(":")[1]

            cases_params = testcase.values()[0]
            case[mod_case + ":" + func] = cases_params
            new_case_list.append(case)

        return new_case_list