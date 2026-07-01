#!/usr/bin/env python3

import iperf3

client = iperf3.Client()
client.duration = 30  # in sec
client.server_hostname = '10.0.2.2'
client.port = 12345
client.protocol = 'tcp'
# client.reverse = True  # Toggles test direction (Server sends -> Client receives)
# client.num_streams = 2   # (# of TCP streams to open besides a default one opened (stream ID: 0))

print('Connecting to {0}:{1}'.format(client.server_hostname, client.port))
result = client.run()

if result.error:
    print(result.error)
else:
    print('')
    print('Test completed:')
    print('  started at         {0}'.format(result.time))
    print('  Test duration      {0}'.format(result.duration))
    print('  bytes transmitted  {0}'.format(result.sent_bytes)) # result.bytes for UDP
    print('  bytes received     {0}'.format(result.received_bytes))
    print('  retransmits        {0}'.format(result.retransmits))


    # print('  jitter (ms)        {0}'.format(result.jitter_ms)) # UDP-specific
    print('  avg cpu load       {0}%\n'.format(result.local_cpu_total))

    print('  Sent Megabits per second  (Mbps)       {0}'.format(result.sent_Mbps))
    print('  Received Megabits per second  (Mbps)   {0}'.format(result.received_Mbps))
    client_goodput = "%.3f" % ((result.received_bytes / client.duration) * 8 / (1024*1024))
    print('#--- Overall Goodput: %.3f Mbps' %((result.received_bytes / client.duration) * 8 / (1024*1024)) )
    client_retransm = result.retransmits
    # write results to file
    # output = "%s, %s \n" %(str(result.received_bytes).strip(), str((result.duration)).strip())
    output = "%s, %s, %s, %s \n" %(result.received_bytes, result.duration, client_goodput, client_retransm)
    f = open('temp.txt','a')
    f.write(output)
    f.close()

