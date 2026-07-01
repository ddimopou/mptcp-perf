#===================================================================#
#  Author(s):                                                       #
#       Jonas Hammar:           Initial codebase (2022)             #
#       Dimitris Dimopoulos:    Modifications/enhancements (2024)   #
#                                                                   #
#===================================================================#


#!/usr/bin/env python3

from os import rename
from shutil import move, rmtree
import subprocess
import time as t
from subprocess import run
from subprocess import CompletedProcess
from timeit import default_timer as timer
from mininetenv_iperf import MininetEnvIperf
import pandas as pd
import os
import pwd, grp
import numpy


#                'Technology'   'Capacity'   'Latency'    'Loss'
link_info_dict = {  'WLAN'  :       [[],         [],        []],
                    '5G'    :       [[],         [],        []]
}


schedulers = {      #'TCP'              :       [0, "default", "fullmesh", "cubic"],
                    #'default_cubic'    :       [1, "default", "fullmesh", "cubic"],
                    #'default_lia'      :       [1, "default", "fullmesh", "lia"],
                    #'default_olia'     :       [1, "default", "fullmesh", "olia"],
                    #'default_balia'    :       [1, "default", "fullmesh", "balia"],
                    #'default_wvegas'   :       [1, "default", "fullmesh", "wvegas"],
                    #'default_bbr'      :       [1, "default", "fullmesh", "bbr"],
                    #'default_c-mpbbr'  :       [1, "default", "fullmesh", "c-mpbbr"],

                    #'blest_cubic'      :       [1, "blest", "fullmesh", "cubic"],
                    #'blest_lia'        :       [1, "blest", "fullmesh", "lia"],
                    #'blest_olia'       :       [1, "blest", "fullmesh", "olia"],
                    #'blest_balia'      :       [1, "blest", "fullmesh", "balia"],
                    #'blest_wvegas'     :       [1, "blest", "fullmesh", "wvegas"],
                    #'blest_bbr'        :       [1, "blest", "fullmesh", "bbr"],
                    #'blest_c-mpbbr'    :       [1, "blest", "fullmesh", "c-mpbbr"],

                    #'ecf_cubic'        :       [1, "ecf", "fullmesh", "cubic"],
                    #'ecf_lia'          :       [1, "ecf", "fullmesh", "lia"],
                    #'ecf_olia'         :       [1, "ecf", "fullmesh", "olia"],
                    #'ecf_balia'        :       [1, "ecf", "fullmesh", "balia"],
                    #'ecf_wvegas'       :       [1, "ecf", "fullmesh", "wvegas"],
                    #'ecf_bbr'          :       [1, "ecf", "fullmesh", "bbr"],
                    #'ecf_c-mpbbr'      :       [1, "ecf", "fullmesh", "c-mpbbr"],

                    #'rr_cubic'         :       [1, "roundrobin", "fullmesh", "cubic"],
                    #'rr_lia'           :       [1, "roundrobin", "fullmesh", "lia"],
                    #'rr_olia'          :       [1, "roundrobin", "fullmesh", "olia"],
                    #'rr_balia'         :       [1, "roundrobin", "fullmesh", "balia"],
                    #'rr_wvegas'        :       [1, "roundrobin", "fullmesh", "wvegas"],
                    #'rr_bbr'           :       [1, "roundrobin", "fullmesh", "bbr"],
                    #'rr_c-mpbbr'       :       [1, "roundrobin", "fullmesh", "c-mpbbr"],

                    #'llhd_cubic'       :       [1, "drs", "fullmesh", "cubic"],
                    #'llhd_lia'         :       [1, "drs", "fullmesh", "lia"],
                    #'llhd_olia'        :       [1, "drs", "fullmesh", "olia"],
                    #'llhd_balia'       :       [1, "drs", "fullmesh", "balia"],
                    #'llhd_wvegas'      :       [1, "drs", "fullmesh", "wvegas"],
                    #'llhd_bbr'         :       [1, "drs", "fullmesh", "bbr"],
                    #'llhd_c-mpbbr'     :       [1, "drs", "fullmesh", "c-mpbbr"],

                    #'ASYM'     :       [1, "asym", "fullmesh", "lia"]
}

# bulkList = [10**3 ,10**4 ,10**5 ,10**6 ,10**7 ,10**8 , 10**9]


CAPACITY = 0
LATENCY = 1
LOSS = 2

