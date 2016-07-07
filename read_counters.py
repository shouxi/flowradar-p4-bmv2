#!/usr/bin/env python2

from __future__ import print_function

import os
import sys
import json

sys.path.append(os.path.expanduser("~/bmv2/tools"))
sys.path.append(os.path.expanduser("~/bmv2/targets/simple_switch"))

import runtime_CLI
from sswitch_runtime import SimpleSwitch
from sswitch_CLI import SimpleSwitchAPI


class sshandler(object):
    def __init__(self, thrift_ip='localhost', thrift_port=9090):
        pre = runtime_CLI.PreType.SimplePreLAG
        services = runtime_CLI.RuntimeAPI.get_thrift_services(pre)
        services.extend(SimpleSwitchAPI.get_thrift_services())

        standard_client, mc_client, sswitch_client = runtime_CLI.thrift_connect(
            thrift_ip, thrift_port, services)

        runtime_CLI.load_json_config(standard_client)
        self.ssapi = SimpleSwitchAPI(pre, standard_client, mc_client, sswitch_client)

        self.json_str = runtime_CLI.utils.get_json_config(standard_client, None)
        self.json_ = json.loads(self.json_str)

        self.register_names = {it["name"]: it["size"] for it in self.json_["register_arrays"]}
        self.counter_names = {it["name"]: it["size"] for it in self.json_["counter_arrays"]}

        print()

    def register_read(self, register_name, index):
        return self.ssapi.client.bm_register_read(0, register_name, index)

    def counter_read(self, counter_name, index):
        return self.ssapi.client.bm_counter_read(0, counter_name, index)

    def registers_dump(self):
        for name, size in self.register_names.items():
            if 'flow_filter' == name:
                continue
            print("Register {0} has {1} cells:".format(name, size))
            all_values = [self.register_read(name, i) for i in range(size)]
            print(all_values)
            #non_zero_values = {k: v for k, v in enumerate(all_values) if v is not 0}
            #print(non_zero_values)
            print()

    def counters_dump(self):
        for name, size in self.counter_names.items():
            print("Counter {0} has {1} cells:".format(name, size))
            all_values = [self.counter_read(name, i) for i in range(size)]
            print(all_values)
            #non_zero_values = {k: v for k, v in enumerate(all_values) if v is not 0}
            #print(non_zero_values)


def main():
    s1 = sshandler(thrift_port=9090)
    s1.registers_dump()
    s1.counters_dump()


if __name__ == '__main__':
    main()
