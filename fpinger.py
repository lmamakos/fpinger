#!/usr/bin/env python3.7

import argparse
import influxdb
import re
import time
import yaml
import subprocess

tstamp = 0

def parse_fping(line, db):
    global tstamp
    if re.match(r'^\[\d\d\:\d\d\:\d\d\]', line):
        tstamp = time.gmtime()
        return

    line.strip('\n')
    dat = re.match(r'(\d+\.\d+\.\d+\.\d+) +: +xmt/rcv/%loss = (\d+)/(\d+)/(\d+)%, min/avg/max = ([\d.]+)/([\d.]+)/([\d.]+)', line)
    if dat:
        (addr, transmitted, received, pctloss, min_lat, avg_lat, max_lat) = dat.groups()
    else:
        print("no match! " + line)
        return

    res = {
        "time" : time.strftime('%Y-%m-%dT%H:%M:%SZ', tstamp),
        "measurement" : "ping",
        "tags" : {
            "dest" : addr
        },
        "fields": {
            "sent" : int(transmitted),
            "recv" : int(received),
            "computed_los" : 1.0 - float(received)/float(transmitted),
            "avg" : float(avg_lat),
            "min" : float(min_lat),
            "max" : float(max_lat),
            "loss" : float(pctloss)
        }
    }
    db.write_points([res], time_precision='s')

    
def add_param(args, opt, cfg_name, default_value):
    if cfg_name in args:
        return f'--{opt}={args[cfg_name]}'
    else:
        return f'--{opt}={default_value}'
                
def run_fping(config):
    c = config['fping']
    if 'fping' in c:
        fping_args = [ c['fping'], '--loop' ]
    else:
        fping_args = [ '/usr/bin/fping', '--loop' ]

    for optdefs in [
            ('backoff','backoff', 1),
            ('squiet', 'report_interval', 30),
            ('size', 'size', 10),
            ('period', 'period', 500),
            ('interval', 'interval', 100) ]:
        fping_args.append(add_param(c, *optdefs))

    fping_args = fping_args + c['dest_hosts']
    proc = subprocess.Popen(fping_args, bufsize=1,
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            shell=False, universal_newlines=True)
    db = influxdb.InfluxDBClient(**config['influxdb'])
    for line in proc.stdout:
        parse_fping(line, db)

def main():
    parser = argparse.ArgumentParser(
        description='ping list of addresses and record perf data in influxdb')
    parser.add_argument('-c','--config', default='config.yaml',
                        help='Configuration file (default config.yaml)')

    arguments = parser.parse_args()
    with open(arguments.config) as cf:
        config = yaml.safe_load(cf)

    # db = influxdb.InfluxDBClient(**config['influxdb'])
    run_fping(config)

main()
