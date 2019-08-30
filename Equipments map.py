"""Creates a map for equipment."""


import ast
import argparse
from os import environ
from dotenv import load_dotenv, find_dotenv
from pyzabbix import ZabbixAPI


__author__ = "Vishenka Philipp"
__version__ = "2019.08.30"


def separation_hostname(hostname, seps):
    data = {}
    sep_2 = hostname.split(seps[1])
    data["hostname_left"] = sep_2[0]
    data["name_new_map"] = sep_2[0]
    sep_2_left = sep_2[0].split(seps[0])
    data["name_main_map"] = sep_2_left[0]
    return data


def search_map(zapi, name):
    params = {
        "search": {"name": name},
        "output": "extend",
        "selectSelements": "extend",
        "selectLinks": "extend"
    }
    maps = zapi.do_request(method='map.get',
                           params=ast.literal_eval(str(params)))["result"]
    return maps


def generate_host_name(sep, template, hostname_left):
    hostname = []
    for i in template[0]["selements"]:
        if i["label"]:
            hostname.append("%s%s%s" % (hostname_left, sep, i["label"]))
    return hostname


def search_host(zapi, hostname_list):
    hosts = []
    for hostname in hostname_list:
        params_hosts = {
            "filter": {"name": hostname},
            'output': 'extend'
        }
        try:
            hosts.append(zapi.do_request(method='host.get',
                                         params=ast.literal_eval(str(params_hosts)))['result'][0])
        except IndexError:
            return []
    return hosts


def preparation_new_template(map_template, map_name, hosts):
    map_template[0].update({"name": map_name})
    for selement in map_template[0]["selements"]:
        for host in hosts:
            if selement["label"] in host["name"] and selement["label"]:
                print(selement["label"])
                selement.update({"label": "{HOST.NAME}\r\n{HOST.IP}\r\n{HOST.DESCRIPTION}"})
                selement.update({"elementtype": "0"})
                selement.update({"elements": [{"hostid": host["hostid"]}]})
    return map_template


def req_main_host_id(hostname, hosts):
    for host in hosts:
        if host["name"] == hostname:
            return host["hostid"]


def preparation_main_template(map_template, host_id, map_id, element_name):
    for selement in map_template[0]["selements"]:
        if selement["elements"] == [{"hostid": host_id}]:
            selement.update({"label": element_name})
            selement.update({"elementtype": "1"})
            selement.update({"elements": [{"sysmapid": map_id}]})
            return map_template
    return []


def main():
    # --prefix "[PRT]" -hn "1300.22=BKM67-MB3170" -tp "[template] BKM" -sr = -
    parser = argparse.ArgumentParser()
    parser.add_argument("-hn", "--hostname", type=str, help="zabbix hostname {HOST.NAME}")
    parser.add_argument("--prefix", type=str, help="prefix name main map")
    parser.add_argument("-tp", "--template", type=str, help="zabbix template map")
    parser.add_argument("-sr", "--separator", nargs="+", help="")
    args = parser.parse_args()

    zapi = ZabbixAPI(url=environ.get('ZABBIX_URL'),
                     user=environ.get('ZABBIX_USERNAME'),
                     password=environ.get('ZABBIX_PASSWORD'))

    data = separation_hostname(args.hostname, args.separator)

    map_template = search_map(zapi, args.template)
    if len(map_template) == 1:
        st_1_main_map = search_map(zapi, data["name_main_map"])

        main_map = []
        for ele in st_1_main_map:
            if args.prefix in ele["name"]:
                main_map.append(ele)

        if len(main_map) == 1:
            hostname_list = generate_host_name(args.separator[1], map_template, data["hostname_left"])
            hosts = search_host(zapi, hostname_list)
            if hosts and len(hosts) == len(hostname_list):
                new_map = search_map(zapi, data["name_new_map"])
                new_map_id = ""
                if len(new_map) == 0:
                    new_map = preparation_new_template(map_template, data["name_new_map"], hosts)
                    new_map_id = zapi.do_request(method='map.create',
                                                 params=ast.literal_eval(str(new_map)))["result"]["sysmapids"][0]
                elif len(new_map) == 1:
                    new_map_id = new_map[0]["sysmapid"]
                else:
                    print("Map '%s' not found (len(maps) > 1)." % data["name_new_map"])

                main_host_id = req_main_host_id(args.hostname, hosts)
                main_map = preparation_main_template(main_map, main_host_id, new_map_id, data["name_new_map"])
                if len(main_map) == 1:
                    zapi.do_request(method='map.update',
                                    params=ast.literal_eval(str(main_map)))
                else:
                    print("host_id on main map not found")
            else:
                print("Host '%s' not found (len(hosts) == 0 or > 1)." % hostname_list)
        else:
            print("Map '%s' not found (len(maps) == 0 or > 1)." % data["name_main_map"])
    else:
        print("Map '%s' not found (len(maps) == 0 or > 1)." % args.template)


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    main()
