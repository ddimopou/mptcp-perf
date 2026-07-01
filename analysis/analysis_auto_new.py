#=======================================#
#  Author(s):                           #
#       Dimitris Dimopoulos (2024)      #
#                                       #
#=======================================#


#!/usr/bin/python3

''' Script for goodput analysis of all pcap files residing into 'iperf_results/' directory '''  # to be updated 
''' analysis_auto_new.py: 'analysis(..)' , 'merge_csv(..)' functions created to offload code from main()  '''

import pyshark
from sys import argv
from timeit import default_timer as timer
import os
from shutil import move, rmtree
from subprocess import run, Popen, PIPE
from subprocess import CompletedProcess
import pandas as pd
from time import sleep

# from ..iperf.control_minimal_iperf_auto import create_dir, delete_file
import pwd, grp


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


def copy_from_remote(remote_path, local_path):
    target_server_ip = 'xx.xx.xx.xx'        # add your remote file-server's IP
    target_server_port = 'xxxx'             # add your remote file-server's port
    target_server_user = 'username'         # add your remote file-server's username
    rsa_key_path = '/home/mininet/.ssh/id_rsa'  # modify accordingly
    hostKeyCheck = 'StrictHostKeyChecking accept-new'
    target_server = target_server_user + '@' + target_server_ip + ':' + remote_path
    
    result = run(["scp", 
                  '-P', target_server_port,
                  '-o', hostKeyCheck,  
                  '-i', rsa_key_path, 
                  '-r', target_server, 
                  local_path], check=True)
    CompletedProcess.check_returncode(result)


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


def create_remote_dir(dirname, target_path, pattern=None):
    # subprocess.run is blocking; while subprocess.Popen is non-blocking
    full_dir = os.path.join(target_path, dirname)

    target_server_ip = 'xx.xx.xx.xx'        # add your remote file-server's IP
    target_server_port = 'xxxx'             # add your remote file-server's port
    target_server_user = 'username'         # add your remote file-server's username
    rsa_key_path = '/home/mininet/.ssh/id_rsa'  # modify accordingly
    hostKeyCheck = 'StrictHostKeyChecking accept-new'
    target_server = target_server_user + '@' + target_server_ip

    if pattern is not None:
        result = run(['ssh', 
                '-p', target_server_port, 
                '-o', hostKeyCheck, 
                '-i', rsa_key_path, 
                target_server, 'ls', '-l', target_path], check=True, shell=False, stdout=PIPE, stderr=PIPE)
        check_dir =  run(['grep', pattern], input=result.stdout, stdout=PIPE, stderr=PIPE, shell=False)
        
        if not check_dir.stdout.decode('utf-8'):  # enter if True --> that is, when check_dir above is False -> False if dir pattern not found 
            run_mkdir = run(['ssh', 
                  '-p', target_server_port, 
                  '-o', hostKeyCheck, 
                  '-i', rsa_key_path, 
                  target_server, 'mkdir', '-p', full_dir], check=True, shell=False, stdout=PIPE, stderr=PIPE)
            CompletedProcess.check_returncode(run_mkdir)
    else:
        run_mkdir = run(['ssh', 
                  '-p', target_server_port, 
                  '-o', hostKeyCheck, 
                  '-i', rsa_key_path, 
                  target_server, 'mkdir', '-p', full_dir], check=True, shell=False, stdout=PIPE, stderr=PIPE)
        CompletedProcess.check_returncode(run_mkdir)
    # print("\n--CHECK stdout:", check_dir.stdout, type(check_dir.stdout.decode('utf-8')))


def create_dir(dir_path):
    # df = pd.read_csv(filename)
    # dir_name = df.iloc[i]['id'] + '_' + df.iloc[i]['subdir_name']
    # dir_path = "/home/xx/mininet/mininet_dd/full_suite/iperf/iperf_results/" + dir_name
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


def sorted_dir_list(dir):
    content = os.listdir(dir)
    sorted_content = sorted(content)
    return sorted_content


def found_file_pattern(target_dir, pattern):
    found = False
    for file in os.listdir(target_dir):
        filename = os.path.join(target_dir, file)
        if os.path.isfile(filename) and pattern in str(filename):
            found = True
        else:
            continue
    return found


def return_file_w_pattern(dir, pattern):
    found = False
    for file in os.listdir(dir):
        filename = os.path.join(dir, file)
        if os.path.isfile(filename) and pattern in str(filename):
            found = True
            break
    if found:
        return file
    else:
        print("File with requested pattern not found!\n")
        exit()


