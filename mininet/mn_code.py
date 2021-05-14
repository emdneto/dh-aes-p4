#!/usr/bin/python

import os
import sys

from time import sleep

from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.bmv2 import P4Switch
from mininet.term import makeTerm


def topology():
    'Create a network.'
    net = Mininet_wifi()

    for fname in os.listdir('pcaps'):
        if fname.endswith('.cap'):
            os.system('cd pcaps && rm -r {}'.format(fname))

    os.system("sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1")
    os.system("sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1")
    os.system("sudo sysctl -w net.ipv6.conf.default.autoconf=0")
    os.system("sudo sysctl -w net.ipv6.conf.lo.autoconf=0")

    info('*** Adding stations/hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/8', mac="00:00:00:00:00:01")
    h2 = net.addHost('h2', ip='10.0.0.2/8', mac="00:00:00:00:00:02")
    c1 = net.addHost('c1', ip='10.0.0.3/8', mac="00:00:00:00:00:03")

    arg = sys.argv
    json_file = '../p4src/build/{}.json'.format(arg[1])

    info('*** Adding P4 Switch\n')
    s1 = net.addSwitch('s1', cls=P4Switch, netcfg=True, loglevel='info',
                       json=json_file, thriftport=50001)
    s2 = net.addSwitch('s2', cls=P4Switch, netcfg=True, loglevel='info',
                       json=json_file, thriftport=50002)

    info('*** Creating links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s2)
    net.addLink(s1, s2)
    net.addLink(c1, s1)

    info('*** Starting network\n')
    net.start()
    net.staticArp()

    if arg[1] != 'no_crypto' and arg[1] != 'no_controller' and arg[2] == 'test':
        key0 = '0x4df2971c482e031fb3bd72fef68ff4905eb26bcd6f3eee3dca6d12131b251976'
        key1 = '0x80b9058aa1c3297837416c43409340e61e16dbc7799c5e2ed35ed55b92da4692'
    else:
        key0 = '0x0000000000000000000000000000000000000000000000000000000000000000'
        key1 = '0x0000000000000000000000000000000000000000000000000000000000000000'

    bits = '0x0'
    if arg[1] != 'no_crypto' and arg[1] != 'no_controller':
        if arg[3] == '128':
            bits = '0x0'
        elif arg[3] == '192':
            bits = '0x1'
        elif arg[3] == '256':
            bits = '0x2'

    cmd1 = 'simple_switch_CLI --thrift-port'
    cmd2 = 'table_add MyIngress.forward'

    if arg[1] == 'no_crypto' or arg[1] == 'no_controller':
        sleep(4)
        s1.cmd('{} 50001 <<<\"{} set_egress_spec 1 => 2\"'.format(cmd1, cmd2))
        sleep(1)
        s1.cmd('{} 50001 <<<\"{} set_egress_spec 2 => 1\"'.format(cmd1, cmd2))
        sleep(1)
        s2.cmd('{} 50002 <<<\"{} set_egress_spec 2 => 1\"'.format(cmd1, cmd2))
        sleep(1)
        s2.cmd('{} 50002 <<<\"{} set_egress_spec 1 => 2\"'.format(cmd1, cmd2))
        if arg[1] == 'no_controller':
            info('*** Adding data to tables, please wait until c1 and c2 xterms get closed.\n')
            table = '../utils/table.txt'
            makeTerm(s1, title='c1', cmd="bash -c '{} 50001 < {};'".format(cmd1, table))
            makeTerm(s2, title='c2', cmd="bash -c '{} 50002 < {};'".format(cmd1, table))
    else:
        # We need these two rules for key negotiation
        sleep(4)
        s1.cmd('{} 50001 <<<\"{} set_encrypt 3 0x812 => 2 {}\"'.format(cmd1, cmd2, key0))
        sleep(1)
        s2.cmd('{} 50002 <<<\"{} set_decrypt 2 0x812 => 1 {}\"'.format(cmd1, cmd2, key1))
        sleep(1)
        s1.cmd('{} 50001 <<<\"{} set_egress_spec 2 0x812 => 3\"'.format(cmd1, cmd2))

        sleep(1)
        s1.cmd('{} 50001 <<<\"{} set_flag 1 0x9999 => 2 0x3 {}\"'.format(cmd1, cmd2, bits))
        sleep(1)
        s2.cmd('{} 50002 <<<\"{} set_flag 2 0x9999 => 1 0x0 {}\"'.format(cmd1, cmd2, bits))

        info('*** Adding data to tables, please wait until c1 and c2 xterms get closed.\n')
        table = '../utils/table.txt'
        makeTerm(s1, title='c1', cmd="bash -c '{} 50001 < {};'".format(cmd1, table))
        makeTerm(s2, title='c2', cmd="bash -c '{} 50002 < {};'".format(cmd1, table))

    makeTerm(s1, title='eth1', cmd="bash -c 'tcpdump -i s1-eth1 -w pcaps/s1-eth1.cap;'")
    makeTerm(s1, title='eth2', cmd="bash -c 'tcpdump -i s1-eth2 -w pcaps/s1-eth2.cap;'")
    makeTerm(s1, title='eth3', cmd="bash -c 'tcpdump -i s1-eth3 -w pcaps/s1-eth3.cap;'")
    makeTerm(s2, title='eth1', cmd="bash -c 'tcpdump -i s2-eth1 -w pcaps/s2-eth1.cap;'")
    makeTerm(s2, title='eth2', cmd="bash -c 'tcpdump -i s2-eth2 -w pcaps/s2-eth2.cap;'")

    if arg[1] == 'no_crypto':
        makeTerm(h1, title='h1-send-data', cmd="bash -c 'python no_crypto/sender_data_miss.py;'")
    elif arg[1] == 'no_controller':
        makeTerm(h1, title='h1-send-aes', cmd="bash -c 'python no_controller/sender.py;'")
    else:
        if arg[2] == 'miss':
            makeTerm(h1, title='h1-send-miss', cmd="bash -c 'python miss/sender_data_miss.py;'")
            makeTerm(c1, title='c1-send-miss', cmd="bash -c 'python miss/sender_control_miss.py;'")
        elif arg[2] == 'dh':
            makeTerm(c1, title='c1-send-dh', cmd="bash -c 'python dh/sender_control_dh.py;'")
        elif arg[2] == 'aes':
            makeTerm(c1, title='c1-send-aes', cmd="bash -c 'python aes/sender_control_aes.py;'")
            makeTerm(h1, title='h1-send-aes', cmd="bash -c 'python aes/sender_data_aes.py;'")
        elif arg[2] == 'no-controller':
            makeTerm(h1, title='h1-send-aes', cmd="bash -c 'python test/sender_data_aes.py;'")
        elif arg[2] == 'test':
            makeTerm(c1, title='c1-send-aes', cmd="bash -c 'python test/sender_control_aes.py;'")
            makeTerm(h1, title='h1-send-aes', cmd="bash -c 'python test/sender_data_aes.py;'")

    info('*** Running CLI\n')
    CLI(net)

    info('*** Kill xterm terminals\n')
    os.system('pkill -9 -f \"xterm\"')

    info('*** Stopping network\n')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology()
