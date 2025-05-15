#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
# Author: Peter Belenko
# Data: 07 AUG 2019
# Rev: 08 JUL 2021
# Version: 1.0.10
import sys
import re
import getpass
from termcolor import colored
from datetime import datetime
from free_ports_count import __show_command
from supporting_files.menus import __interfaces, __dc_sel, __interface_type, __port_sel
from supporting_files.file_manipulations import __lf


def __ipmi_and_pxe_write(port_name, port_sel, free_port, description, device_number, port_type, vlan_sel,
                         deployment_type):
    port_name.write(
        'delete interfaces ' + str(port_sel) + str(free_port) + '\n')
    port_name.write(
        'set interfaces ' + str(port_sel) + str(free_port) + ' description ' + description + str(
            device_number) + port_type + '\n')
    if '-ipmi' in port_type:
        port_name.write(
            'set interfaces ' + str(port_sel) + str(free_port) +
            ' unit 0 family ethernet-switching interface-mode access\n')
        port_name.write(
            'set interfaces ' + str(port_sel) + str(free_port) +
            ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
        port_name.write(
            'set interfaces ' + str(port_sel) + str(free_port) +
            ' unit 0 family ethernet-switching storm-control default\n')
    else:
        if 'ACI' in deployment_type:
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' native-vlan-id 22' + '\n')
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' unit 0 family ethernet-switching interface-mode trunk\n')
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' unit 0 family ethernet-switching vlan members vlan21' + '\n')
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' unit 0 family ethernet-switching vlan members vlan22' + '\n')
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' unit 0 family ethernet-switching storm-control default\n')
        else:
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' unit 0 family ethernet-switching interface-mode access\n')
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
            port_name.write(
                'set interfaces ' + str(port_sel) + str(free_port) +
                ' unit 0 family ethernet-switching storm-control default\n')


def __smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel, name_sub_port_pairs):
    if port_sel == 'ge-0/0/':
        line = str(sw_name) + 'a port ' + str(number) + ' -> ' + description + str(
            device_number) + port_type + '\n'
        return line
    elif port_sel == 'ge-1/0/':
        line = str(sw_name) + 'b port ' + str(number) + ' -> ' + description + str(
            device_number) + port_type + '\n'
        return line
    elif port_sel == 'xe-/0/':
        line = str(sw_name) + 'a,b port ' + str(number) + ' -> ' + description + str(
           device_number) + '\n'
        return line
    elif port_sel == 'et-0/0/':
        line = '\nFor 4 ports cassettes\n'
        for key in name_sub_port_pairs:
            device_name = key
            sub_port_number = int(name_sub_port_pairs[key])
            if sub_port_number == 0:
                port_location_eight_ports = 'First port on the 4 ports cassette.'
            elif sub_port_number == 1:
                port_location_eight_ports = 'Second port from the left on the 4 ports cassette.'
            elif sub_port_number == 2:
                port_location_eight_ports = 'Third port from the left on the 4 ports cassette.'
            elif sub_port_number == 3:
                port_location_eight_ports = 'Forth port from the left on the 4 ports cassette.'
            else:
                print(colored('Error in def __smarthands. Out of scope. Please fix', 'red'))
                sys.exit()

            line += device_name + ' -> ' + port_location_eight_ports + '\n'

        line += '\nFor 12 ports cassettes.\nPlease be careful, 12 ports cassettes have 3 groups (4 ports each), ' \
                'with Group 1 being the first starting from the left.\n'
        for key in name_sub_port_pairs:
            device_name = key
            sub_port_number = int(name_sub_port_pairs[key])
            if sub_port_number == 0:
                port_location_twelve_ports = 'BOTTOM left port OF THE GROUP on the 12 ports cassette.'
            elif sub_port_number == 1:
                port_location_twelve_ports = 'TOP left port IN THE SAME GROUP on the 12 ports cassette.'
            elif sub_port_number == 2:
                port_location_twelve_ports = 'TOP right port IN THE SAME GROUP on the 12 ports cassette.'
            elif sub_port_number == 3:
                port_location_twelve_ports = 'BOTTOM right port IN THE SAME GROUP on the 12 ports cassette.'
            else:
                print(colored('Error in def __smarthands. Out of scope. Please fix', 'red'))
                sys.exit()

            line += device_name + ' -> ' + port_location_twelve_ports + '\n'
        return line
    else:
        print(colored(str(port_sel) + ' not yet supported', 'red'))
        sys.exit()