def convert_file_pattern(parameter, pattern):
    if parameter == 'snd_cwnd' and pattern == 'sf1_srtt':
        target_file_pattern = 'sf1_snd_cwnd'
    elif parameter == 'snd_cwnd' and pattern == 'sf2_srtt':
        target_file_pattern = 'sf2_snd_cwnd'
    else:
        target_file_pattern = pattern
    return target_file_pattern


def return_test_prefix(direc, suffix):
    for filename in os.listdir(direc):
        if filename.endswith(suffix):
            file_prefix = filename.split(suffix)[0]
            break
    return file_prefix


def get_pat_from_param(parameter):
    pat_list = []
    if parameter == 'srtt':
        pat_list = ['sf1_srtt', 'sf2_srtt']
    elif parameter == 'snd_cwnd':
        pat_list = ['sf1_srtt', 'sf2_srtt']
    elif parameter == 'ofo':
        pat_list = ['ofo']
    return pat_list


''' pcap file post-processing to calculate the overall and the per-subflow goodput '''
def calculate_goodput(pcap_file):
    sf1_addr = '10.0.0.2'
    sf2_addr = '10.0.1.2'
    filter = 'and !(tcp.analysis.retransmission) and  !(tcp.analysis.spurious_retransmission) and !(tcp.analysis.fast_retransmission)'
    filter_str1 = f"(ip.addr == {sf1_addr})" + filter
    filter_str2 = f"(ip.addr == {sf2_addr})" + filter

    cap1 = pyshark.FileCapture(f"{pcap_file}", display_filter= filter_str1)
    cap2 = pyshark.FileCapture(f"{pcap_file}", display_filter= filter_str2)

    cap_list = [cap1, cap2]
    cap_names = ["cap1", "cap2"]

    caps = {
        "cap1" : {
            "total_payload" : 0,
            "start_time"    : None,
            "end_time"      : None,
            "goodput"       : 0
        },
        "cap2" : {
            "total_payload" : 0,
            "start_time"    : None,
            "end_time"      : None,
            "goodput"       : 0
        }
    }

    i=-1
    for cap in cap_list:
        i+=1
        total_payload = 0
        start_time = None
        end_time = None
        for packet in cap:
            if 'TCP' in packet:
                # print("#---///---packet", packet)
                if start_time is None:
                    start_time = float(packet.sniff_time.timestamp())
                end_time = float(packet.sniff_time.timestamp())
                total_payload += int(packet.tcp.len)
        # print("#-- cap=", cap_names[i])
        caps[cap_names[i]]["total_payload"] = total_payload
        caps[cap_names[i]]["start_time"] = start_time
        caps[cap_names[i]]["end_time"] = end_time
        cap.close()

    # calculate goodput
    i=-1
    for cap in cap_list:
        i+=1
        if caps[cap_names[i]]["start_time"] is not None and caps[cap_names[i]]["end_time"] is not None:
            duration = caps[cap_names[i]]["end_time"] - caps[cap_names[i]]["start_time"]
            # goodput = total_payload / duration  # bytes per second
            goodput_mib = (caps[cap_names[i]]["total_payload"] / duration) * 8 / (1024*1024)  # Mbit/s 
            caps[cap_names[i]]["goodput"] = goodput_mib
            #return goodput
            #return duration
        else:
            caps[cap_names[i]]["goodput"] = -1  # indicative of invalid entry for subsequent validation
    return caps


''' pcap file post-processing to calculate the overall and the per-subflow retransmissions '''
def calculate_retransmissions(pcap_file):
    sf1_addr = '10.0.0.2'
    sf2_addr = '10.0.1.2'
    filter = 'and ((tcp.analysis.retransmission) or (tcp.analysis.spurious_retransmission) or (tcp.analysis.fast_retransmission))'
    filter_str1 = f"(ip.addr == {sf1_addr})" + filter
    filter_str2 = f"(ip.addr == {sf2_addr})" + filter

    cap1 = pyshark.FileCapture(f"{pcap_file}", display_filter= filter_str1)
    cap2 = pyshark.FileCapture(f"{pcap_file}", display_filter= filter_str2)

    cap_list = [cap1, cap2]
    cap_names = ["cap1", "cap2"]

    caps = {
        "cap1" : {
            "retransmissions" : 0
        },
        "cap2" : {
            "retransmissions" : 0
        }
    }

    # Alternative code-block:  Retransmisisons' calculation -- Load pcap in memory (faster but memory intensive)
    i=-1
    for cap in cap_list:
        i+=1
        print("#-- cap=", cap_names[i])
        cap.load_packets()
        caps[cap_names[i]]["retransmissions"] = len(cap)
        cap.close()
    return caps


def create_file(dirpath, filename, suffix=None):
    if suffix is not None:
        filename = str(filename) + str(suffix)
    full_file_path = os.path.join(dirpath, filename)
    found = found_file_pattern(dirpath, filename)
    if found is not True:
        with open(full_file_path, 'a') as fp:
            pass


