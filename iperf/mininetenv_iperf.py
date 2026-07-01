#===================================================================#
#  Author(s):                                                       #
#       Jonas Hammar:           Initial codebase (2022)             #
#       Dimitris Dimopoulos:    Modifications/enhancements (2024)   #
#                                                                   #
#===================================================================#

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import Link , TCLink ,Intf
from mininet.log import setLogLevel
from mininet.util import pmonitor
from subprocess import Popen , PIPE , run
from time import sleep
import subprocess
import os
import pwd, grp

server_ip = '10.0.2.2'
server_port = '12345'

setLogLevel('debug')
class MininetEnvIperf():

    def __init__(self, mptcp=1, scheduler="default", pm="fullmesh", cc="lia", kernel_trace = 0, tcp_no_metrics_save = 1, cs = 0):
        mptcp_key   =   "net.mptcp.mptcp_enabled"
        sched_key   =   "net.mptcp.mptcp_scheduler"
        pm_key      =   "net.mptcp.mptcp_path_manager"
        tcp_nms_key =   "net.ipv4.tcp_no_metrics_save"
        cc_key      =   "net.ipv4.tcp_congestion_control"
        cs_key      =   "net.mptcp.mptcp_checksum"

        ## --- SOS: force execution to fail in case a parameter cannot be set -- currently ignores whether proper value is actually applied -- misleading! ---#
        p = Popen("sysctl -w %s=%s" % (mptcp_key, mptcp), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        print("stdout=", stdout, "stderr=", stderr)
        p = Popen("sysctl -w %s=%s" % (sched_key, scheduler), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        print("stdout=", stdout, "stderr=", stderr)
        p = Popen("sysctl -w %s=%s" % (pm_key, pm), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        print("stdout=", stdout, "stderr=", stderr)
        p = Popen("sysctl -w %s=%s" % (tcp_nms_key, tcp_no_metrics_save), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        print("stdout=", stdout, "stderr=", stderr)
        p = Popen("sysctl -w %s=%s" % (cc_key, cc), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        print("stdout=", stdout, "stderr=", stderr)
        p = Popen("sysctl -w %s=%s" % (cs_key, cs), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        print("stdout=", stdout, "stderr=", stderr)

        # kernel_trace -- enable/disable tcp_probe (collect 'srtt' and 'snd_cwnd')
        tcp_probe_path = "/sys/kernel/debug/tracing/events/tcp/tcp_probe/enable"
        if kernel_trace != 1 and kernel_trace != 0:
            print("ERROR: tcp_probe value should be either 0 or 1")
        print("\n#######------>  kernel_trace: %s, path: %s" %(kernel_trace, tcp_probe_path))
        p = Popen("echo %s > %s" % (kernel_trace, tcp_probe_path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        print("stdout=", stdout, "stderr=", stderr)

        self.ctx = Mininet(link=TCLink)


    def __del__(self):
        self.ctx.stop()

    def setLinks(self , bw1=10, delay1='0ms', bw2=10, delay2='0ms', loss1=0, loss2=0):  # delay=None
        self.h1 = self.ctx.addHost('h1')
        self.h2 = self.ctx.addHost('h2')
        self.r = self.ctx.addHost('r')

        linkopt1 ={'bw':bw1, 'delay':delay1, 'loss':loss1}
        linkopt2 ={'bw':bw2, 'delay':delay2, 'loss':loss2}
        linkopt3 ={'bw': 2000}  # check if less is needed, e.g. 1Gbps
        self.ctx.addLink(self.r, self.h1, cls=TCLink, ** linkopt1)
        self.ctx.addLink(self.r, self.h1, cls=TCLink, ** linkopt2)
        self.ctx.addLink(self.r, self.h2, cls=TCLink, ** linkopt3)
        self.ctx.build()

    def setRouting(self):
        self.r.cmd("ifconfig r-eth0 0")
        self.r.cmd("ifconfig r-eth1 0")
        self.r.cmd("ifconfig r-eth2 0")

        self.h1.cmd("ifconfig h1-eth0 0")
        self.h1.cmd("ifconfig h1-eth1 0")
        self.h2.cmd("ifconfig h2-eth0 0")

        self.r.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")
        self.r.cmd("ifconfig r-eth0 10.0.0.1 netmask 255.255.255.0")
        self.r.cmd("ifconfig r-eth1 10.0.1.1 netmask 255.255.255.0")
        self.r.cmd("ifconfig r-eth2 10.0.2.1 netmask 255.255.255.0")
        self.h1.cmd("ifconfig h1-eth0 10.0.0.2 netmask 255.255.255.0")
        self.h1.cmd("ifconfig h1-eth1 10.0.1.2 netmask 255.255.255.0")
        self.h2.cmd("ifconfig h2-eth0 10.0.2.2 netmask 255.255.255.0")

        self.h1.cmd("ip rule add from 10.0.0.2 table 1")
        self.h1.cmd("ip rule add from 10.0.1.2 table 2")
        self.h1.cmd("ip route add 10.0.0.0/24 dev h1-eth0 scope link table 1")
        self.h1.cmd("ip route add default via 10.0.0.1 dev h1-eth0 table 1")
        self.h1.cmd("ip route add 10.0.1.0/24 dev h1-eth1 scope link table 2")
        self.h1.cmd("ip route add default via 10.0.1.1 dev h1-eth1 table 2")
        self.h1.cmd("ip route add default scope global nexthop via 10.0.0.1 dev h1-eth0")
        self.h2.cmd("ip rule add from 10.0.2.2 table 1")
        self.h2.cmd("ip route add 10.0.2.0/24 dev h2-eth0 scope link table 1")
        self.h2.cmd("ip route add default via 10.0.2.1 dev h2-eth0 table 1")
        self.h2.cmd("ip route add default scope global nexthop via 10.0.2.1 dev h2-eth0")

        # self.h1.cmd("ethtool -K h1-eth0 tso off gso off gro off lro off sg off")
        # self.h1.cmd("ethtool -K h1-eth1 tso off gso off gro off lro off sg off")
        # self.h2.cmd("ethtool -K h2-eth0 tso off gso off gro off lro off sg off")


    def setProtocol(self):
        pass

    def startEnvironment(self):
        #CLI(self.ctx)
        self.ctx.start()

    def stopEnvironment(self):
        self.ctx.stop()

    # def runExperiment(self, saveDump, req, name):
    def runExperiment(self, saveDump, kernel_trace, name):
        h1 = self.ctx.get('h1')
        h2 = self.ctx.get('h2')

        # saveDump = 0
        if saveDump:
            # create dir if it doesn't exist
            # dir_path = "/home/xx/mininet/mininet_dd/full_suite/iperf/iperf_results"
            dir_path = "/home/mininet/mininet/mininet_dd/full_suite/iperf/iperf_results"
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
                uid = pwd.getpwnam("mininet").pw_uid
                gid = grp.getgrnam("mininet").gr_gid
                os.chown(dir_path, uid, gid)

            #--- tcpdump
            p3 = h2.popen(f"tcpdump -s128 -w {name}.pcap -i h2-eth0 tcp port 12345")
            sleep (0.5)
            
            #--- OFO queue trace
            with open(f"{name}__ofo.txt", 'w') as ofo:
                p4 = h1.popen("dmesg -w | grep -i ofo", shell=True, stdout=ofo, stderr=PIPE)

            #--- Trace SRTT and CWND per subflow
            trace_pipe_path = "/sys/kernel/debug/tracing/trace_pipe"
            # target_addr_filter = "dest=10.0.2.2:12345"
            target_addr_filter = 'dest=' + server_ip + ':' + server_port  # "dest=10.0.2.2:12345"
            sf1 = "mptcp=1"
            sf2 = "mptcp=2"

            if kernel_trace:
                # sf1_srtt
                with open(f"{name}__sf1_srtt.txt", 'w') as sf1_srtt:
                    p5 = Popen("cat %s | grep -i '%s' | grep -i '%s' | grep -i 'srtt'" % (trace_pipe_path, target_addr_filter, sf1), shell=True, stdout=sf1_srtt, stderr=PIPE)
                # sf2_srtt
                with open(f"{name}__sf2_srtt.txt", 'w') as sf2_srtt:
                    p6 = Popen("cat %s | grep -i '%s' | grep -i '%s' | grep -i 'srtt'" % (trace_pipe_path, target_addr_filter, sf2), shell=True, stdout=sf2_srtt, stderr=PIPE)

        p2 = h2.popen("python3 iperf3_server.py")  # change this according to verify.py // popen is non-blocking
        # h2.sendCmd("iperf3 -s")
        sleep (0.3)
        # h1.sendCmd(f"iperf3 -c 10.0.2.2 -i 1 -t 20 {req}")  # -R for reverse traffic: server -> client // mininet sendCmd is non-blocking // h1.cmd is blocking
        h1.sendCmd("python3 iperf3_client.py")

        results = {}
        results[0] = h1.waitOutput ()

        p2.terminate()

        if saveDump:
            # terminate processes
            p3.terminate()
            p4.terminate()

            p5.terminate()
            p6.terminate()

    def runCli(self):
        CLI(self.ctx)