#!/usr/bin/env python3
import requests
import logging
import base64


class influxdb:
    
    def __init__(self, influxdb_ip, influxdb_port, influxdb_user, influxdb_password, influxdb_name, measure_name):
        self.influxdb_ip=influxdb_ip
        self.influxdb_port=influxdb_port
        self.influxdb_name=influxdb_name
        self.auth = base64.b64encode("{}:{}".format(influxdb_user,influxdb_password).encode()).decode('utf-8')
        self.measure_name=measure_name
        self.queue = []

    def add_measure(self, tags, name, value):
        data_string = "{}".format(self.measure_name)
        try:
            for i in tags:
                data_string = data_string + ",{}={}".format(i,tags[i])
            data_string = data_string + " {}={}".format(name,value)
            self.queue.append(data_string)
        except Exception as error:
            logging.warning('Invalid data format:', error) 


    def write_influxdb(self):
        headers = {
           'Content-Type': 'application/x-www-form-urlencode',
           'Authorization': 'Basic {}'.format(self.auth)
        }
        data='\n'.join(self.queue)
        try:
            response = requests.post('http://%s:%s/write?db=%s'%(self.influxdb_ip,self.influxdb_port,self.influxdb_name), headers=headers, data=data)
            if(response.status_code==204):
                self.queue = []
            else:
                logging.warning('Failure writing to influxdb: {}'.format(response.text))
        except Exception as error:
            logging.warning('Error posting to influxdb:', error)
