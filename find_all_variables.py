#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
#
# Author: Petr Belenko
# Data: 07 MAY 2018
# Rev: 03 NOV 2020
# Version: 2.1

import re
from pathlib import Path


def __searchfile(path, search_pattern, additional_files):
    for word in additional_files:
        file_path = path / word
        files.append(str(file_path))
    for word in path.glob(search_pattern):
        files.append(str(word))
    return files


if __name__ == '__main__':
    files = []

    # Files location
    cfg_bits_folder = Path('../ConfigurationBits/Juniper/')
    cfg_bits_fw_folder = Path('../ConfigurationBits/Juniper/Firewall')
    base_bits_pattern = "*.nconf"
    base_fw_bits_pattern = "*.nconf"
    additional_bits = ''
    additional_bits_fw = ''

    files_list = __searchfile(cfg_bits_folder, base_bits_pattern, additional_bits)
    files_list += __searchfile(cfg_bits_fw_folder, base_fw_bits_pattern, additional_bits_fw)

    config_values = []
    specific_values = []
    pattern = re.compile('#!.*!#')
    pattern2 = re.compile('!!.*!!')
    pattern3 = re.compile('#\w*!')
    pattern4 = re.compile('# .*')

    for file_name in files_list:
        with open(file_name, 'r') as file:
            for line in file:
                found_word = pattern.findall(line)
                found_word2 = pattern2.findall(line)
                found_word3 = pattern3.findall(line)
                if found_word:
                    if found_word2:
                        config_values += found_word
                        config_values += found_word2
                    else:
                        config_values += found_word
                elif found_word3:
                    specific_values += found_word3
                else:
                    continue

    # Remove duplicate values
    config_values = sorted(list(set(config_values)))

    # Remove duplicate values
    specific_values = sorted(list(set(specific_values)))

    variable = ''
    description = ''
    with open('supporting_files/file_manipulations.py', 'r') as py_file:
        file_manipulations = py_file.readlines()
        py_file.close()

    with open('variables.txt', 'w+') as outfile:
        outfile.write('Config values:\n\n')
        for line in config_values:
            outfile.write(str(line) + '\n')
        outfile.write('\nSpecific values:\n\n')
        for line in file_manipulations:
            if any(word in line for word in specific_values):
                variable = ' '.join(pattern3.findall(line))
                definition = ' '.join(pattern4.findall(line))
                definition = definition.replace('#', '  Description:')
                outfile.write(str(variable) + '\n' + str(definition) + '\n')
        outfile.close()
