#!/usr/bin/env python
""" To test guest cpu topology
    domain:cpu_topology
        guestname
            xxx
        username
            root
        password
            xxxxxx
        sockets
            2
        cores
            1
        threads
            2
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Tue Aug 30, 2011'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2011 Red Hat, Inc.'
__all__ = []

import os
import re
import sys
import time
from xml.dom import minidom

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

def check_params(params):
    """check out the arguments requried for testing"""
    logger = params['logger']
    keys = ['guestname', 'username', 'password',
            'sockets', 'cores', 'threads']
    for key in keys:
        if key not in params:
            logger.error("Argument %s is required" % key)
            return 1
    return 0

def check_domain_running(domobj, guestname, logger):
    """check if the domain exists, may or may not be active"""
    defined_guest_names = domobj.get_defined_list()

    if guestname not in defined_guest_names:
        logger.error("%s doesn't exist or still in running" % guestname)
        return 1
    else:
        return 0

def add_cpu_xml(domobj, guestname, sockets, cores, threads, logger):
    """edit domain xml description and insert <cpu> element"""

    guestxml = domobj.get_xml_desc(guestname)
    logger.debug('''original guest %s xml :\n%s''' %(guestname, guestxml))

    doc = minidom.parseString(guestxml)
    cpu = doc.createElement('cpu')
    topology = doc.createElement('topology')
    topology.setAttribute('sockets', sockets)
    topology.setAttribute('cores', cores)
    topology.setAttribute('threads', threads)
    cpu.appendChild(topology)

    vcpuval = int(sockets) * int(cores) * int(threads)
    newvcpu = doc.createElement('vcpu')
    newvcpuval = doc.createTextNode(str(vcpuval))
    newvcpu.appendChild(newvcpuval)
    oldvcpu = doc.getElementsByTagName('vcpu')[0]

    domain = doc.getElementsByTagName('domain')[0]
    domain.appendChild(cpu)
    domain.replaceChild(newvcpu, oldvcpu)

    return doc.toxml()

def guest_undefine(domobj, guestname, logger):
    """undefine original guest"""
    try:
        logger.info("undefine guest")
        domobj.undefine(guestname)
        logger.info("undefine the domain is successful")
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to undefine domain")
        return 1

    return 0

def guest_define(domobj, domxml, logger):
    """define new guest xml"""
    try:
        logger.info("define guest")
        domobj.define(domxml)
        logger.info("success to define new domain xml description")
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to define domain")
        return 1

    return 0

def guest_start(domobj, guestname, util, logger):
    """start guest"""
    timeout = 600
    ip = ''
    mac = util.get_dom_mac_addr(guestname)

    try:
        logger.info("start guest")
        domobj.start(guestname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to start domain")
        return 1

    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = util.mac_to_ip(mac, 180)

        if not ip:
            logger.info(str(timeout) + "s left")
        else:
            logger.info("vm %s power on successfully" % guestname)
            logger.info("the ip address of vm %s is %s" % (guestname, ip))
            break

    if timeout <= 0:
        logger.info("fail to power on vm %s" % guestname)
        return 1, ip

    return 0, ip

def cpu_topology_check(ip, username, password,
                       sockets, cores, threads, util, logger):
    """login the guest, run lscpu command to check the result"""
    lscpu = "lscpu"
    # sleep for 5 seconds
    time.sleep(40)
    ret, output = util.remote_exec_pexpect(ip, username, password, lscpu)
    logger.debug("lscpu:")
    logger.debug(output)
    if ret:
        logger.error("failed to run lscpu on guest OS")
        return 1

    int = 0
    actual_thread = actual_core = actual_socket = ''

    for item in output.strip().split('\r'):
        if int == 5:
            actual_thread = item.split()[-1]
            logger.info("the actual thread in the guest is %s" % actual_thread)
        if int == 6:
            actual_core = item.split()[-1]
            logger.info("the actual core in the guest is %s" % actual_core)
        if int == 7:
            actual_socket = item.split()[-1]
            logger.info("the actual socket in the guest is %s" % actual_socket)

        int += 1

    if actual_thread == '' or actual_core == '' or actual_socket == '':
       logger.error("No data was retrieved")
       return 1

    if actual_thread == threads and actual_core == cores and actual_socket == sockets:
       return 0
    else:
       logger.error("The data doesn't match!!!")
       return 1

def cpu_topology(params):
    """ edit domain xml description according to the values
        and login to the guest to check the results
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    guestname = params['guestname']
    username = params['username']
    password = params['password']
    sockets = params['sockets']
    cores = params['cores']
    threads = params['threads']

    logger.info("guestname is %s" % guestname)
    logger.info("sockets is %s" % sockets)
    logger.info("cores is %s" % cores)
    logger.info("threads is %s" % threads)

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    logger.info("the uri is %s" % uri)
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)

    if check_domain_running(domobj, guestname, logger):
        conn.close()
        return 1

    domxml = add_cpu_xml(domobj, guestname, sockets, cores, threads, logger)

    if guest_undefine(domobj, guestname, logger):
        conn.close()
        return 1

    if guest_define(domobj, domxml, logger):
        conn.close()
        return 1

    ret, ip = guest_start(domobj, guestname, util, logger)
    if ret:
        conn.close()
        return 1

    if cpu_topology_check(ip, username, password,
                          sockets, cores, threads, util, logger):
       conn.close()
       return 1

    conn.close()
    return 0
