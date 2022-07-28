from bluepy.btle import Scanner, DefaultDelegate
import struct
import binascii
import logging
import time
from influxdb import influxdb
import argparse
import yaml

def read_config(configfile):
    try:
        with open(configfile, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)
            return cfg
    except Exception as error:
        print("Could not open config file.")
        return None


def prefix_mija(mac):
    return mac[:8] == "a4:c1:38"

# Gets the actual scanning data  
class ScanDelegate(DefaultDelegate):
    def __init__(self, influxdatabase):
        logging.debug("Initializing Delegate Object")
        DefaultDelegate.__init__(self)
        self.influxdatabase = influxdatabase

    def handleDiscovery(self, dev, isNewDev, isNewData):
        logging.debug(f"Discovered {dev.addr}")
        if not prefix_mija(dev.addr): return
        for (adtype, desc, value) in dev.getScanData():
          if adtype==22: # Manufacturer Data
            data = value[4:]
            #if not dev.addr in lastAdvertising or lastAdvertising[dev.addr] != data:
            self.onDeviceChanged(dev.addr, data)

    def onDeviceChanged(self, addr, data):
      logging.debug("Device %s, value %s" % (addr,data))
      data_b = binascii.a2b_hex(data)
      mac,temp,hum,bat,voltage,count = struct.unpack('>6shBBhB', data_b)
      self.influxdatabase.add_measure({'mac':addr},'temperature','{:.1f}'.format((temp/10.0)))
      self.influxdatabase.add_measure({'mac':addr},'humidity','{:.1f}'.format(hum))
      self.influxdatabase.add_measure({'mac':addr},'battery','{:.1f}'.format(bat))
      self.influxdatabase.add_measure({'mac':addr},'voltage','{:.1f}'.format(voltage))
      logging.debug(f"Device {addr} has Temp {temp/10.0}, Hum: {hum}%, Bat: {bat}%")



#scanner = Scanner().withDelegate(ScanDelegate())
#scanner.clear()
#scanner.start()
#while True: 
#    scanner.process(10)
#    #time.sleep(60)
#    #scanner.clear()
#scanner.stop()

if __name__ == "__main__":
    # Execute API requests
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", default=False, action='store_true', help="Enable Debug Logging")
    parser.add_argument('--config', type=str, default='config.yml', help='Specify the location of the config file. Defaults to config.yml.')
    args = parser.parse_args()
    if(args.debug):
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    myconfig = read_config(args.config)

    logging.basicConfig(
        filename="mija_ble_reader.log",
        format='%(asctime)s %(message)s',
        level=loglevel)


    myinfluxdb = influxdb(myconfig['influxdb']['host'],
                            myconfig['influxdb']['port'],
                            myconfig['influxdb']['user'],
                            myconfig['influxdb']['password'],
                            myconfig['influxdb']['dbname'],
                            myconfig['influxdb']['measurename'])
    
    scanDelegateInstance = ScanDelegate(myinfluxdb)

    while True:
        scanner = Scanner().withDelegate(scanDelegateInstance)
        scanner.scan()
        myinfluxdb.write_influxdb()
        time.sleep(myconfig['interval'])
