# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <fred@dushin.net> wrote this file.  You are hereby granted permission to
# copy, modify, or mutilate this file without restriction.  If you create a
# work derived from this file, you may optionally include a copy of this notice,
# for which I would be most grateful, but you are not required to do so.
# If we meet some day, and you think this stuff is worth it, you can buy me a
# beer in return.   Fred Dushin
# ----------------------------------------------------------------------------

import machine
import ubinascii
import sys
import gc
import os
import esp
import uhttpd
import network
import logging


class APIHandler:
    def __init__(self):
        self._handlers = {
            'system': SystemAPIHandler(),
            'memory': MemoryAPIHandler(),
            'flash': FlashAPIHandler(),
            'network': NetworkAPIHandler()
        }

    def get(self, res_path, query_params):
        context = api_request['context']
        print(context)
        if len(context) == 0 or (len(context) == 1 and context[0] == ''):
            api_request['context'] = []
            return {
                'system': self._handlers['system'].get(api_request),
                'memory': self._handlers['memory'].get(api_request),
                'flash': self._handlers['flash'].get(api_request),
                'network': self._handlers['network'].get(api_request),
            }



class SystemAPIHandler:
    def __init__(self):
        pass

    #
    # callbacks
    #

    def get(self, api_request):
        return self.get_sys_stats()

    #
    # read operations
    #

    def get_sys_stats(self):
        return {
            'machine_id': "0x{}".format(ubinascii.hexlify(machine.unique_id()).decode().upper()),
            'machine_freq': machine.freq(),
            'byteorder': sys.byteorder,
            'system': "{}-{}".format(
                sys.implementation[0],
                self.to_version_string(sys.implementation[1]),
            ),
            'maxsize': sys.maxsize,
            'modules': self.keys(sys.modules),
            'path': sys.path,
            'platform': sys.platform,
            'version': sys.version,
        }

    def keys(self, pairs):
        ret = []
        for k, v in pairs.items():
            ret.append(k)
        return ret

    def to_version_string(self, version):
        return "{}.{}.{}".format(
            version[0], version[1], version[2]
        )


class MemoryAPIHandler:
    def __init__(self):
        pass

    #
    # callbacks
    #

    def get(self, api_request):
        return self.get_memory_stats()

    #
    # read operations
    #

    def get_memory_stats(self):
        mem_alloc = gc.mem_alloc()
        mem_free = gc.mem_free()
        return {
            'mem_alloc': mem_alloc,
            'mem_free': mem_free
        }


class FlashAPIHandler:
    def __init__(self):
        pass

    #
    # callbacks
    #

    def get(self, api_request):
        return self.get_flash_stats()

    #
    # read operations
    #

    def get_flash_stats(self):
        stats = os.statvfs('/')
        frsize = stats[1]
        blocks = stats[2]
        bavail = stats[4]
        capacity = blocks * frsize
        free = bavail * frsize
        used = capacity - free
        return {
            'flash_id': esp.flash_id(),
            'flash_size': esp.flash_size(),
            'capacity': capacity,
            'used': used,
            'free': free
        }


class NetworkAPIHandler:
    def __init__(self):
        pass

    #
    # callbacks
    #

    def get(self, api_request):
        logging.info("get {}".format(api_request))
        context = api_request['context']
        return self.get_network_stats(context)

    def post(self, api_request):
        logging.info("post {}".format(api_request))
        return self.save(api_request)

    def put(self, api_request):
        logging.info("put {}".format(api_request))
        return self.save(api_request)

    #
    # read operations
    #

    def get_network_stats(self, context):
        ret = {
            'phy_mode': self.get_phy_mode(),
            'sta': self.get_sta_stats(),
            'ap': self.get_ap_stats()
        }
        for component in context:
            if component in ret:
                ret = ret[component]
            else:
                raise uhttpd.NotFoundException("Bad context: {}".format(context))
        return ret

    def get_sta_stats(self):
        sta = network.WLAN(network.STA_IF)
        return self.get_wlan_stats(sta)

    def get_ap_stats(self):
        ap = network.WLAN(network.AP_IF)
        wlan_stats = self.get_wlan_stats(ap)
        wlan_stats['config'] = self.get_wlan_config_stats(ap)
        return wlan_stats

    def get_wlan_stats(self, wlan):
        if wlan.active():
            ip, subnet, gateway, dns = wlan.ifconfig()
            return {
                'status': self.get_wlan_status(wlan),
                'ifconfig': {
                    'ip': ip,
                    'subnet': subnet,
                    'gateway': gateway,
                    'dns': dns
                }
            }
        else:
            return {}

    def get_wlan_config_stats(self, ap):
        import ubinascii
        return {
            'mac': "0x{}".format(ubinascii.hexlify(ap.config('mac')).decode()),
            'essid': ap.config('essid'),
            'channel': ap.config('channel'),
            'hidden': ap.config('hidden'),
            'authmode': self.get_auth_mode(ap.config('authmode'))
        }

    def get_auth_mode(self, mode):
        if mode == network.AUTH_OPEN:
            return "AUTH_OPEN"
        elif mode == network.AUTH_WEP:
            return "AUTH_WEP"
        elif mode == network.AUTH_WPA_PSK:
            return "AUTH_WPA_PSK"
        elif mode == network.AUTH_WPA2_PSK:
            return "AUTH_WPA2_PSK"
        elif mode == network.AUTH_WPA_WPA2_PSK:
            return "AUTH_WPA_WPA2_PSK"
        else:
            return "Unknown auth_mode: {}".format(mode)

    def get_wlan_status(self, wlan):
        status = wlan.status()
        if status == network.STAT_IDLE:
            return 'STAT_IDLE'
        elif status == network.STAT_CONNECTING:
            return 'STAT_CONNECTING'
        elif status == network.STAT_WRONG_PASSWORD:
            return 'STAT_WRONG_PASSWORD'
        elif status == network.STAT_NO_AP_FOUND:
            return 'STAT_NO_AP_FOUND'
        elif status == network.STAT_CONNECT_FAIL:
            return 'STAT_CONNECT_FAIL'
        elif status == network.STAT_GOT_IP:
            return 'STAT_GOT_IP'
        else:
            return "Unknown wlan status: {}".format(status)

    def get_phy_mode(self):
        phy_mode = network.phy_mode()
        if phy_mode == network.MODE_11B:
            return 'MODE_11B'
        elif phy_mode == network.MODE_11G:
            return 'MODE_11G'
        elif phy_mode == network.MODE_11N:
            return 'MODE_11N'
        else:
            return "Unknown phy_mode: {}".format(phy_mode)

    #
    # save operations
    #

    def save(self, api_request):
        context = api_request['context']
        logging.info("context: {}".format(context))
        if context == ['ap', 'config']:
            return self.save_ap_config(api_request)
        else:
            raise uhttpd.BadRequestException("Unsupported context on save: {}", context)

    def save_ap_config(self, api_request):
        config = api_request['body']
        ap = network.WLAN(network.AP_IF)
        logging.info("config: {}".format(config))
        ap.config(
            #mac=config['mac'],
            essid=config['essid'],
            channel=config['channel'],
            hidden=config['hidden']
        )
        return self.get_wlan_config_stats(ap)
