#!/usr/bin/env python3

import iperf3

server = iperf3.Server()


server.bind_ip = "10.0.2.2"
server.port = 12345
server.verbose = False

while True:
    server.run()