def __main():
    try:
        auto_mode = input('Apply in auto mode(y/n):')
        if auto_mode == 'Y' or auto_mode == 'y':
            auto = True
        elif auto_mode == 'N' or auto_mode == 'n':
            auto = False
        else:
            print(colored('Unsupported selection please start over', 'red'))
            sys.exit()
        if auto:
            dc_ip_list = __lf('dc_ip_list.yml')
            selected_dc = __dc_sel()
            dc_name = selected_dc.lower()
            # interface_ans = __interface_type()
            selected_series = 'SWITCH'
            interface_ans = __interface_type()
            if 'IPMI + PXE' in interface_ans or 'IPMI' in interface_ans:
                selected_ports = '1G'
            else:
                selected_ports = '10G'
            number_of_servers = int(input('Provide number of servers that are going to be setup:'))
            # check if it's a valid number
            if number_of_servers == number_of_servers / 1:
                pass
            else:
                print(colored('Not supported number_of_servers. Please start again', 'red'))
                sys.exit()
            user = input('\nUsername:')
            password = getpass.getpass('Password:')
            port = 22
            file_name = 'PortReports/' + str(datetime.now().date()) + '.csv'
            device_name, ip, free_ports = __show_command(dc_ip_list, user, password, port, selected_dc,
                                                         selected_series, selected_ports, file_name, auto)
            sw_name = device_name
            # Number of ports needed
            if 'IPMI + PXE' in interface_ans:
                number_of_ports = number_of_servers * 2
            else:
                number_of_ports = number_of_servers

            # Check if number of devices is more than physical capability of the switch
            if free_ports:
                if int(number_of_ports) > len(free_ports):
                    print(colored('Not enough free ports. Currently we have ' + str(len(free_ports)) +
                                  ' Please try again or use manual mode', 'red'))
                    sys.exit()
                else:
                    pass
            else:
                print('You are here')
                sys.exit()

        else:
            dc_name = input('Data Center name(ZRH1,PHX1...):').lower()
            interface_ans = __interface_type()

            # port numbers
            start_port = input('Provide first switch port number after ge-0/0/? or xe-0/0/? or et-0/0/?:')
            number_of_servers = int(input('Provide number of servers that are going to be setup:'))

            # check if it's a valid number
            if number_of_servers == number_of_servers / 1:
                if 'IPMI + PXE' in interface_ans:
                    if number_of_servers > 23:
                        print(colored('Currently such setup is not supported, please use smaller blocks', 'red'))
                        number_of_servers = int(input('Number of devices:'))
                    else:
                        pass
                else:
                    if number_of_servers > 46:
                        print(colored('Currently such setup is not supported, please use smaller blocks', 'red'))
                        number_of_servers = int(input('Number of devices:'))
                    else:
                        pass
            else:
                print(colored('Not supported number_of_servers. Please start again', 'red'))
                sys.exit()

            sw_name = input('Provide a switch number (for example 04 or 4)')
            if len(sw_name) > 1:
                search_pattern = '([0-9]{2})'
                compiled = re.compile(search_pattern)
                sw_number = compiled.findall(sw_name)[0]
            elif len(sw_name) == 1:
                search_pattern = '([0-9])'
                compiled = re.compile(search_pattern)
                sw_number = compiled.findall(sw_name)[0]
            else:
                print(colored('Not supported', 'red'))
                sys.exit()
            if '0' in str(sw_number):
                pass
            else:
                sw_number = '0' + str(sw_number)

            sw_name = str(dc_name) + '-sw-' + str(sw_number)
            # Add ports for IPMI and PXE, change logic for QFX5120
            if 'IPMI + PXE' in interface_ans:
                start_port = int(start_port)
                end_port = start_port + number_of_servers * 2
            elif 'QFX5120' in interface_ans:
                end_port = 0
            else:
                start_port = int(start_port)
                end_port = start_port + number_of_servers
        description_input = input('input first device name (for example fra2-infra-vz-ph01):')

        device_number = ''
        # find the device name and a number
        # storage
        # for example *-acs1-stor
        search_pattern = '(.*-\w{3}\d-\w{4})\d{2}$'
        compiled = re.compile(search_pattern)
        description_base = compiled.findall(description_input)
        if not description_base:
            pass
        else:
            # *-acs02
            search_pattern = '.*-\w{4}(\d{2})$'
            compiled = re.compile(search_pattern)
            device_number = int(compiled.findall(description_input)[0])

        # new storage *-acs01-01
        if not description_base or not device_number:
            search_pattern = '(.*-\w{3}-)\d{2}$'
            compiled = re.compile(search_pattern)
            description_base = compiled.findall(description_input)
            if not description_base:
                pass
            else:
                # find the server number in initial data
                # *-acs01-01
                search_pattern = '.*-(\d{2})$'
                compiled = re.compile(search_pattern)
                device_number = int(compiled.findall(description_input)[0])
        else:
            pass

        # Compute nodes
        if not description_base or not device_number:
            # separating server description from number
            # any, but not storage with a number at the end
            search_pattern = '(.*-)\d{2}'
            compiled = re.compile(search_pattern)
            description_base = compiled.findall(description_input)
            if not description_base:
                pass
            else:
                # find the server number in initial data
                search_pattern = '.*-(\d{2})$'
                compiled = re.compile(search_pattern)
                device_number = int(compiled.findall(description_input)[0])
        else:
            pass

        # add an additional 0
        print(description_base)
        print(device_number)
        if device_number < 10:
            description = description_base[0] + '0'
        else:
            description = description_base[0]

        # check if we have enough ports on one device
        if not auto:
            if end_port > 48:
                print(colored('Currently ' + str(end_port) + ' ports setup is not supported, please use smaller blocks',
                              'red'))
                sys.exit()
            else:
                pass

        marker = 0
        smarthands = []

        # port_sel is not needed in auto mode
        if auto:
            port_sel = ''
        else:
            pass

        # opening file to write
        port_name = open('port_config_' + str(sw_name) + '.set', 'w')
        sub_port_number = ''

        if 'IPMI + PXE' in interface_ans:
            # All IPMI + PXE

            if 'ACI' in interface_ans:
                deployment_type = 'ACI'
            else:
                deployment_type = 'None'

            if auto:
                for free_port in free_ports:
                    # Determine whether to add a leading 0 for device number in description
                    if device_number < 10:
                        description = description_base[0] + '0'
                    else:
                        description = description_base[0]
                    if free_port == free_ports[0]:
                        vlan_sel = '210'
                        port_type = '-ipmi'

                        __ipmi_and_pxe_write(port_name, port_sel, free_port, description, device_number, port_type,
                                             vlan_sel, deployment_type)

                        smarthands.append(
                            __smarthands(dc_name, sw_name, free_port, description, device_number, port_type,
                                         port_sel, sub_port_number))
                        marker = 1

                    else:
                        if marker == 1:
                            if 'Storage' in interface_ans:
                                vlan_sel = '220'
                            elif 'DR2' in interface_ans:
                                vlan_sel = '240'
                            else:
                                vlan_sel = '230'
                            port_type = '-pxe'

                            __ipmi_and_pxe_write(port_name, port_sel, free_port, description, device_number, port_type,
                                                 vlan_sel, deployment_type)

                            smarthands.append(
                                __smarthands(dc_name, sw_name, free_port, description, device_number, port_type,
                                             port_sel, sub_port_number))
                            device_number = device_number + 1
                            marker = 0

                        else:
                            vlan_sel = '210'
                            port_type = '-ipmi'
                            __ipmi_and_pxe_write(port_name, port_sel, free_port, description, device_number, port_type,
                                                 vlan_sel, deployment_type)

                            smarthands.append(
                                __smarthands(dc_name, sw_name, free_port, description, device_number, port_type,
                                             port_sel, sub_port_number))
                            marker = 1

            else:
                port_sel = __interfaces()
                if start_port == start_port/1 and end_port == end_port/1:
                    for number in range(start_port, end_port):
                        # Determine whether to add a leading 0 for device number in description
                        if device_number < 10:
                            description = description_base[0] + '0'
                        else:
                            description = description_base[0]
                        if number == start_port:
                            vlan_sel = '210'
                            port_type = '-ipmi'
                            __ipmi_and_pxe_write(port_name, port_sel, number, description, device_number, port_type,
                                                 vlan_sel, deployment_type)

                            smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number,
                                                           port_type, port_sel, sub_port_number))
                            marker = 1

                        else:
                            if marker == 1:
                                if 'Storage' in interface_ans:
                                    vlan_sel = '220'
                                elif 'DR2' in interface_ans:
                                    vlan_sel = '240'
                                else:
                                    vlan_sel = '230'
                                port_type = '-pxe'
                                __ipmi_and_pxe_write(port_name, port_sel, number, description, device_number, port_type,
                                                     vlan_sel, deployment_type)

                                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number,
                                                               port_type, port_sel, sub_port_number))
                                device_number = device_number + 1
                                marker = 0

                            else:
                                vlan_sel = '210'
                                port_type = '-ipmi'
                                __ipmi_and_pxe_write(port_name, port_sel, number, description, device_number, port_type,
                                                     vlan_sel, deployment_type)

                                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number,
                                                               port_type, port_sel, sub_port_number))
                                marker = 1
                else:
                    print('Numbers expected, got ', start_port, ' ', end_port, ' instead')
        elif interface_ans == 'IPMI':
            # IPMI
            deployment_type = None
            port_sel = __interfaces()
            sub_port_number = ''
            vlan_sel = '210'
            port_type = '-ipmi'
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                __ipmi_and_pxe_write(port_name, port_sel, number, description, device_number, port_type, vlan_sel,
                                     deployment_type)
                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1

        elif interface_ans == 'Storage':
            # Storage storage node 10G interfaces
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            if dc_name == 'eu3':
                vlan_sel2 = '130'
            else:
                vlan_sel2 = '100'
            vlan_sel = '200'
            vlan_sel3 = '280'
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1
        elif interface_ans == 'ABC_VZ':
            # ABC VZ node 10G interfaces
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            vlan_sel = '110'
            vlan_sel2 = '190'
            vlan_sel3 = '250'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel

            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')

                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        elif interface_ans == 'DR2_ESX':
            # DR2 ESX 10G interfaces
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            vlan_sel = '180'
            vlan_sel2 = '970'
            vlan_sel3 = '1150'
            vlan_sel4 = '1160'
            vlan_sel5 = '1170'
            vlan_sel6 = 'dr20'

            for number in range(start_port, end_port):
                # first switch
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str( device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' mtu 9216\n')
                port_name.write('set interfaces xe-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces xe-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel5) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members ' + str(vlan_sel6) + '\n')
                # second switch
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' mtu 9216\n')
                port_name.write('set interfaces xe-1/0/' + str(number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces xe-1/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel5) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members ' + str(vlan_sel6) + '\n')

                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
            # make sure that vlan range is in place
            port_name.write('set vlans dr20 description dr2_customer_vlans\n')
            port_name.write('set vlans dr20 vlan-id-list 2000-2200')

        elif interface_ans == 'Enterprise_DR2_10G':
            # DR2 Storage 10G interfaces
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel

            vlan_sel = '970'
            vlan_sel3 = '1150'
            vlan_sel4 = '1170'
            vlan_sel5 = '2070'
            vlan_sel6 = '2170'
            vlan_sel7 = '2270'
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel5) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel6) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel7) + '\n')
                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        elif interface_ans == 'ACI_NODE':
            # DR2 Storage 10G interfaces
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel

            vlan_sel = '100'
            vlan_sel3 = '140'
            vlan_sel4 = '190'
            vlan_sel5 = '200'
            vlan_sel6 = '280'
            vlan_sel7 = '330'
            vlan_sel8 = '340'
            vlan_sel9 = '660'
            vlan_sel10 = '1150'
            vlan_sel11 = '2060'
            vlan_sel12 = '2160'
            vlan_sel13 = '2260'
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel5) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel6) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel7) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel8) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel9) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel10) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel11) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel12) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel13) + '\n')
                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        elif interface_ans == 'DR2_Storage':
            # DR2 Storage 10G interfaces
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel

            vlan_sel = '180'
            vlan_sel3 = '1150'
            vlan_sel4 = '1160'
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        elif interface_ans == 'ABC_VZ_FORCE_UP':
            # ABC VZ node 10G interfaces with force UP
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            vlan_sel = '110'
            vlan_sel2 = '190'
            vlan_sel3 = '250'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + ' lacp force-up\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' native-vlan-id 22\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')

                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        elif interface_ans == 'ABC_VZ_EVPN':
            # Configuration for ABC VZ hosts in EVPN env
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            vlan_sel = '110'
            vlan_sel2 = '190'
            vlan_sel3 = '250'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' encapsulation ethernet-bridge\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' esi all-active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                + str(sw_number) + ':00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                    + str(sw_number) + ':00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')

                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        elif interface_ans == 'Storage_EVPN':
            # Configuration for Storage hosts in EVPN env
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            vlan_sel = '100'
            vlan_sel2 = '200'
            vlan_sel2 = '280'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' encapsulation ethernet-bridge\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' esi all-active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                + str(sw_number) + ':00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                    + str(sw_number) + ':00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        elif interface_ans == 'Storage_QFX5120':
            # Configuration for Storage hosts in EVPN QFX5120 env
            if ':' in start_port:
                pass
            else:
                print(colored('Missing sub-port identificator(:), please start over and make sure to include it.\n'
                              'Your input = ' + start_port, 'red'))
                sys.exit()
            port_type = None
            number = 0
            name_sub_port_pairs = {}
            port_sel = 'et-0/0/'
            vlan_sel = '100'
            vlan_sel2 = '200'
            vlan_sel3 = '280'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            # removing : from the line
            converted_string = str(start_port).replace(':', '')
            # getting port and sub-port number
            if len(converted_string) < 3:
                port_number = int(converted_string[0])
                sub_port_number = int(converted_string[1])
            else:
                port_number = int(converted_string[:2])
                sub_port_number = int(converted_string[-1:])

            for i in range(0, number_of_servers):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                if int(sub_port_number) > 3:
                    sub_port_number = 0
                    port_number = int(port_number) + 1
                else:
                    pass
                number = str(port_number) + ':' + str(sub_port_number)
                device_name = str(description) + str(device_number)

                port_name.write('delete interfaces et-0/0/' + str(number) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' encapsulation ethernet-bridge\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' esi all-active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                    + str(sw_number) + ':00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                name_sub_port_pairs.update({str(device_name): int(sub_port_number)})
                device_number = device_number + 1
                ae_number = ae_number + 1
                sub_port_number = int(sub_port_number) + 1
            smarthands = __smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                      name_sub_port_pairs)

        elif interface_ans == 'ABC_VZ_QFX5120':
            # Configuration for ABC VZ hosts in EVPN QFX5120 env
            if ':' in start_port:
                pass
            else:
                print(colored('Missing sub-port identificator(:), please start over and make sure to include it.\n'
                              'Your input = ' + start_port, 'red'))
                sys.exit()
            port_type = None
            number = 0
            name_sub_port_pairs = {}
            port_sel = 'et-0/0/'
            vlan_sel = '110'
            vlan_sel2 = '190'
            vlan_sel3 = '250'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            # removing : from the line
            converted_string = str(start_port).replace(':', '')
            # getting port and sub-port number
            if len(converted_string) < 3:
                port_number = int(converted_string[0])
                sub_port_number = int(converted_string[1])
            else:
                port_number = int(converted_string[:2])
                sub_port_number = int(converted_string[-1:])

            for i in range(0, number_of_servers):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                if int(sub_port_number) > 3:
                    sub_port_number = 0
                    port_number = int(port_number) + 1
                else:
                    pass
                number = str(port_number) + ':' + str(sub_port_number)
                device_name = str(description) + str(device_number)

                port_name.write('delete interfaces et-0/0/' + str(number) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' encapsulation ethernet-bridge\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' esi all-active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                + str(sw_number) + ':00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                    + str(sw_number) + ':00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                name_sub_port_pairs.update({str(device_name): int(sub_port_number)})
                device_number = device_number + 1
                ae_number = ae_number + 1
                sub_port_number = int(sub_port_number) + 1
            smarthands = __smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                      name_sub_port_pairs)

        elif interface_ans == 'DR2_ESX_QFX5120':
            # Configuration for DR2 ESX hosts in EVPN QFX5120 env
            if ':' in start_port:
                pass
            else:
                print(colored('Missing sub-port identificator(:), please start over and make sure to include it.\n'
                              'Your input = ' + start_port, 'red'))
                sys.exit()
            port_type = None
            number = 0
            name_sub_port_pairs = {}
            port_sel = 'et-0/0/'
            vlan_sel = '180'
            vlan_sel2 = '970'
            vlan_sel3 = '1150'
            vlan_sel4 = '1160'
            vlan_sel5 = '1170'
            vlan_sel6 = 'dr20'
            # removing : from the line
            converted_string = str(start_port).replace(':', '')
            # getting port and sub-port number
            if len(converted_string) < 3:
                port_number = int(converted_string[0])
                sub_port_number = int(converted_string[1])
            else:
                port_number = int(converted_string[:2])
                sub_port_number = int(converted_string[-1:])

            for i in range(0, number_of_servers):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                if int(sub_port_number) > 3:
                    sub_port_number = 0
                    port_number = int(port_number) + 1
                else:
                    pass
                number = str(port_number) + ':' + str(sub_port_number)
                device_name = str(description) + str(device_number)

                port_name.write('delete interfaces et-0/0/' + str(number) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' mtu 9216\n')
                port_name.write('set interfaces et-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces et-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel5) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel6) + '\n')
                name_sub_port_pairs.update({str(device_name): int(sub_port_number)})
                device_number = device_number + 1
                ae_number = ae_number + 1
                sub_port_number = int(sub_port_number) + 1
            smarthands = __smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                      name_sub_port_pairs)
        elif interface_ans == 'DR2_Storage_QFX5120':
            # Configuration for DR2 Storage hosts in EVPN QFX5120 env
            if ':' in start_port:
                pass
            else:
                print(colored('Missing sub-port identificator(:), please start over and make sure to include it.\n'
                              'Your input = ' + start_port, 'red'))
                sys.exit()
            port_type = None
            number = 0
            name_sub_port_pairs = {}
            port_sel = 'et-0/0/'
            vlan_sel = '180'
            vlan_sel3 = '1150'
            vlan_sel4 = '1160'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            # removing : from the line
            converted_string = str(start_port).replace(':', '')
            # getting port and sub-port number
            if len(converted_string) < 3:
                port_number = int(converted_string[0])
                sub_port_number = int(converted_string[1])
            else:
                port_number = int(converted_string[:2])
                sub_port_number = int(converted_string[-1:])

            for i in range(0, number_of_servers):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                if int(sub_port_number) > 3:
                    sub_port_number = 0
                    port_number = int(port_number) + 1
                else:
                    pass
                number = str(port_number) + ':' + str(sub_port_number)
                device_name = str(description) + str(device_number)

                port_name.write('delete interfaces et-0/0/' + str(number) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' encapsulation ethernet-bridge\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' esi all-active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                + str(sw_number) + ':00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                    + str(sw_number) + ':00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                name_sub_port_pairs.update({str(device_name): int(sub_port_number)})
                device_number = device_number + 1
                ae_number = ae_number + 1
                sub_port_number = int(sub_port_number) + 1
            smarthands = __smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                      name_sub_port_pairs)
        elif interface_ans == 'DR2_DRC_QFX5120':
            # Configuration for DR2 DR Cloud hosts in EVPN QFX5120 env
            if ':' in start_port:
                pass
            else:
                print(colored('Missing sub-port identificator(:), please start over and make sure to include it.\n'
                              'Your input = ' + start_port, 'red'))
                sys.exit()
            port_type = None
            number = 0
            name_sub_port_pairs = {}
            port_sel = 'et-0/0/'
            vlan_sel = '970'
            vlan_sel2 = '1150'
            vlan_sel3 = '1170'
            vlan_sel4 = '2060'
            vlan_sel5 = '2160'
            vlan_sel6 = '2260'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            # removing : from the line
            converted_string = str(start_port).replace(':', '')
            # getting port and sub-port number
            if len(converted_string) < 3:
                port_number = int(converted_string[0])
                sub_port_number = int(converted_string[1])
            else:
                port_number = int(converted_string[:2])
                sub_port_number = int(converted_string[-1:])

            for i in range(0, number_of_servers):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                if int(sub_port_number) > 3:
                    sub_port_number = 0
                    port_number = int(port_number) + 1
                else:
                    pass
                number = str(port_number) + ':' + str(sub_port_number)
                device_name = str(description) + str(device_number)

                port_name.write('delete interfaces et-0/0/' + str(number) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' encapsulation ethernet-bridge\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' esi all-active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                + str(sw_number) + ':00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                    + str(sw_number) + ':00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel3) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel4) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel5) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel6) + '\n')
                name_sub_port_pairs.update({str(device_name): int(sub_port_number)})
                device_number = device_number + 1
                ae_number = ae_number + 1
                sub_port_number = int(sub_port_number) + 1
            smarthands = __smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                      name_sub_port_pairs)

        elif interface_ans == 'EDR_QFX5120':
            # Configuration for new EDR service nodes in EVPN QFX5120 env
            if ':' in start_port:
                pass
            else:
                print(colored('Missing sub-port identificator(:), please start over and make sure to include it.\n'
                              'Your input = ' + start_port, 'red'))
                sys.exit()
            port_type = None
            number = 0
            name_sub_port_pairs = {}
            port_sel = 'et-0/0/'
            vlan_sel = '110'
            vlan_sel2 = '190'
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel
            # removing : from the line
            converted_string = str(start_port).replace(':', '')
            # getting port and sub-port number
            if len(converted_string) < 3:
                port_number = int(converted_string[0])
                sub_port_number = int(converted_string[1])
            else:
                port_number = int(converted_string[:2])
                sub_port_number = int(converted_string[-1:])

            for i in range(0, number_of_servers):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                if int(sub_port_number) > 3:
                    sub_port_number = 0
                    port_number = int(port_number) + 1
                else:
                    pass
                number = str(port_number) + ':' + str(sub_port_number)
                device_name = str(description) + str(device_number)

                port_name.write('delete interfaces et-0/0/' + str(number) + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces et-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + device_name + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' encapsulation ethernet-bridge\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' esi 00:' + str(sw_number) +
                                ':00:00:00:00:00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' esi all-active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                if ae_number > 99:
                    if ae_number < 110:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                + str(sw_number) + ':00:00:01:0' + str(ae_number - 100) + '\n')
                    else:
                        port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                            + str(sw_number) + ':00:00:01:' + str(ae_number - 100) + '\n')
                else:
                    port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp system-id 00:'
                                    + str(sw_number) + ':00:00:00:' + str(ae_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                name_sub_port_pairs.update({str(device_name): int(sub_port_number)})
                device_number = device_number + 1
                ae_number = ae_number + 1
                sub_port_number = int(sub_port_number) + 1
            smarthands = __smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                      name_sub_port_pairs)    

        elif interface_ans == 'EDR_10G':
            # Configuration for new EDR service nodes in non-EVPN 10G env
            port_sel = 'xe-/0/'
            port_type = None
            sub_port_number = ''
            ae_sel = int(input('Please provide next available ae interface number (for example 34):'))
            ae_number = ae_sel

            vlan_sel = '110'
            vlan_sel2 = '190'
            for number in range(start_port, end_port):
                # Determine whether to add a leading 0 for device number in description
                if device_number < 10:
                    description = description_base[0] + '0'
                else:
                    description = description_base[0]
                port_name.write('delete interfaces xe-0/0/' + str(number) + '\n')
                port_name.write('delete interfaces xe-1/0/' + str(number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces xe-0/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                port_name.write('set interfaces xe-1/0/' + str(number) + ' ether-options 802.3ad ae' +
                                str(ae_number) + '\n')
                # ae interfaces
                port_name.write('set interfaces ae' + str(ae_number) + ' description ' + description +
                                str(device_number) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' mtu 9216\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' disable\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp active\n')
                port_name.write('set interfaces ae' + str(ae_number) + ' aggregated-ether-options lacp periodic fast\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching interface-mode trunk\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel) + '\n')
                port_name.write('set interfaces ae' + str(ae_number) +
                                ' unit 0 family ethernet-switching vlan members vlan' + str(vlan_sel2) + '\n')
                smarthands.append(__smarthands(dc_name, sw_name, number, description, device_number, port_type, port_sel,
                                               sub_port_number))
                device_number = device_number + 1
                ae_number = ae_number + 1

        else:
            print(interface_ans, ' not yet supported')

        # for smart hands file
        if 'IPMI' in interface_ans:
            smarthands_file = open('smarthands_IPMI.txt', 'w')
            smarthands_file.write('Hello team,\nPlease connect the servers using the connection schema below. '
                                  'All connections are copper Cat5 or Cat6 wires. IPMI port, '
                                  'sometimes called MGMT and marked green. '
                                  'For PXE port please use the first on-board 1G interface.\n')

        else:
            smarthands_file = open('smarthands_10G.txt', 'w')
            if port_sel == 'et-0/0/':
                smarthands_file.write('Hello team,\nPlease connect the servers to the fiber patch panel at the top of the rack. '
                                  'Please use 850nm transceivers and aqua color optics.\n'
                                  'Each server has two 10/25G ports/connections.\n')
            else:
                smarthands_file.write('Hello team,\nPlease connect the servers using the connection schema below. '
                                  'Please use 850nm transceivers and aqua color optics.\n'
                                  'Each server has two 10/25G ports/connections.\n')

        for item in smarthands:
            smarthands_file.write(str(item))
    except KeyboardInterrupt:
        print(colored('\nCancelled by user', 'yellow'))
        sys.exit()


if __name__ == '__main__':
    task_start_time = datetime.now()
    __main()
    task_end_time = datetime.now()
    task_total_time = task_end_time - task_start_time
    print(colored('\nTime spent for task' + str(task_total_time), 'yellow'))