prot_key = 0
sched_key = 1
pathman_key = 2
cc_key = 3
singlePath = 0
saveDump = 1
kernel_trace = 1


def divide_latency(rtt):
    rtt = int(rtt [: -2])  # slicing -- truncates 'ms' suffix from the 'latency' attribute read from .csv
    # rtt = float(rtt [: -2])
    rtt /= 2
    return f'{rtt}ms'


def TCPTest(link_info):
    testNr = 0
    prot = 'TCP'
    for tech in link_info:
        for capacity in link_info[tech][ CAPACITY ]:
            for latency in link_info[tech][ LATENCY ]:
                # for req in bulkList:
                    # open('temp.txt','w').close ()
                    # new_name = f"{prot}:{tech}_{capacity}_{latency}_{req}"
                    new_name = f"{prot}:{tech}_{capacity}_{latency}"
                    m = MininetEnvIperf( schedulers[prot][prot_key],
                                   schedulers[prot][sched_key],
                                   schedulers[prot][pathman_key],
                                   schedulers[prot][cc_key], kernel_trace)
                    m.setLinks(bw1 = capacity, delay1 = divide_latency(latency),
                               bw2 = capacity, delay2 = divide_latency(latency)
                               )
                    m.setRouting()
                    m.startEnvironment()
                    
                    # m.runExperiment(saveDump, kernel_trace, req=req, name='iperf_results/'+new_name)
                    m.runExperiment(saveDump, kernel_trace, name='iperf_results/'+new_name)
                    del m

                    rename('temp.txt', new_name)
                    move(new_name, 'iperf_results/'+new_name)
                    testNr += 1
    return testNr


def MPTCPTest(link_info, sched):
    testNr = 0
    prot = sched   #Set to the multi-path protocol that should be used
    num = 1
    for tech_1 in link_info:
        if num == 0:    # avoid primary/secondary path, i.e., once 5G+WLAN combinations have been tested, no need to test again WLAN+5G
            break
        for tech_2 in link_info:
            for capacity_l1 in link_info[tech_1][ CAPACITY ]:
                for latency_l1 in link_info[tech_1][ LATENCY ]:
                    for loss_l1 in link_info[tech_1][ LOSS ]:
                        for capacity_l2 in link_info[tech_2][ CAPACITY ]:
                            for latency_l2 in link_info[tech_2][ LATENCY ]:
                                for loss_l2 in link_info[tech_2][ LOSS ]:
                                # for req in bulkList:
                                    if tech_1 == tech_2:    # avoid executing between same tech, i.e., 5G+5G or WLAN+WLAN
                                        continue
                                    open('temp.txt','w').close()
                                    # new_name = f"{prot}:{tech_1}_{capacity_l1}_{latency_l1 }+{ tech_2}_{capacity_l2}_{latency_l2}_{req}"
                                    new_name = f"{prot}__{tech_1}_{capacity_l1}_{latency_l1}_{loss_l1}__{ tech_2}_{capacity_l2}_{latency_l2}_{loss_l2}"

                                    m = MininetEnvIperf( schedulers[prot][prot_key],
                                                schedulers[prot][sched_key],
                                                schedulers[prot][pathman_key],
                                                schedulers[prot][cc_key], kernel_trace)
                                    m.setLinks(bw1 = capacity_l1, delay1 = divide_latency(latency_l1), loss1 = loss_l1,
                                            bw2 = capacity_l2, delay2 = divide_latency(latency_l2), loss2 = loss_l2
                                            )
                                    m.setRouting()
                                    m.startEnvironment()
                                    # m.runCli()

                                    # m.runExperiment(saveDump, kernel_trace, req=req, name= 'iperf_results/' + new_name)
                                    m.runExperiment(saveDump, kernel_trace, name= 'iperf_results/' + new_name)
                                    del m

                                    rename('temp.txt', new_name)
                                    move(new_name, 'iperf_results/'+ new_name)
                                    testNr += 1
        num = 0
    return testNr, prot


