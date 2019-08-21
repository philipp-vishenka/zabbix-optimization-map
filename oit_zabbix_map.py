#!/usr/bin/python3
# -*- coding: utf-8 -*-


import argparse
import re
import sys
from pyzabbix import ZabbixAPI

__version__ = '2019.08.17'

config = {
    'zabbix': {
        'url': 'https://localhost/zabbix/',
        'user': 'zapi',
        'password': 'jDkwl(28*52bGH1'
    },
}

temp_name_korenix = r'^([0-9]+).Korenix$'
temp_name_radius = '.WF.Radius'
temp_name_moxa = '.MGate'
data = {}

parser = argparse.ArgumentParser()
parser.add_argument('host_host', type=str)
args = parser.parse_args()


def check_host(*kwargs):
    for hostname in kwargs:
        if not zapi.do_request(method='host.get',
                               params={'filter': {'host': [hostname]}})['result']:
            result = False
            break
        else:
            result = True

    return result


def req_host_data(data_dict):
    for key in data_dict:
        params_host = {
            'output': ['hostid'],
            'filter': {'host': data_dict[key]['hostname']}
        }
        host_get = zapi.do_request(method='host.get',
                                   params=params_host)['result'][0]

        params_host_interface = {
            'output': ['ip'],
            'filter': {
                'hostid': host_get['hostid'],
                'main': '1'
            }
        }
        host_interface_get = zapi.do_request(method='hostinterface.get',
                                             params=params_host_interface)['result'][0]

        data[key]['id'] = host_get['hostid']
        data[key]['ip'] = host_interface_get['ip']


if re.search(temp_name_korenix, args.host_host):
    data['kx'] = {'hostname': args.host_host}
    host_num = re.search(r'([0-9]+)', data['kx']['hostname'])[1]
    data['rs'] = {'hostname': host_num + temp_name_radius}
    data['mx'] = {'hostname': host_num + temp_name_moxa}
    map_name = '[scr] ÁÊÌ %s' % host_num
    ele_map_name = 'ÁÊÌ %s' % host_num

    zapi = ZabbixAPI(config['zabbix']['url'],
                     user=config['zabbix']['user'],
                     password=config['zabbix']['password'])

    if check_host(data['rs']['hostname'],
                  data['mx']['hostname']):

        req_host_data(data)

        map_id_for_up = []
        kx_selementid = ''

        par_all_temp_map = {
            'output': 'extend',
            'selectSelements': 'extend'
        }
        all_temp_map = zapi.do_request(method='map.get',
                                       params=par_all_temp_map)['result']

        for temp_map in all_temp_map:
            if not re.search(r'\[scr\]', temp_map['name']):
                for selement in temp_map['selements']:
                    if 'elements' in selement and re.search(r'\[scr\]', selement['label']):
                        for element in selement['elements']:
                            if ('hostid' in element) and element['hostid'] == data['kx']['id']:
                                kx_selementid = selement['selementid']
                                map_id_for_up.append(temp_map['sysmapid'])

        if not map_id_for_up:
            print('Maps for editing found: %s.' % map_id_for_up)
            sys.exit()

        elif len(map_id_for_up) > 1:
            print('Found several maps (%s) with element id: %s (%s) and a word [scr].' % (map_id_for_up,
                                                                                          data['kx']['id'],
                                                                                          data['kx']['hostname']))
            sys.exit()

        # Duplicate.
        try:
            par_dup_map_id = {
                'filter': {'name': map_name}
            }
            dup_map_id = zapi.do_request(method='map.get',
                                         params=par_dup_map_id)['result'][0]['sysmapid']

            print('Map %s exists.' % map_name)
            created_map_id = dup_map_id
        except:
            params_new_map = {
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
                            {'hostid': data['kx']['id']}
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
                            {'hostid': data['rs']['id']}
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
                            {'hostid': data['mx']['id']}
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

            created_map_id = zapi.do_request(method='map.create',
                                             params=params_new_map)['result']['sysmapids'][0]
            print('Map "%s" created.' % map_name)

        params_up_map = {
            'output': 'extend',
            'filter': {
                'sysmapid': map_id_for_up[0]
            },
            'selectSelements': 'extend'
        }
        updated_map_template = zapi.do_request(method='map.get',
                                               params=params_up_map)['result'][0]['selements']

        for position, element in enumerate(updated_map_template):
            if element['selementid'] == kx_selementid:
                element.update({'elementtype': '1'})
                element.update({'iconid_off': '154'})
                element.update({'label': '%s\r\nkx: %s\r\nrs: %s\r\nmx: %s' % (ele_map_name,
                                                                   data['kx']['ip'],
                                                                   data['rs']['ip'],
                                                                   data['mx']['ip'])})
                element.update({'elements': [{'sysmapid': created_map_id}]})
                updated_map_template[position] = element

        params_up_map = {
            'sysmapid': map_id_for_up[0],
            'selements': updated_map_template
        }
        zapi.do_request(method='map.update',
                        params=params_up_map)
        print('Map updated.')

    else:
        print('Hosts not found.')
        sys.exit()

else:
    print('Incorrect hostname: "%s" (template: %s).' % (args.host_host, temp_name_korenix))
    sys.exit()
