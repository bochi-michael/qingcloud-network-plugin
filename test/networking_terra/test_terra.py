#!/usr/bin/evn python
# -*- coding: utf-8 -*-
import mox
import unittest
from networking_terra.ml2.mech_terra import TerraMechanismDriver
from oslo_config import cfg
from networking_terra.l3.terra_l3 import TerraL3RouterPlugin
from oslo_log import log as logging
from common.neutron_driver import NeutronDriver, BgpPeer
from networking_terra.qcext.qcext_terra import TerraQcExtDriver


LOG = logging.getLogger(__name__)


class TerraNetTestCases(unittest.TestCase):

    def setUp(self):
        super(TerraNetTestCases, self).setUp()
        self.m = mox.Mox()

    def tearDown(self):
        self.m.UnsetStubs()

    def get_driver(self):

        cfg.CONF(["--config-file",
                  "/etc/ml2_conf_terra.ini"])

        l3 = TerraL3RouterPlugin()
        ml2 = TerraMechanismDriver()
        ml2.initialize()
        qcext = TerraQcExtDriver()

        return NeutronDriver(l3, ml2, qcext)

    def test_net(self):

        vxnet_id = "vxnet-123456"
        router_id = "rtr-123456"
        l3vni = 12001
        l2vni = 11001
        vlan_id = 100
        user_id = 'usr-123456'
        ip_network = '192.168.0.0/24'
        gateway_ip = '192.168.0.1'
        host = 'tr02n34'

        bgp_peers = []
        bgp_peers.append(BgpPeer("169.254.2.2",
                                 "65101",
                                 "Border-Leaf-92160.02"))
        bgp_peers.append(BgpPeer("169.254.1.2",
                                 "65101",
                                 "Border-Leaf-92160.01"))

        driver = self.get_driver()

        driver.create_vpc(router_id, l3vni, user_id, bgp_peers=bgp_peers)

        driver.create_vxnet(vxnet_id, l2vni, ip_network, gateway_ip, user_id)

        driver.join_vpc(router_id, vxnet_id, user_id)

        driver.add_node(vxnet_id, l2vni, host, user_id, vlan_id)

        driver.remove_node(vxnet_id, host, user_id)

        driver.leave_vpc(router_id, vxnet_id, user_id)

        driver.delete_vxnet(vxnet_id, user_id)

        # cisco need roughly 10s to delete l3vni
        # need 10s interval when run this test repeatly
        driver.delete_vpc(router_id, user_id)

    def test_host(self):

        driver = self.get_driver()

        hostname = "jim_green"
        mgmt_ip = "198.18.0.2"
        connections = [{
                         "host_name": hostname,
                         "host_interface_name": "bond0",
                         "switch_name": "vpc1",
                         "switch_interface_name": "port-channel100"
                       }]

        driver.create_host(hostname, mgmt_ip, connections)

        ret = driver.get_host(hostname)
        self.assertEqual(ret["hostname"], hostname)
        self.assertEqual(ret["mgmt_ip"], mgmt_ip)
        self.assertEqual(ret["connections"], connections)

        driver.delete_host(hostname)

        self.assertIsNone(driver.get_host(hostname))