def link_config(filename, i):
    
    # #                'Technology'   'Capacity'   'Latency'    'Loss'
    # link_info_dict = {  'WLAN'  :       [[],         [],        []],
    #                     '5G'    :       [[],         [],        []]
    # }

    link_info_dict['WLAN'][CAPACITY].clear()
    link_info_dict['WLAN'][LATENCY].clear()
    link_info_dict['WLAN'][LOSS].clear()

    link_info_dict['5G'][CAPACITY].clear()
    link_info_dict['5G'][LATENCY].clear()
    link_info_dict['5G'][LOSS].clear()

    df = pd.read_csv(filename)
    link_info_dict['WLAN'][CAPACITY].append(df.iloc[i]['link1_bw'].item())
    link_info_dict['WLAN'][LATENCY].append(df.iloc[i]['link1_delay'])
    link_info_dict['WLAN'][LOSS].append(df.iloc[i]['link1_loss'].item())

    link_info_dict['5G'][CAPACITY].append(df.iloc[i]['link2_bw'].item())
    link_info_dict['5G'][LATENCY].append(df.iloc[i]['link2_delay'])
    link_info_dict['5G'][LOSS].append(df.iloc[i]['link2_loss'].item())

    return link_info_dict


def create_dir(dir_path):
    # df = pd.read_csv(filename)
    # dir_name = df.iloc[i]['id'] + '_' + df.iloc[i]['subdir_name']
    # dir_path = "/home/xx/mininet/mininet_dd/full_suite/iperf/iperf_results/" + dir_name      /* '/home/mininet/....' */
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
        uid = pwd.getpwnam("mininet").pw_uid
        gid = grp.getgrnam("mininet").gr_gid
        os.chown(dir_path, uid, gid)


def delete_directory(dir_path):
    if os.path.isdir(dir_path):
        rmtree(dir_path)
    else:
        raise Exception("Path either points to file or does not exist!")


def delete_file(file_path):
    if os.path.isfile(file_path):
        os.remove(file_path)
    else:
        raise Exception("File does not exist!")

def copy_to_remote(dirname, target_path):
    target_server_ip = 'xx.xx.xx.xx'        # add your remote file-server's IP
    target_server_port = 'xxxx'             # add your remote file-server's port
    target_server_user = 'username'         # add your remote file-server's username
    rsa_key_path = '/home/mininet/.ssh/id_rsa'  # modify accordingly
    hostKeyCheck = 'StrictHostKeyChecking accept-new'
    target_server = target_server_user + '@' + target_server_ip + ':' + target_path
    
    result = run(["scp", 
                  '-P', target_server_port,
                  '-o', hostKeyCheck,  
                  '-i', rsa_key_path, 
                  '-r', dirname, 
                  target_server], check=True)
    CompletedProcess.check_returncode(result)


# function that checks local disk utilisation 
def check_local_disk_util():
    df_out = run(["df", '-h', '/'], stdout=subprocess.PIPE)
    CompletedProcess.check_returncode(df_out)
    result = df_out.stdout.decode('utf-8').splitlines()[1].split()[4].rstrip('%')
    return int(result)


