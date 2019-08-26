"""Creates a map for equipment."""


import argparse
import json
import os
from dotenv import load_dotenv


__author__ = "Vishenka Philipp"
__version__ = "1.0.0"


load_dotenv('G:/python/conf/.env')
config = {
    'zabbix': {
        'url': os.getenv('URL'),
        'user': os.getenv('USER'),
        'password': os.getenv('PASSWORD')
    },
}


def main():
    # -hn "1300.21=BKM605.4-RB951G" -tp "[template] map" -sr = -
    parser = argparse.ArgumentParser()
    parser.add_argument("-hn", "--hostname", type=str, help="zabbix hostname {HOST.NAME}")
    parser.add_argument("-tp", "--template", type=str, help="zabbix template map")
    parser.add_argument("-sr", "--separator", nargs="+", help="")
    args = parser.parse_args()

    sep = separation_hostname(args.hostname, args.separator)
    print(sep["map_name"])
    print(sep["number"])


def separation_hostname(hostname, separator):
    data = {}
    first_separator = hostname.split(separator[0])
    data["map_name"] = first_separator[0]
    second_separator = first_separator[1].split(separator[1])
    number = ""
    for i in second_separator[0]:
        if not i.isalpha():
            number += i
    data["number"] = number
    return data


def check_map(map_name):
    print(1)


if __name__ == "__main__":
    main()
