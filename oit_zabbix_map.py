#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import re
import sys
from pyzabbix import ZabbixAPI


__version__ = '2019.08.17'


config = {
    'zabbix': {
        'url': 'http://192.168.0.9/zabbix',
        'user': 'zabadm',
        'password': 'enable'
    },
}

temp_name_korenix = r'^([0-9]+).Korenix$'
temp_name_radius = '.Radius'
temp_name_moxa = '.MGate'


parser = argparse.ArgumentParser()
parser.add_argument('host_host', type=str)
args = parser.parse_args()


def check_host(hosts):
    for host in hosts:
        if not zapi.do_request(method='host.get',
                               params={'filter': {'host': [host]}})['result']:
            result = False
            break
        else:
            result = True

    return result


def req_host_data(arr):
    hosts_data = {}

    for host_name in arr:
        params_host = {
            'output': ['hostid'],
            'filter': {'host': host_name}
        }
        host = zapi.do_request(method='host.get',
                               params=params_host)['result'][0]

        params_host_interface = {
            'output': ['ip'],
            'filter': {
                'hostid': host['hostid'],
                'main': '1'
            }
        }
        host_interface = zapi.do_request(method='hostinterface.get',
                                         params=params_host_interface)['result'][0]

        hosts_data[host_name] = {'id': host['hostid'],
                                 'ip': host_interface['ip']}

    return hosts_data


if re.search(temp_name_korenix, args.host_host):
    list_hostname = []

    host_host_korenix = args.host_host
    list_hostname.append(host_host_korenix)

    host_host_number = re.search(r'([0-9]+).[A-z]+', host_host_korenix)[1]

    map_name = '[scr] БКМ %s' % host_host_number
    ele_map_name = 'БКМ %s' % host_host_number
    arr_host_host = []

    host_host_radius = '%s%s' % (host_host_number, temp_name_radius)
    arr_host_host.append(host_host_radius)
    list_hostname.append(host_host_radius)

    host_host_moxa = '%s%s' % (host_host_number, temp_name_moxa)
    arr_host_host.append(host_host_moxa)
    list_hostname.append(host_host_moxa)

    zapi = ZabbixAPI(config['zabbix']['url'],
                     user=config['zabbix']['user'],
                     password=config['zabbix']['password'])

    if check_host(arr_host_host):
        data = req_host_data(list_hostname)

        params_maps = {
            'output': 'extend',
            'selectSelements': 'extend'
        }
        maps = zapi.do_request(method='map.get',
                               params=params_maps)['result']

        array_maps = []
        selementid_korenix = ''

        for i_map in maps:
            if not re.search(r'\[scr\]', i_map['name']):
                for i_selement in i_map['selements']:
                    if 'elements' in i_selement and re.search(r'\[scr\]', i_selement['label']):
                        for i_element in i_selement['elements']:
                            if ('hostid' in i_element) and i_element['hostid'] == data[host_host_korenix]['id']:
                                selementid_korenix = i_selement['selementid']
                                array_maps.append(i_map['sysmapid'])

        if not array_maps:
            print('Maps for editing found: %s.' % array_maps)
            sys.exit()
        if len(array_maps) > 1:
            print('Found several maps with element id: %s (%s) and a word [scr].' % (data[host_host_korenix]['id'],
                                                                                     host_host_korenix))
            sys.exit()

        # Duplicate.
        map_bkm_id = zapi.do_request(method='map.get',
                                     params={'filter': {'name': map_name}})['result']

        if not map_bkm_id:
            template_map = {
                'name': map_name,
                'width': '600',
                'height': '600',
                'grid_size': '40',
                'label_format': '1',
                'label_type_host': '0',
                'label_type_hostgroup': '0',
                'label_type_trigger': '4',
                'label_type_map': '0',
                'label_type_image': '4',
                'selements': [
                    {
                        'selementid': '1',
                        'elements': [
                            {'hostid': data[host_host_korenix]['id']}
                        ],
                        'elementtype': '0',
                        'iconid_off': '154',
                        'label': '{HOST.NAME}\r\n{HOST.IP}\r\n{HOST.DESCRIPTION}',
                        'x': '276',
                        'y': '365'
                    },
                    {
                        'selementid': '2',
                        'elements': [
                            {'hostid': data[host_host_radius]['id']}
                        ],
                        'elementtype': '0',
                        'iconid_off': '124',
                        'label': '{HOST.NAME}\r\n{HOST.IP}\r\n{HOST.DESCRIPTION}',
                        'x': '156',
                        'y': '198'
                    },
                    {
                        'selementid': '3',
                        'elements': [
                            {'hostid': data[host_host_moxa]['id']}
                        ],
                        'elementtype': '0',
                        'iconid_off': '154',
                        'label': '{HOST.NAME}\r\n{HOST.IP}\r\n{HOST.DESCRIPTION}',
                        'x': '396',
                        'y': '205'
                    }
                ],
                "shapes": [
                    {
                        'type': '0',
                        'x': '0',
                        'y': '7',
                        'width': '600',
                        'height': '25',
                        'border_type': '0',
                        'text': '{MAP.NAME}',
                        'font': '9',
                        'font_size': '20',
                        'font_color': '969696'
                    }
                ],
                'links': [
                    {
                        'drawtype': '0',
                        'color': '00CC00',
                        'selementid1': '1',
                        'selementid2': '2'
                    },
                    {
                        'drawtype': '0',
                        'color': '00CC00',
                        'selementid1': '1',
                        'selementid2': '3'
                    }
                ]
            }

            map_bkm_id = zapi.do_request(method='map.create',
                                         params=template_map)['result']['sysmapids'][0]
            print('Map "%s" created.' % map_name)
        else:
            print('Map %s exists.' % map_name)
            map_bkm_id = map_bkm_id[0]['sysmapid']

        params_up_map = {
            'output': 'extend',
            'filter': {
                'sysmapid': array_maps[0]
                       },
            'selectSelements': 'extend'
        }

        old_selements = zapi.do_request(method='map.get',
                                        params=params_up_map)['result'][0]['selements']

        for position, element in enumerate(old_selements):
            if element['selementid'] == selementid_korenix:
                element.update({'elementtype': '1'})
                element.update({'iconid_off': '154'})
                element.update({'label': '%s\r\n%s\r\n%s\r\n%s' % (ele_map_name,
                                                                   data[host_host_korenix]['ip'],
                                                                   data[host_host_radius]['ip'],
                                                                   data[host_host_moxa]['ip'])})
                element.update({'elements': [{'sysmapid': map_bkm_id}]})
                old_selements[position] = element
                new_selements = old_selements

        test_map = {
            'sysmapid': array_maps[0],
            'selements': old_selements
        }

        upgrade_map = zapi.do_request(method='map.update',
                                      params=test_map)

        print('Script complete.')

    else:
        print('Hosts: %s not found.' % arr_host_host)
        sys.exit()

else:
    print('Incorrect hostname: "%s" (template: %s).' % (args.host_host,
                                                        temp_name_korenix))
    sys.exit()