def create_csv_file(dirpath, prefix, filetype):
    if filetype == 'goodput':
        csv_name = f"{prefix}__goodput.csv"
        csv_full_name = os.path.join(dirpath, csv_name)
        with open(csv_full_name, 'w', encoding='utf-8') as gp:
            gp.write("scheduler,overall_gp,sf1_gp,sf2_gp,retransmissions,overall_retransm,sf1_retransm,sf2_retransm,bytes,duration\n")
    else:
        csv_name = f"{prefix}__{filetype}.csv"
        csv_full_name = os.path.join(dirpath, csv_name)
        with open(csv_full_name, 'w', encoding='utf-8') as f:
            f.write(f"scheduler,{filetype}\n")
    return csv_full_name


def copy_csv_file_content(source_file_path, target_file_path, mode=None, header=None):
    df = pd.read_csv(source_file_path)
    if mode is not None and header is not None:
        df.to_csv(target_file_path, index=False, mode=mode, header=header)
    elif mode is None and header is not None:
        df.to_csv(target_file_path, index=False, header=header)
    elif mode is not None and header is None:
        df.to_csv(target_file_path, index=False, mode=mode)
    else:
        df.to_csv(target_file_path, index=False, mode='a', header=True)


''' Checks whether scheduler path contains all five high-level scenario directories: 'homogen', 'mild_het', 'int_het', 'v_int_het', 'mix_het' '''
def post_analysis_outer_scen_validation(filepath):  # Returns 'True' if validation is successful.
    invalid, homogen, mild_het, int_het, v_int_het, mix_het = 0, 0, 0, 0, 0, 0
    valid_pass = True
    for dir in os.listdir(filepath):
        full_dir_path = os.path.join(filepath, dir)
        if os.path.isfile(full_dir_path):
            invalid += 1
    for dir in os.listdir(filepath):
        if str(dir).startswith('homogen') is True:
            homogen += 1
        elif str(dir).startswith('mild_het') is True:
            mild_het += 1
        elif str(dir).startswith('int_het') is True:
            int_het += 1
        elif str(dir).startswith('v_int_het') is True:
            v_int_het += 1
        elif str(dir).startswith('mix_het') is True:
            mix_het += 1
    # print(f'homogen={homogen}, mild={mild_het}, int={int_het}, v_int={v_int_het}, mix={mix_het}')
    if homogen == 0 or mild_het == 0 or int_het == 0 or v_int_het == 0 or mix_het == 0:
        invalid += 1
    if invalid > 0:
        valid_pass = False
    return valid_pass


''' 
* Checks whether an outer scenario directory (i.e., one of the: 'homogen', 'mild_het', ..) contains the expected number of inner directories: i.e., four (4) inner scenarios are expected for 'homogen' or 'mix_het', 
* and seven (7) inner directories are expected for the rest. 
'''
def post_analysis_inner_scen_validation(filepath):
    invalid, inner_scenarios_tmp = 0, 0
    homogen, mix_het = 4, 4
    mild_het, int_het, v_int_het = 7, 7, 7
    files_found_msg = 'unexpected_files_found'
    valid_pass = True
    err_list = []
    for dir in os.listdir(filepath):
        full_dir_path = os.path.join(filepath, dir)
        if os.path.isfile(full_dir_path):
            err_list.append(files_found_msg)
            invalid += 1
    for dir in os.listdir(filepath):
        if os.path.isdir(dir):
            inner_scenarios_tmp += 1
    if str(filepath).startswith('homogen') is True:
        if inner_scenarios_tmp != homogen:
            invalid += 1
            err_list.append(filepath)
    elif str(filepath).startswith('mild_het') is True:
        if inner_scenarios_tmp != mild_het:
            invalid += 1
            err_list.append(filepath)
    elif str(filepath).startswith('int_het') is True:
        if inner_scenarios_tmp != int_het:
            invalid += 1
            err_list.append(filepath)
    elif str(filepath).startswith('v_int_het') is True:
        if inner_scenarios_tmp != v_int_het:
            invalid += 1
            err_list.append(filepath)
    elif str(filepath).startswith('mix_het') is True:
        if inner_scenarios_tmp != mix_het:
            invalid += 1
            err_list.append(filepath)
    if invalid > 0:
        valid_pass = False
    return valid_pass, err_list


