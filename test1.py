#!/usr/bin/python3
# -*- coding: utf-8 -*-


import argparse
import re
import sys
from pyzabbix import ZabbixAPI


config = {
    'zabbix': {
        'url': 'http://192.168.0.9/zabbix',
        'user': 'zabadm',
        'password': 'enable'
    },
}


zapi = ZabbixAPI(config['zabbix']['url'],
                 user=config['zabbix']['user'],
                 password=config['zabbix']['password'])


data = {}


def check_host(*kwargs):
    for i in kwargs:
        print(i)


def req_host_data(data_dict):
    for key in data_dict:
        params_host_get = {
            'output': ['hostid'],
            'filter': {'host': data_dict[key]['hostname']}
        }
        host_get = zapi.do_request(method='host.get',
                                   params=params_host_get)['result'][0]

        params_host_interface_get = {
            'output': ['ip'],
            'filter': {
                'hostid': host_get['hostid'],
                'main': '1'
            }
        }
        host_interface_get = zapi.do_request(method='hostinterface.get',
                                             params=params_host_interface_get)['result'][0]

        data[key]['id'] = host_get['hostid']
        data[key]['ip'] = host_interface_get['ip']


kx_hostname = '1.Korenix'
mx_hostname = '1.Radius'
rs_hostname = '1.MGate'

data['kx'] = {'hostname': kx_hostname}
data['rs'] = {'hostname': rs_hostname}
data['mx'] = {'hostname': mx_hostname}

print(data)
req_host_data(data)
print(data)

check_host(data['kx']['hostname'],
           data['rs']['hostname'],
           data['mx']['hostname'])
