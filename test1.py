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


def req_host_data(arr):
    for host_name in arr:
        params = {
            'output': ['hostid', 'interfaces'],
            'filter': {'host': [host_name]}
        }
        host = (zapi.do_request(method='host.get',
                                params=params)['result'][0])
        host_data[host_name] = {'id': host['hostid'], 'ip': host['interfaces']}

    return host_data


zapi = ZabbixAPI(config['zabbix']['url'],
                 user=config['zabbix']['user'],
                 password=config['zabbix']['password'])

list_hostname = ['1.Korenix']
host_data = {}

#req = req_host_data(list_hostname)
#print(req)


params_host = {
    'output': ['hostid'],
    'filter': {'host': '1.Korenix'}
        }
zabb1 = zapi.do_request(method='host.get',
                        params=params_host)['result'][0]

params_host_interface = {
    'output': ['ip'],
    'filter': {
        'hostid': '10279',
        'main': '1'
               }
        }
zabb2 = zapi.do_request(method='hostinterface.get',
                        params=params_host_interface)['result'][0]

print(zabb1['hostid'])
print(zabb2['ip'])