''' 
* Checks whether the inner scenario directory (e.g. the 'e1') contains the expected fixed number of analysed files (6), and whether the size of the files is greater than zero. 
* If the size of a file is zero, it could be an issue for specific files, such as for .pcap, and manual investigation should follow. '''
def post_analysis_inner_scen_file_validation(filepath):
    target_fcount = 6
    invalid, fcount = 0, 0
    valid_pass = True
    if os.path.isdir(filepath):
        for fname in os.listdir(filepath):
            full_file_path = os.path.join(filepath, fname)
            if os.path.isfile(full_file_path) and os.path.getsize(full_file_path) > 0:
                fcount += 1
            else:
                invalid += 1    # possible issue -- prompts for subsequent manual check 
    if (target_fcount != target_fcount) or (invalid > 0):
        valid_pass = False
    return valid_pass


def validate_csv(filepath):     # Returns 'True' if validation is successful.
    invalid = 0
    valid_pass = True
    with open(filepath, "r") as f:
        lines = f.readlines()
    with open(filepath, "w") as f:
        for line in lines:
            if str(line).find('-') != -1 or str(line).find('-1') != -1:  # if this condition is True then at least one erroneous line has been found
                invalid += 1
                continue
            else:
                f.write(line)
        if invalid > 0:
            valid_pass = False
    return valid_pass


def ofo_merged_csv_validation(filepath):    # Returns 'True' if validation is successful.
    invalid = 0
    valid_pass = True
    minrtt_num = 0
    blest_num = 0
    ecf_num = 0
    rr_num = 0
    llhd_num = 0
    with open(filepath, "r") as f:
        lines = f.readlines()
        if len(lines) < 60002:  # possible issue based on mnumber of lines
            invalid += 1
        for line in lines:
            if str(line).find('minRTT') != -1:
                minrtt_num += 1
            elif str(line).find('BLEST') != -1:
                blest_num += 1
            elif str(line).find('ECF') != -1:
                ecf_num += 1
            elif str(line).find('RR') != -1:
                rr_num += 1
            elif str(line).find('LLHD') != -1:
                llhd_num += 1
        if minrtt_num == 0 or blest_num == 0 or ecf_num == 0 or rr_num == 0 or llhd_num == 0:
            invalid += 1
    if invalid > 0:
        valid_pass = False
    return valid_pass


def sched_from_prefix(prefix):
    sched_pat = str(prefix).split("_")[0]
    if sched_pat == 'default':
        sched = 'minRTT'
    elif sched_pat == 'blest':
        sched = 'BLEST'
    elif sched_pat == 'ecf':
        sched = 'ECF'
    elif sched_pat == 'rr':
        sched = 'RR'
    elif sched_pat == 'llhd':
        sched = 'LLHD'
    elif sched_pat == 'aeps':  # future use
        sched = 'AEPS'
    return sched


''' parameter values extraction: 'goodput', 'retransmissions'  '''
def append_goodput_file(dirpath, csv_full_name, prefix):
    scheduler = sched_from_prefix(prefix)
    with open(csv_full_name, 'a', encoding='utf-8') as gp:
        pcap_name = f"{prefix}.pcap"
        start_in = timer()
        caps = calculate_goodput(os.path.join(dirpath, pcap_name))
        goodput_subflow1 = "%.3f" % float(caps["cap1"]["goodput"])
        goodput_subflow2 = "%.3f" % float(caps["cap2"]["goodput"])
        # print("GP_SF1: %s, GP_SF2: %s" % (goodput_subflow1, goodput_subflow2))
        caps = calculate_retransmissions(os.path.join(dirpath, pcap_name))
        retransm_subflow1 = int(caps["cap1"]["retransmissions"])
        retransm_subflow2 = int(caps["cap2"]["retransmissions"])
        overall_retransm = retransm_subflow1 + retransm_subflow2
        end_in = timer()
        with open(os.path.join(dirpath, prefix), 'r') as f1:
            first_line = f1.readline()
            overall_gp = first_line.strip('\n').split(",")[2].lstrip()
            retransm = first_line.strip('\n').split(",")[3].rstrip().lstrip()
            bytes = first_line.strip('\n').split(",")[0].lstrip()
            duration = first_line.strip('\n').split(",")[1].lstrip()
            gp.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" %(scheduler, overall_gp, goodput_subflow1, goodput_subflow2, retransm, overall_retransm, retransm_subflow1, retransm_subflow2, bytes, duration))

        # print(f'Goodput of subflow 1: {goodput_subflow1} Mbit/s')
        # print(f'Goodput of subflow 2: {goodput_subflow2} Mbit/s')
        # end = timer()
        output = "%s\n" %(str((end_in-start_in)).strip())
        print("#--- Goodput Analysis duration for %s Bytes: %ssec\n" % (bytes, output))


