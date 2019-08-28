"""Creates a map for equipment."""


import ast
import argparse
import json
import os
from dotenv import load_dotenv
from pyzabbix import ZabbixAPI


__author__ = "Vishenka Philipp"
__version__ = "1.0.0"


load_dotenv('../.env')


def main():
    # -hn "1300.22=BKM67-MB3170" -tp "[template] map" -sr = -
    parser = argparse.ArgumentParser()
    parser.add_argument("-hn", "--hostname", type=str, help="zabbix hostname {HOST.NAME}")
    parser.add_argument("-tp", "--template", type=str, help="zabbix template map")
    parser.add_argument("-sr", "--separator", nargs="+", help="")
    args = parser.parse_args()

    sep = separation_hostname(args.hostname, args.separator)
    # print(sep["update_map_name"])
    # print(sep["create_map_name"])
    # print(sep["number"])
    # print(args.template)

    zapi = ZabbixAPI(url=os.getenv('URL'),
                     user=os.getenv('USER'),
                     password=os.getenv('PASSWORD'))

    params_maps = {
        "output": "extend",
        "selectSelements": "extend",
        "selectLinks": "extend",
    }
    maps = zapi.do_request(method='map.get',
                           params=ast.literal_eval(str(params_maps)))['result']

    template_map = check_map(maps, args.template)
    if len(template_map):
        update_map = check_map(maps, sep["update_map_name"])
        if len(update_map):
            name_list = general_host_name(args.separator, template_map, sep["create_map_name"])
            # print(name_list)

            params_hosts = {
                'output': 'extend'
            }
            hosts = zapi.do_request(method='host.get',
                                    params=ast.literal_eval(str(params_hosts)))['result']

            host_info = check_host(hosts, name_list)
            if host_info:
                print(host_info)
                create_map_info = check_map(maps, sep["create_map_name"])
                if len(create_map_info):
                    print("1")
                else:
                    print("%s not found." % sep["create_map_name"])

                    new_map_temp = preparation_template(template_map, sep["create_map_name"], host_info)
                    zapi.do_request(method='map.create',
                                    params=ast.literal_eval(str(new_map_temp)))

            else:
                print(host_info)

        else:
            print('%s not found.' % sep["update_map_name"])

    else:
        print('%s not found.' % args.template)


def separation_hostname(hostname, separator):
    data = {}
    first_separator = hostname.split(separator[0])
    data["update_map_name"] = first_separator[0]
    data["create_map_name"] = hostname.split(separator[1])[0]
    second_separator = first_separator[1].split(separator[1])
    number = ""
    for i in second_separator[0]:
        if not i.isalpha():
            number += i
    data["number"] = number
    return data


def check_map(maps, name):
    for i in maps:
        if name in i["name"]:
            return [i]
    return []


def general_host_name(separator, template_map, create_map_name):
    name_list = []
    for i in template_map[0]["selements"]:
        name_list.append("%s%s%s" % (create_map_name, separator[1], i["label"]))
    return name_list


def check_host(hosts, name_list):
    arr = []
    for name in name_list:
        for host in hosts:
            if name == host["name"]:
                arr.append(host)
    if len(name_list) == len(arr):
        return arr
    else:
        return False


def preparation_template(map_temp, map_name, host_list):
    map_temp[0].update({"name": map_name})
    for i in map_temp[0]["selements"]:
        for host in host_list:
            if i["label"] in host["name"]:
                i.update({"label": "{HOST.NAME}"})
                i.update({"elementtype": "0"})
                i.update({"elements": [{"hostid": host["hostid"]}]})
    return map_temp


if __name__ == "__main__":
    main()
