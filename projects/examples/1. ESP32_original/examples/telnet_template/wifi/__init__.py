import machine, network, utime
import json
import uasyncio as asyncio

class WifiManager:

    def __init__(self, debug=True):
        self.debug = debug
        self.status = False
        self.status_ap = False

    def dprint(self, str,arg):
        if self.debug:
            print('{} - {}'.format(str, arg))

    @classmethod
    def accesspoint(self):
        return network.WLAN(network.AP_IF)

    @classmethod
    def wlan(self):
        return network.WLAN(network.STA_IF)


    def get_config(self, config_file='/networks.json', type="sta"):

        try:
            with open(config_file, "r") as f:
                config = json.loads(f.read())

                if type == "sta":
                    return config["known_networks"]
                if type == "ap":
                    return config["access_point"]

        except:
            self.dprint("Error","Cann't loading config file")
            return False



    # async def _scan(self):
    #     scan = None
    #     try:
    #         scan = self.wlan().scan()
    #     except:
    #         pass
    #     return scan

    async def sta_start(self):

        config_sta = self.get_config(type="sta")
        self.status = False
        self.status_ap = False
        self.wlan().active(True)

        while True:

            if self.status:
                await asyncio.sleep(15)

            ip = self.wlan().ifconfig()
            await asyncio.sleep(10)

            if ip[0] is "0.0.0.0":
                for ssid, pwd in config_sta.items():
                    self.wlan().connect(ssid, pwd)
                    await asyncio.sleep(2)

                    ip = self.wlan().ifconfig()

                    if ip[0] is not "0.0.0.0":
                        break


            if ip[0] is not "0.0.0.0":
                self.status = True
                self.accesspoint().active(False)
                self.status_ap = False
            else:
                self.status = False
                self.ap_start()
                self.status_ap = True

            # scan = await self._scan()
            #
            # for ap in scan:
            #     if ap[0].decode("utf-8") in config_sta.keys():
            #         self.wlan().connect(ap[0].decode("utf-8"), config_sta[ap[0].decode("utf-8")])





    def ap_start(self):

        config_ap = self.get_config(type="ap")

        self.accesspoint().active(True)
        self.accesspoint().config(essid=config_ap["essid"])
        self.accesspoint().config(authmode=config_ap["authmode"],
                                  password=config_ap["password"],
                                  channel=config_ap["channel"])