''' parameter values extraction: 'srtt', 'snd_cwnd', 'ofo' '''
def append_param_file(source_file, target_file, parameter, prefix):
    if (os.path.isfile(source_file) is not True):
        print("Source file does not exist!")
        exit()

    # derive scheduler by source_file prefix
    sched = sched_from_prefix(prefix)

    with open(source_file, 'r') as f:
        with open(target_file, 'a') as pf:
            if parameter == 'srtt':
                lines = f.readlines()
                for x in lines[:-1]:
                    if '=' not in x:
                        break
                    param_val = x.split(parameter)[1].split()[0].lstrip('=')
                    pf.write("%s,%s\n" % (sched, str(float(param_val)/1000)))  # srtt unit conversion from us to ms
            elif parameter == 'snd_cwnd':
                lines = f.readlines()
                for x in lines[:-1]:
                    if '=' not in x:
                        break
                    param_val = x.split(parameter)[1].split()[0].lstrip('=')
                    pf.write("%s,%s\n" % (sched, param_val))  # snd_cwnd in # of packets
            elif parameter == 'ofo':
                lines = f.readlines()
                for x in lines[:-1]:
                    if '=' not in x:
                        break
                    param_val = x.split('=')[1].split()[0]
                    pf.write("%s,%s\n" % (sched, str(float(param_val)/1000)))  # # OFO queue size converted from Bytes to KiB


''' 
* Fetch iperf files from remote server, analyse them and create a .csv file per-parameter / per-scenario for each scheduler-cc combination. 
* i.e.: For "blest_lia" there will be a .csv file for each sub-scenario (e.g. homogen/e1_hom_bw_delay/blest_lia__WLAN_100_5ms_0.0__5G_100_5ms_0.0__goodput.csv) containing the results of the 5 iterations for that particular scenario.
'''
def iperf_analysis(schedulers, remote_path, local_path):
    start = timer()
    print("#-- ANALYSIS PART! --#\n\n")
    for sched in schedulers.keys():
        target_path = os.path.join(remote_path, sched)  # remote_path + sched + '/'
        # copy_from_remote(target_path, local_path)  # fetch directory from remote server
        sched_path = os.path.join(local_path, sched)    # local_path + sched + '/'
        for testdir in os.listdir(sched_path):
            if testdir.endswith('output') or testdir.endswith('.txt'):  # delete 'execution output' fetched directory or txt file
                del_path = os.path.join(sched_path, testdir)
                delete_directory(del_path)
                continue
            outer_scenario_path = os.path.join(sched_path, testdir)  # i.e. outer_scenario_path = 'homogen'
            for scenario in os.listdir(outer_scenario_path):  # i.e. scenario = 'e1_xyz'
                scenario_path = os.path.join(outer_scenario_path, scenario)
                # print("#--- Scenario: %s has scenario path: %s \n" % (scenario, scenario_path))
                sorted_subdir = sorted_dir_list(scenario_path)
                for subdir in sorted_subdir:  # i.e. subdir = 'r1'  -- first loop over subdirectories to gather scenario prefix
                    subdir_path = os.path.join(scenario_path, subdir)
                    # print("#--- Subdir list: %s,  current subdir: %s,  subdir_path: %s \n" % (os.listdir(scenario_path), subdir, subdir_path))
                    if os.path.isdir(subdir_path):
                        prefix = return_test_prefix(subdir_path, ".pcap")  # prefix is common among all subdirectories of same scenario - use it below
                    else:
                        continue
                sorted_subdir = sorted_dir_list(scenario_path)
                for subdir in sorted_subdir:
                    subdir_path = os.path.join(scenario_path, subdir)
                    # print("#--- No2: Subdir list: %s,  current subdir: %s,  subdir_path: %s \n" % (os.listdir(scenario_path), subdir, subdir_path))
                    if goodput_extract:  # goodput extraction
                        pattern_found = found_file_pattern(scenario_path, "goodput.csv")
                        if pattern_found is not True:
                            csv_full_path = create_csv_file(scenario_path, prefix, 'goodput')
                        append_goodput_file(subdir_path, csv_full_path, prefix)

                    if param_extract:  # parameters' extraction
                        for pat in pattern_list:  # sf1_srtt, sf2_srtt, sf1_snd_cwnd, sf2_snd_cwnd, ofo
                            pat_found = found_file_pattern(scenario_path, pat)
                            if pat_found is not True:
                                csv_full_name = create_csv_file(scenario_path, prefix, pat)
                        for param in param_list:  # srtt, snd_cwnd, ofo
                            pat_list = get_pat_from_param(param)
                            for new_pat in pat_list:
                                file_w_pat = return_file_w_pattern(subdir_path, new_pat)
                                source_file_full_path = os.path.join(subdir_path, file_w_pat)
                                target_csv_pattern = convert_file_pattern(param, new_pat)
                                target_csv_name = return_file_w_pattern(scenario_path, target_csv_pattern)
                                target_csv_full_path = os.path.join(scenario_path, target_csv_name)
                                append_param_file(source_file_full_path, target_csv_full_path, param, prefix)   # appending does not help to present CWND evolution / wrapping up per iterarion 
                                if param == 'ofo':
                                    df = pd.read_csv(target_csv_full_path)
                                    if len(df) > ofo_sample_size:
                                        df1 = df.sample(n=ofo_sample_size, ignore_index=True)
                                        # df1.to_csv(target_csv_full_path, index=False)
                                        df1.to_csv(target_csv_full_path, index=False)

                # Transfer to remote server
                create_remote_dir(sched, remote_analysis_path, sched)
                remote_sched_path = os.path.join(remote_analysis_path, sched)
                create_remote_dir(testdir, remote_sched_path, testdir)
                remote_test_dir_path = os.path.join(remote_sched_path, testdir)
                # for scenario in os.listdir(outer_scenario_path):  # i.e. scenario = 'e1_xyz'
                # print("# -----HERE - Scenario:%s,----- scenario_path:%s" % (scenario, scenario_path))
                # scenario_path = os.path.join(outer_scenario_path, scenario)
                for subdir in os.listdir(scenario_path):  # i.e. subdir = 'r1'
                    subdir_path = os.path.join(scenario_path, subdir)
                    if os.path.isdir(subdir_path):
                        delete_directory(subdir_path)
                copy_to_remote(scenario_path, remote_test_dir_path)
                delete_directory(scenario_path)
            delete_directory(outer_scenario_path)
        delete_directory(sched_path)
    end = timer()
    cumul_dur = "%s\n" %(str((end-start)).strip())
    print("Overall Analysis duration:", cumul_dur)


