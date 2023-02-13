#!/usr/bin/python3
# -- coding: utf-8 --
# @Author : Long.Hou
# @Email : Long2.Hou@luxshare-ict.com
# @File : main.py
# @Project : TrackingFlex
# @Time : 2023/2/9 10:28
# -------------------------------
import csv
import json
import os
import re
import sys
import time
import uuid

import requests
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from Resource.mainPanel import MainPanel

# 电脑MAC地址
mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
mac = ":".join([mac[e:e + 2] for e in range(0, 11, 2)]).upper()


def read_json():
    if not os.path.exists('./Resource/config.json'):
        exit()
    with open('./Resource/config.json', 'r') as f:
        data = json.load(f)
    data['MesConfig']['mac_address'] = mac
    return data


def sava_json(data):
    with open('./Resource/config.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def write_csv(file_name, result_dict):
    herder = ['Station ID', 'Product', 'SerialNumber', 'Test Pass/Fail Status', 'TestTime', 'List of Failing Tests']
    if not os.path.exists(file_name):
        with open(file_name, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(herder)
    data = [config['MesConfig']['station_id'], config['MesConfig']['product']]
    for test_item in herder:
        if test_item in result_dict.keys():
            data.append(result_dict[test_item])
    with open(file_name, 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)


def get_last_content(file):
    data = {}
    with open(file, 'r') as f:
        while True:
            try:
                r_list = [next(f).strip() for _ in range(6)]
            except StopIteration:
                res = ''.join(r_list)
                break
    r = re.findall('Serial# (.*?) - (.*?)Result - (.*)', res)
    if r and len(r[0]) == 3:
        data['SerialNumber'] = r[0][0]
        data['TestTime'] = r[0][1]
        if r[0][2].split(':')[0] == 'Pass':
            data['Test Pass/Fail Status'] = "PASS"
            data['List of Failing Tests'] = ''
        else:
            data['Test Pass/Fail Status'] = "FAIL"
            data['List of Failing Tests'] = r[0][2].split(':')[1]
    return data


def update_mes(test_data, mes_config):
    data = {'result': test_data['Test Pass/Fail Status'], 'audio': 0, 'start_time': test_data['TestTime'],
            'stop_time': test_data['TestTime'], 'sn': test_data['SerialNumber'],
            'fixture_id': 0, 'test_head_id': 0,
            'list_of_failing_tests'.upper(): test_data['List of Failing Tests'], 'c': 'ADD_RECORD',
            'failure_message': test_data['List of Failing Tests'].split(', ')[0],
            'test_station_name': mes_config['test_station_name'],
            'station_id': mes_config['station_id'], 'product': mes_config['product'], 'emp_no': '',
            "type": 1, "HW001": 'OK' if not test_data['List of Failing Tests']else "NG"}
    for i in range(3):
        try:
            response = requests.post(url=mes_config['url'], data=data, timeout=3)
            if response.status_code == 200:
                if "SFC_OK" in response.text:
                    break
            time.sleep(0.1)
        except Exception as e:
            continue


def main_close_signal_slot(panel_data):
    print(panel_data)
    config['panel'] = panel_data
    sava_json(config)


def main_timer_timeout_slot():
    last_time = config["panel"]['LastTime']
    d = get_last_content(config['panel']['logFilePath'])
    if last_time != d['TestTime']:
        config["panel"]['LastTime'] = d['TestTime']
        main.update_SerialNumber_Result(d)
        write_csv(f"{config['panel']['csvPath']}/{time.strftime('%Y-%m')}.csv", d)
        if config['MesConfig']['enabled']:
            update_mes(d,config['MesConfig'])


def main_signal_connect():
    main.close_signal.connect(main_close_signal_slot)
    main.timer.timeout.connect(main_timer_timeout_slot)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    config = read_json()
    main = MainPanel(config['panel'])
    # 设置窗体置顶
    main.setWindowFlag(Qt.WindowStaysOnTopHint)
    main_signal_connect()
    main.show()
    sys.exit(app.exec_())
