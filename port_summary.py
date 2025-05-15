#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
#
# Author: Petr Belenko
# Data: 07 MAY 2018
# Rev: 22 FEB 2019
# Version: 2.0.10

from termcolor import colored
from datetime import datetime
from pathlib import Path


def __delete_file(file_name):
    created_file = Path(file_name)
    created_file.unlink()


def __port_summary(file_name):

    current_data_center = []
    previous_data_center = ['']
    et100_total = int(0)
    et100_used_summary = int(0)
    et_total = int(0)
    et_used_summary = int(0)
    xe_total = int(0)
    xe_used_summary = int(0)
    ge_total = int(0)
    ge_used_summary = int(0)
    xe_dc_sum = []
    ge_dc_sum = []
    et_dc_sum = []
    et100_dc_sum = []
    data = open(file_name, 'r')
    current_port_info = data.read()
    data.close()

    # Calculating port summary

    for line in sorted(current_port_info.splitlines()):

        if not line:
            pass
        else:
            current_data_center = line.split(',')

            print('\nProcessing line:')
            print(colored(current_data_center, 'cyan'))

            if previous_data_center == ['']:
                previous_data_center = current_data_center
                if current_data_center[1] == '100G':
                    et100_total += int(current_data_center[3])
                    et100_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '25G':
                    et_total += int(current_data_center[3])
                    et_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '10G':
                    xe_total += int(current_data_center[3])
                    xe_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '1G':
                    ge_total += int(current_data_center[3])
                    ge_used_summary += int(current_data_center[4])

                else:
                    pass

            elif previous_data_center[0] == current_data_center[0]:

                if current_data_center[1] == '100G':
                    et100_total += int(current_data_center[3])
                    et100_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '25G':
                    et_total += int(current_data_center[3])
                    et_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '10G':
                    xe_total += int(current_data_center[3])
                    xe_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '1G':
                    ge_total += int(current_data_center[3])
                    ge_used_summary += int(current_data_center[4])

                else:
                    pass

            elif previous_data_center[0] != current_data_center[0]:
                et100_dc_sum.append(previous_data_center[0] + ',' + '100G' + ',' + str(et100_total) + ',' +
                                    str(et100_used_summary))
                et_dc_sum.append(previous_data_center[0] + ',' + '25G' + ',' + str(et_total) + ',' + str(et_used_summary))
                xe_dc_sum.append(previous_data_center[0] + ',' + '10G' + ',' + str(xe_total) + ',' + str(xe_used_summary))
                ge_dc_sum.append(previous_data_center[0] + ',' + '1G' + ',' + str(ge_total) + ',' + str(ge_used_summary))
                et100_total = int(0)
                et100_used_summary = int(0)
                et_total = int(0)
                et_used_summary = int(0)
                xe_total = int(0)
                xe_used_summary = int(0)
                ge_total = int(0)
                ge_used_summary = int(0)
                previous_data_center = current_data_center

                if current_data_center[1] == '100G':
                    et100_total += int(current_data_center[3])
                    et100_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '25G':
                    et_total += int(current_data_center[3])
                    et_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '10G':
                    xe_total += int(current_data_center[3])
                    xe_used_summary += int(current_data_center[4])
                elif current_data_center[1] == '1G':
                    ge_total += int(current_data_center[3])
                    ge_used_summary += int(current_data_center[4])

                else:
                    pass
            else:
                pass
    et100_dc_sum.append(previous_data_center[0] + ',' + '100G' + ',' + str(et100_total) + ',' + str(et100_used_summary))
    et_dc_sum.append(previous_data_center[0] + ',' + '25G' + ',' + str(et_total) + ',' + str(et_used_summary))
    xe_dc_sum.append(current_data_center[0] + ',' + '10G' + ',' + str(xe_total) + ',' + str(xe_used_summary))
    ge_dc_sum.append(current_data_center[0] + ',' + '1G' + ',' + str(ge_total) + ',' + str(ge_used_summary))

    latest_report = et100_dc_sum + et_dc_sum + xe_dc_sum + ge_dc_sum

    # Calculate the difference with the previous week
    data = open('PortReports/ports_use_summary.csv', 'r')
    current_port_info = data.read()
    data.close()

    date = 'test'
    data_center = 'test'
    date_of_report_run = {date: [data_center]}

    # Create dictionary
    for line in current_port_info.splitlines():
        if '2019' in line or '2021' in line:
            date = line.split(' ')
            date = date[0]
        elif not line == '':
            if date_of_report_run == {'test': ['test']}:
                date_of_report_run.clear()
            else:
                date_of_report_run.setdefault(date, []).append(line)
        else:
            pass

    # Identify last reports
    previous_report_date = list(date_of_report_run.keys())[-1]
    # Calculate the difference with the previous week
    et100_current_sum = []
    et_current_sum = []
    xe_current_sum = []
    ge_current_sum = []
    for data_center_previous in sorted(date_of_report_run[previous_report_date]):
        data_center_previous = data_center_previous.split(',')
        for data_center_current in sorted(latest_report):
            data_center_current = data_center_current.split(',')
            if data_center_previous[0] == data_center_current[0]:
                if data_center_previous[1] == data_center_current[1]:
                    difference = int(data_center_current[3]) - int(data_center_previous[3])
                    data_center_current.append(str(difference))
                    finale_line = ','.join(data_center_current)
                    if data_center_current[1] == '100G':
                        et100_current_sum.append(finale_line)
                    elif data_center_current[1] == '25G':
                        et_current_sum.append(finale_line)
                    elif data_center_current[1] == '10G':
                        xe_current_sum.append(finale_line)
                    elif data_center_current[1] == '1G':
                        ge_current_sum.append(finale_line)
                    else:
                        pass
                else:
                    pass
            else:
                finale_line = ','.join(data_center_current)
                if data_center_current[1] == '100G':
                    et100_current_sum.append(finale_line)
                elif data_center_current[1] == '25G':
                    et_current_sum.append(finale_line)
                elif data_center_current[1] == '10G':
                    xe_current_sum.append(finale_line)
                elif data_center_current[1] == '1G':
                    ge_current_sum.append(finale_line)

    # Write to the file
    with open('PortReports/ports_use_summary.csv', 'a+') as outfile:
        outfile.write('\n' + str(datetime.now()) + '\n')
        for et100_item in et100_current_sum:
            outfile.write(et100_item + '\n')
        for et_item in et_current_sum:
            outfile.write(et_item + '\n')
        for xe_item in xe_current_sum:
            outfile.write(xe_item + '\n')
        for ge_item in ge_current_sum:
            outfile.write(ge_item + '\n')
    return


def __add_difference():
    data = open('PortReports/ports_use_summary.csv', 'r')
    port_summary = data.read()
    data.close()

    dictionary = {}
    date = ''

    # with open('PortReports/ports_use_summary.csv', 'w') as outfile:
    for line in sorted(port_summary.splitlines()):
        if not line:
            continue
        else:
            if '-' in line:
                date = line.split(' ')
                date = date[0]
            else:
                dictionary.setdefault(date, []).append(str(line))
    print(dictionary)


def __main():
    file_name = 'PortReports/' + str(datetime.now().date()) + '.csv'
    print (colored('Initiating calculation process', 'magenta'))
    __port_summary(file_name)
    # __delete_file(file_name)
    print ('Done!')


if __name__ == '__main__':

    __main()