# function that deletes hanging kernel trace files (ofo)
def clean_lsof_files():
    # file_path = "/home/xx/mininet/mininet_dd/full_suite/iperf/"
    # lsof_out = run(["lsof", '|', 'grep', 'deleted', '|', 'grep', 'iperf', '|', 'wc', '-l'], stdout=subprocess.PIPE)
    lsof_out = run(['lsof'], stdout=subprocess.PIPE)
    CompletedProcess.check_returncode(lsof_out)
    deleted_out = run(['grep', 'deleted'], input=lsof_out.stdout, stdout=subprocess.PIPE)
    CompletedProcess.check_returncode(deleted_out)
    with open("pid.txt", 'w') as pid_file:
        iperf_out = run(['grep', 'iperf'], input=deleted_out.stdout, stdout=pid_file)
        ofo_out = run(['grep', 'ofo.txt'], input=deleted_out.stdout, stdout=pid_file)
        # CompletedProcess.check_returncode(iperf_out)
    with open("pid.txt", 'r') as pid_file:
        for pid_line in pid_file.readlines():
            # print("PID line: \n", pid_line)
            pid = str(pid_line).split()[1]
            # print("PID:\n", pid)
            kill_pid = run(['kill', '-9', pid], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            # CompletedProcess.check_returncode(kill_pid)
    delete_file("pid.txt")



if __name__ =="__main__":
    testNr = 0
    totalTimeStart = timer()
    if singlePath:
        testNr = TCPTest()

    if not singlePath:
        results_path = "/home/mininet/mininet/mininet_dd/full_suite/iperf/iperf_results/"       # local results path
        remote_path = '/home/ubuntu/code_backup/mininet_dd/full_suite/iperf/iperf_results/'     # remote server path -- modify accordingly
        for sched in schedulers.keys():
            disk_util = check_local_disk_util()
            if disk_util >= 85:
                raise Exception("Disk utilisation critical: >= 85%")
            # prepare schedulers main directory
            sched_dir = results_path + sched
            create_dir(sched_dir)
            par_dir_copied = 0  # parent dir copied remotely

            # filename = 'test_config.csv'
            filename = 'test_conf_dummy.csv'
            df = pd.read_csv(filename)
            for i in range(len(df)):
                # prepare link_info dictionary
                dict = link_config(filename, i)
                print("\n#---- DICT -------\n")
                print(dict)

                # prepare classified dirs (homogen, mild_het, int_het, v_int_het, mix_het)
                if str(df.iloc[i]['subdir_name']).startswith('hom'):
                    classif_dir = sched_dir + '/' + 'homogen'   
                elif str(df.iloc[i]['subdir_name']).startswith('mild_het'):
                    classif_dir = sched_dir + '/' + 'mild_het'
                elif str(df.iloc[i]['subdir_name']).startswith('int_het'):
                    classif_dir = sched_dir + '/' + 'int_het'
                elif str(df.iloc[i]['subdir_name']).startswith('v_int_het'):
                    classif_dir = sched_dir + '/' + 'v_int_het'
                elif str(df.iloc[i]['subdir_name']).startswith('mix_het'):
                    classif_dir = sched_dir + '/' + 'mix_het'
                create_dir(classif_dir)

                # prepare specific-results' main directory
                test_dir_name = df.iloc[i]['id'] + '_' + df.iloc[i]['subdir_name']
                test_dir_path = classif_dir + '/' + test_dir_name
                create_dir(test_dir_path)

                # create specific-results' subdirectory (execution: 5x)
                for j in range(5):  # 5x
                    subdir_path = str(test_dir_path) + '/r'+ str(j+1)
                    # print(subdir_path)
                    create_dir(subdir_path)

                    testNr, prot = MPTCPTest(dict, sched)
                    test_files = os.listdir(results_path)
                    for file in test_files:
                        if file.startswith(prot):
                            if os.path.isdir(os.path.join(results_path, file)):
                                print("\n-----DIR file---\n:", file)
                                continue
                            target_path = subdir_path + '/' + file
                            # print("----------- TARGET PATH-------:\n", target_path)
                            move(os.path.abspath('iperf_results/' + file), target_path)    # WORKING locally UP to HERE! // uncomment below block to transfer results to remote file-server
# ------------------------------------------------------------------------------------------------------------------------#
    #                 # Tranfer to remote backup server!
    #                 # print("\n J out:\n", j)
    #                 if j == 4 and i < len(df) - 1:  # test case ahead
    #                     # print("\n J in a):\n", j)
    #                     current_set = str(df.iloc[i]['subdir_name']).rstrip('_')
    #                     next_set = str(df.iloc[i+1]['subdir_name']).rstrip('_')
    #                     print("\n\n---- current_set: %s, next_set: %s ----\n" % (current_set, next_set))
    #                     if current_set != next_set:     # main set change -- transfer current test-set folder to backup server
    #                         if par_dir_copied == 0:
    #                             dirname = sched_dir + '/'   # copy at scheduler level
    #                             target_path = remote_path
    #                             print("\n parent_dir_copied_0 =%s, dirname=%s, target_path=%s" % (par_dir_copied, dirname, target_path))
    #                         elif par_dir_copied == 1:       # copy at test-set level
    #                             dirname = classif_dir
    #                             target_path = remote_path + sched + '/'
    #                             print("\n parent_dir_copied_1 =%s, dirname=%s, target_path=%s" % (par_dir_copied, dirname, target_path))
    #                         copy_to_remote(dirname, target_path)
    #                         delete_directory(classif_dir)
    #                         par_dir_copied = 1
    #                 elif j==4 and i == len(df) - 1:  # last test case -- transfer last test-set folder to backup server
    #                     # print("\n J in b):\n", j)
    #                     dirname = classif_dir
    #                     target_path = remote_path + sched + '/'
    #                     print("\n Last test: parent_dir_copied_2 =%s, dirname=%s, target_path=%s" % (par_dir_copied, dirname, target_path))
    #                     copy_to_remote(dirname, target_path)
    #         delete_directory(sched_dir)
    #         clean_lsof_files()
    # totalTimeEnd = timer()
    # print(f"Nr of tests : {testNr}, execution time: {totalTimeEnd - totalTimeStart}")