''' 
* Post_Analysis_check:  A variety of checks takes place: 
*   i) whether the # of outer scenarios is the expected, 
*  ii) whether the # of inner scenario directories is the expected per respective outer scenario and, 
* iii) whether the number of very inner files is as expected, as well as their size. 
'''
def post_analysis_check(schedulers, remote_path, local_path):
    print("#-- POST-ANALYSIS-CHECK PART! --#\n\n")
    outer_scen_cnt = 5
    err_full_list, err_list = ([] for i in range(2))
    for sched in schedulers.keys():
        target_path = os.path.join(remote_path, sched)  # remote_path + sched + '/'
        # copy_from_remote(target_path, local_path)  # fetch directory from remote server
        sched_path = os.path.join(local_path, sched)    # local_path + sched + '/'
        for testdir in os.listdir(sched_path):
            if testdir.endswith('output') or testdir.endswith('.txt'):  # delete 'execution output' fetched directory or txt file
                del_path = os.path.join(sched_path, testdir)
                delete_directory(del_path)
                continue
        post_analysis_outer_check = post_analysis_outer_scen_validation(sched_path)     # Outer: check for presence of 5 expected outer scenario directories
        if post_analysis_outer_check is not True:
            print(f"\nOuter_scenario_check_Failed: #-- {sched} -> Outer scenario directories don't match the number of {outer_scen_cnt} which were expected.\n")
        for testdir in os.listdir(sched_path):
            outer_scenario_path = os.path.join(sched_path, testdir)  # i.e. outer_scenario_path = 'homogen'
            post_analysis_inner_check, err_list = post_analysis_inner_scen_validation(outer_scenario_path)     # Inner: check for presence of the expected number of inner scenario directories according to outer scenario
            if post_analysis_inner_check is not True:
                print(f"\nInner_scenario_check_Failed: #- {sched} -> Inner scenario directories don't match the expected, according to respective outer scenario.\n")
            for scenario in os.listdir(outer_scenario_path):    # i.e. e1, e2, ..
                inner_scenario_path = os.path.join(outer_scenario_path, scenario)
                inner_scen_file_check = post_analysis_inner_scen_file_validation(inner_scenario_path)
                if inner_scen_file_check is not True:
                    print(f"\nInner_File_check_Failed: # {sched} -> Either missing files or FileSize is zero -- manual check needed.")
            if len(err_list) > 0:
                for i in range(len(err_list)):
                    concat = f'{sched}__{testdir}__{err_list[i]}'
                    err_full_list.append(concat)
        delete_directory(sched_path)
    if len(err_full_list) > 0:
        print(f"\nUnexpected number of inner scenario directories for the following schedulers:\n")
        for i in range(len(err_full_list)):
            print("\n\t  --> ", err_full_list[i])
    for sched in schedulers.keys():
        sched_flag = 0
        for i in range(len(err_full_list)):
            print(err_full_list[i])
            if err_full_list[i].startswith(str(sched)) is True:
                sched_flag = 1
        if sched_flag == 0:
            print(f"{sched} -> No issues detected -- good to go.\n")
    

