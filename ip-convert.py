#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
from netaddr import *
import sys

line_re = re.compile(r"[^0-9\./]")


def file2ipset(filename):
    """
    :param filename: 文件名
    :return: ip集合
    """
    file_ipset = set()
    with open(filename) as f:
        for line in f.readlines():
            file_ipset = file_ipset.union(line2ipset(line))
    return set([str(ip) for ip in file_ipset if str(ip) != 'None'])


def line2ipset(ipline):
    """
    :param ipline: 一行字符串，代表一些ip
    :return: ip集合
    """
    line = ipline.strip()
    ipset = set()
    # 1.1.1.1/24
    if len(line.split("/")) == 2:
        ip_network = IPNetwork(line)
        for ip in ip_network.ipv4().iter_hosts():
            ipset.add(ip)
        ipset.add(str(IPNetwork(line.strip()).network))
        ipset.add(str(IPNetwork(line.strip()).broadcast))
        return ipset
    line_array = line_re.split(line)
    if len(line_array) == 2:
        # 222.30.32.10-222.30.32.11
        if len(line_array[1]) > 3:
            for ip in IPRange(line_array[0], line_array[1]):
                ipset.add(ip)
            return ipset
        # 222.30.32.10~12
        else:
            end_ip_array = line_array[0].split(".")
            end_ip = end_ip_array[0] + "." + end_ip_array[1] + "." + end_ip_array[2] + "." + line_array[1]
            for ip in IPRange(line_array[0], end_ip):
                ipset.add(ip)
            return ipset
    # 222.30.32.10
    if len(line_array) == 1:
        ipset.add(line_array[0])
        return ipset
    print "parser line ", line, "error"
    return ipset


def ipset2cidr(ipset):
    """
    把ip集合转换成cidr格式，返回多个cidr组成的集合
    :param ipset: ip集合
    :return: 单个ip cidr组成的集合
    """
    ip_list = [IPNetwork(str(ip)) for ip in ipset]
    return [str(ip) for ip in cidr_merge(ip_list)]


def ipset2iprange(ipset):
    ip_network_list = sorted([IPNetwork(str(ip)) for ip in ipset])
    ip_list = [str(ip)[:-3] for ip in ip_network_list]
    # print ip_list
    result = []
    sub_net = ""
    last_list = set()
    for ip_item in ip_list:
        ip_split = ip_item.split(".")
        ip_prefix = ip_split[0] + "." + ip_split[1] + "." + ip_split[2]
        if sub_net != ip_prefix:
            if len(last_list) > 0:
                i = 0
                # if sub_net=="14.17.101":
                #    print last_list
                last_range = list2range(last_list)
                while i < len(last_range):
                    if last_range[i] == last_range[i + 1]:
                        result.append(sub_net + "." + str(last_range[i]))
                    else:
                        result.append(sub_net + "." + str(last_range[i]) + "," + sub_net + "." + str(last_range[i + 1]))
                    i = i + 2
            else:
                pass
            last_list = set()

        sub_net = ip_prefix
        last_list.add(ip_split[3])

    if len(last_list) > 0:
        i = 0
        last_range = list2range(last_list)
        while i < len(last_range):
            if last_range[i] == last_range[i + 1]:
                result.append(sub_net + "." + str(last_range[i]))
            else:
                result.append(sub_net + "." + str(last_range[i]) + "," + sub_net + "." + str(last_range[i + 1]))
            i = i + 2
    return result


def list2range(num_lis):
    num_list = [int(i) for i in num_lis]
    num_list.sort()
    if len(num_list) == 0:
        return []
    num_range = []
    num_current = num_list[0]
    num_range.append(num_list[0])
    for i in range(1, len(num_list)):
        num_current += 1
        if num_list[i] != num_current:
            num_range.append(num_list[i - 1])
            num_range.append(num_list[i])
            num_current = num_list[i]
    num_range.append(num_list[-1])
    return num_range


def ipset2file(filename, ipset):
    print "before ipset2file:", filename, len(ipset)
    with open(filename, "w") as f:
        for line in ipset2iprange(ipset):
            f.write(line + "\n")
    print "after ipset2file:", filename, len(file2ipset(filename))


if __name__ == "__main__":
    """
    file2ipset:文件转换成ip集合
    然后可以直接 - ，union等操作
    可以计算长度

    ipset2iprange：转换成1.1.1.1,1.1.1.6这种格式，代表从1.1.1.1到1.1.1.6，不会超过一个C段
    ipset2cidr：转换成cidr格式

    格式转换之后可以用file2ipset对比转换之前的集合大小，防止出错

    ip1229=file2ipset("./1229/55555.txt")
    ip1214=file2ipset("./20171214/55555_12.txt")
    print len(ip1229-ip1214)
    print len(ip1214-ip1229)

    sys.exit(0)
    """
