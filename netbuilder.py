#!/usr/bin/python

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink

from p4_mininet import P4Switch, P4Host

from time import sleep
import subprocess
import argparse
import os
import io


_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_THRIFT_BASE_PORT = 9090#22222

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)
parser.add_argument('--json', help='Path to JSON config file',
                    type=str, action="store", required=True)
parser.add_argument('--cli', help='Path to BM CLI',
                    type=str, action="store", required=True)

args = parser.parse_args()


class MyTopo(Topo):
    def __init__(self, sw_path, json_path, nb_hosts, nb_switches, links, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        for i in xrange(nb_switches):
            switch = self.addSwitch('s%d' % (i + 1),
                                    sw_path = sw_path,
                                    json_path = json_path,
                                    thrift_port = _THRIFT_BASE_PORT + i,
                                    pcap_dump = False, #True,
                                    device_id = i)

        for h in xrange(nb_hosts):
            ip = "10.0.{0}.10".format(h + 1)
            mac = "00:04:00:00:00:{0:02d}".format(h + 1)
            host = self.addHost('h%d' % (h + 1), ip=ip, mac=mac)

        for a, b in links:
            self.addLink(a, b)


def read_topo():
    nb_hosts = 0
    nb_switches = 0
    links = []
    with open("topo.txt", "r") as f:
        line = f.readline().strip()
        w, nb_switches = line.split()
        assert(w == "switches")
        line = f.readline().strip()
        w, nb_hosts = line.split()
        assert(w == "hosts")
        for line in f:
            if not f: break
            line = line.strip()
            a, b = line.split()
            links.append( (a, b) )
    return int(nb_hosts), int(nb_switches), links


def print_port(topo):
    links = []
    for h1 in topo.ports:
        for p1 in topo.ports[h1]:
            h2, p2 = topo.ports[h1][p1]
            links.append('{0}:{1} <----> {2}:{3}'.format(h1, p1, h2, p2))
    links.sort()
    print '# About links:'
    for s in links:
        print s
    return links


def main():
    nb_hosts, nb_switches, links = read_topo()

    topo = MyTopo(args.behavioral_exe,
                  args.json,
                  nb_hosts, nb_switches, links)

    net = Mininet(topo = topo,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None,
                  autoStaticArp = True,
                  autoSetMacs = True)
    net.start()

    for n in range(nb_hosts):
        h = net.get('h%d' % (n + 1))
        for off in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload eth0 %s off" % off
            print cmd
            h.cmd(cmd)
        print "disable ipv6"
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv4.tcp_congestion_control=reno")
        h.cmd("iptables -I OUTPUT -p icmp --icmp-type destination-unreachable -j DROP")

    sleep(2)
    commands = parser_commands()

    for i in range(nb_switches):
        #break
        #cmd = [args.cli, "--json", args.json, "--thrift-port", str(_THRIFT_BASE_PORT + i)]
        cmd = [args.cli, args.json, str(_THRIFT_BASE_PORT + i)]
        print ' '.join(cmd)
        switch_name = 's{0}'.format(i+1)
        sp = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        #for cmd_args in commands[switch_name]:
        cmd_args = '\n'.join(commands[switch_name])
        try:
            print(cmd_args)
            output = sp.communicate(cmd_args)
            print output
        except subprocess.CalledProcessError as e:
            print e
            print e.output

    sleep(1)

    print "Ready !"
    print_port(topo)

    CLI( net )
    net.stop()


def parser_commands(fn="commands.txt"):
    commands = {}
    with open("commands.txt", "r") as f:
        lines = f.readlines()
    switch_name_lst = []
    for line in lines:
        line = line.strip()
        if len(line) is 0 or line.startswith('#'):
            continue
        if line.startswith('set_switch'):
            switch_name_lst = line.split()[1:]
            continue
        for switch_name in switch_name_lst:
            commands.setdefault(switch_name, []).append(line)

    return commands


if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