''' 
* Merge .csv files of multiple schedulers which belong to the same sub-scenario in a common sub-scenario .csv, i.e. all results of e(x). 
* Create common per-cc and per-scenario csv's for: goodput, ofo, sf1_srtt, sf2_srtt, sf1_snd_cwnd, sf2_snd_cwnd  // CC -> keep hierarchical structure (homogen, mild, etc.) -- Scenario (1-29)  -> common csv files 
'''
def merge_csv(schedulers, remote_analysis_path, local_path):
    print("#-- MERGE PART! --#\n\n")
    mycounter = 0 # <-- assistive - can be removed!
    for sched in schedulers.keys():
        target_path = os.path.join(remote_analysis_path, sched)  # remote_path + sched + '/'
        # copy_from_remote(target_path, local_path)  # fetch directory from remote server
    for cc in cc_list:
        # create CC folder
        cc_dir_path = os.path.join(local_path, cc)
        create_dir(cc_dir_path)
        for sched in schedulers.keys():
            # print("\n#1 Scheduler=", sched)
            if str(sched).split("_")[1] == str(cc):
                sched_path = os.path.join(local_path, sched)    # local_path + sched + '/'
                for testdir in os.listdir(sched_path):  # testdir: homogen, mild, etc.
                    # print("\n   #2 Testdir=", testdir)
                    cc_testdir_path = os.path.join(cc_dir_path, testdir)
                    create_dir(cc_testdir_path)
                    outer_scenario_path = os.path.join(sched_path, testdir)  # i.e. outer_scenario_path = '../analysis/blest_lia/homogen'
                    for scenario in os.listdir(outer_scenario_path):  # i.e. scenario = 'e1_xyz'
                        # print("\n       #3 Scenario=", scenario)
                        scenario_path = os.path.join(outer_scenario_path, scenario)
                        cc_scenario_path = os.path.join(cc_testdir_path, scenario)  # e.g. scenario 'e1_xyz' within 'homogen' dir within CC dir
                        create_dir(cc_scenario_path)
                        # Create an empty csv file per parameter: 'goodput, ofo, sf1_srtt, sf2_srtt, sf1_snd_cwnd, sf2_snd_cwnd'
                        for csvf in os.listdir(scenario_path):
                            sched_name = str(sched).split("_")[0]
                            trim_sched_name = sched_name + '_'
                            csvf_new_name = str(csvf).replace(trim_sched_name, "")  # e.g.: 'balia__WLAN_100_5ms_0.0__5G_100_5ms_0.0__goodput.csv'
                            # Create all common parameter .csv files per-CC and per-parameter within CC dir and append the appropriate headers per file based on specific parameter
                            for pat in full_pattern_list:  # goodput, sf1_srtt, sf2_srtt, sf1_snd_cwnd, sf2_snd_cwnd, ofo
                                pat_found = found_file_pattern(cc_scenario_path, pat)
                                if pat_found is not True:
                                    trim_suffix = csvf_new_name.split('__')[3]
                                    trim_string = '__' + trim_suffix
                                    csvf_new_name_prefix = csvf_new_name.rstrip(trim_string)
                                    cc_csv_fname = create_csv_file(cc_scenario_path, csvf_new_name_prefix, pat)
                                else:
                                    continue
                        for csvf in os.listdir(scenario_path):
                            # print("\n           #4 csvf=", csvf)
                            sched_name = str(sched).split("_")[0]
                            trim_sched_name = sched_name + '_'
                            csvf_new_name = str(csvf).replace(trim_sched_name, "")  # e.g.: 'balia__WLAN_100_5ms_0.0__5G_100_5ms_0.0__goodput.csv'
                            csvf_path = os.path.join(scenario_path, csvf)
                            for cc_csv in os.listdir(cc_scenario_path):
                                # print("\n               #5 cc_csv=", cc_csv)
                                # print(f"\n              -->#5.1 csvf_new_name={str(csvf_new_name)}, cc_csv={str(cc_csv)}")
                                if str(csvf_new_name) == str(cc_csv):  # copy / append contents of resulting files to matching CC common file
                                    # print(f"\n #----- MATCH ------#")
                                    mycounter += 1  # <-- remove
                                    cc_csv_path = os.path.join(cc_scenario_path, cc_csv)
                                    copy_csv_file_content(csvf_path, cc_csv_path, 'a', False)
            else:
                continue
            delete_directory(sched_path)
        copy_to_remote(cc_dir_path, remote_merge_path)  # Transfer to remote server
        delete_directory(cc_dir_path)
    print(f"\n Appended {mycounter} times")  # 6 files per scenario x 29 scenarios x 5 schedulers x 4 CCs = 3,480


''' Check each merged per-cc .csv file for invalid lines. Remove such invalid entries from the files if found, and in that case, update the remote merged directory. '''
def validate_merged_csv():
    print("#-- .CSV Files' Validation Part! --#\n\n")
    total_files = 1218  # 7 CCs (lia, olia, balia, wvegas, bbr, c-mpbbr) x 29 scenarios x 6 files per scenario
    count_files = 0
    for cc in cc_list:
        err_files_list = []
        cc_remote_dir_path = os.path.join(remote_merge_path, cc)
        # copy_from_remote(cc_remote_dir_path, local_path)  # fetch cc directory (containing merged .csv files) from remote server to local analysis path
        cc_local_dir_path = os.path.join(local_path, cc)
        # if os.path.isdir(cc_local_dir_path) is not True:  # condition only for testing purposes where not all cc's are present in local dir in the order specified in cc_list
        #     continue
        for cc_testdir in os.listdir(cc_local_dir_path):  # testdir: homogen, mild, etc.
            cc_outer_scenario_path = os.path.join(cc_local_dir_path, cc_testdir)  # i.e. cc_outer_scenario_path = '../analysis/blest/homogen'
            for cc_scenario in os.listdir(cc_outer_scenario_path):  # i.e. scenario = 'e1_xyz'
                cc_scenario_path = os.path.join(cc_outer_scenario_path, cc_scenario)
                for csvf in os.listdir(cc_scenario_path):
                    count_files += 1
                    csvf_path = os.path.join(cc_scenario_path, csvf)
                    verdict = validate_csv(csvf_path)  # updates the file in-place -- removes any erroneous lines found
                    ofo_verdict = True
                    ofo_file = return_file_w_pattern(cc_scenario_path, 'ofo')  # ~~~~~~ To be updated!!! -- calls same ofo each time it fetches a new file from same dir !!! -- place before loop!
                    if str(ofo_file) == str(csvf):
                        ofo_verdict = ofo_merged_csv_validation(csvf_path)
                    if verdict is not True or ofo_verdict is not True:
                        err_files_list.append(str(csvf_path))  # keep a list of files containing invalid lines
                    else:
                        continue
        if len(err_files_list) > 0:  # at least one file from this cc contained invalid content and has been corrected // update cc content of remote path
            # copy_to_remote(cc_local_dir_path, remote_merge_path)
            print("The following files contained invalid lines:\n")
            for i in range(len(err_files_list)):
                print("\n  --> ", err_files_list[i])
        delete_directory(cc_local_dir_path)
    if count_files != total_files:
        print(f"\nCounted {count_files} files, while {total_files} were expected.")
    else:
        print(f"\nCounted {count_files} files, as expected.")



if __name__ =="__main__":
    
    local_path = "/home/mininet/mininet/mininet_dd/full_suite/analysis/"  # VM-specific
    remote_path = "/home/ubuntu/code_backup/mininet_dd/full_suite/iperf/iperf_results/"
    remote_analysis_path = "/home/ubuntu/code_backup/mininet_dd/full_suite/analysis/analysis_results/"
    remote_merge_path = "/home/ubuntu/code_backup/mininet_dd/full_suite/analysis/merge_results/"

    goodput_extract = 1
    param_extract = 1
    ofo_sample_size = 60000  # 1 sample / 500us

    full_pattern_list = ['goodput', 'sf1_srtt', 'sf2_srtt', 'sf1_snd_cwnd', 'sf2_snd_cwnd', 'ofo']
    pattern_list = ['sf1_srtt', 'sf2_srtt', 'sf1_snd_cwnd', 'sf2_snd_cwnd', 'ofo']
    param_list = ['srtt', 'snd_cwnd', 'ofo']   # 'retransmissions' is extracted within goodput .csv 
    cc_list = ['olia', 'lia', 'balia', 'wvegas', 'cubic', 'bbr', 'c-mpbbr']
    # cc_list = ['olia']  # ~~ only for experiments -- to be removed!

    analysis = 0        # PART 1: Initial Analysis
    post_analysis = 0   # PART 2: Post Analysis check
    merge = 0           # PART 3: .CSV file merge
    validate = 0        # PART 4: Merged .CSV files' validation

    # PART 1: Initial Analysis
    if analysis:
        iperf_analysis(schedulers, remote_path, local_path)

    # PART 2: Post Analysis check
    if post_analysis:
        post_analysis_check(schedulers, remote_analysis_path, local_path)
    
    # PART 3: .CSV file merge
    if merge:
        merge_csv(schedulers, remote_analysis_path, local_path)
    
    # PART 4: Merged .CSV files' validation
    if validate:
        validate_merged_csv()

