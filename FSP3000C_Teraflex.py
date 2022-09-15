import logging
import requests
from urllib3.exceptions import InsecureRequestWarning
import json
import numpy as np

HTTP_METHOD = "https"
AOS_API_VERSION = "1.0"
HTTP_GET = "GET"
HTTP_POST = "POST"
HTTP_PUT = "PUT"
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class CloudConnectAPIError(Exception):
    """Base error"""
    pass


class HTTPError(CloudConnectAPIError):
    """Generic error raised from CloudConnect API. """
    _errorcodes = {
        400: 'A request body cannot be properly parsed by the server.',
        401: 'Authentication credentials are invalid.',
        403: 'Client\'s user is unauthorized to access the requested resource or an RBAC violation.',
        404: 'Invalid URI.',
        405: 'HTTP verb not supported.',
        406: 'Invalid Accept header is specified for a method which takes an Accept header.',
        409: 'Duplicate Name Exception.',
        415: 'Invalid client specified by client for a media type while a URI specified by the client exists.',
        500: 'Internal server error.',
        503: 'Service unavailable.'
    }

    def __init__(self, msg, code=None):
        CloudConnectAPIError.__init__(self, msg)
        self.msg = msg
        self.code = code
        print('----------------')
        if code:
            print("Reason : %s"%self._errorcodes[code])
        print('----------------')


class RestAPI(object):
    USER_AGENT = "CloudConnect API Client"

    def __init__(self, username='admin', password='hpnNUC99!', server='https://10.68.100.204', logger=logging):
        self._username = username
        self._password = password
        self._server = server
        self._token = None
        self._logger = logger
        # self.login()

    def getServer(self):
        return self._server

    def setServer(self, server):
        self._server = HTTP_METHOD + '://' + server

    def _modifyHeaders(self, headers):
        if self._token is not None:
            headers['X-Auth-Token'] = self._token

        headers['AOS-API-Version'] = "%s"%AOS_API_VERSION
        headers['User-Agent'] = self.USER_AGENT
        return headers

    def _get(self, data):
        return self._SendRequest('GET', data['path'], self._token, None, None, self._modifyHeaders(data['headers']))

    def _patch(self, data):
        return self._SendRequest('PATCH', data['path'], self._token, None, data['body'],
                                 self._modifyHeaders(data['headers']))

    def _post(self, data):
        return self._SendRequest('POST', data['path'], self._token, None, data['body'],
                                 self._modifyHeaders(data['headers']))

    def _delete(self):
        pass

    def _Send(self, method, path, query, content, headers):
        pass

    def _SendRequest(self, method, path, token, query, content, headers):
        url = "%s/%s"%(self._server, path)  # chek if self._server is None
        params = query
        data = content
        print('\n -------- DEBUG INFO ---------\n')
        print('Method is %s \n'%method)
        print('URL is %s\n'%url)
        print('Params are %s\n'%params)
        print("HEADERS are %s\n"%headers)
        print('Token is %s\n'%token)
        print('data are %s\n'%data)
        print('\n -------- DEBUG INFO ---------\n')
        try:
            req = requests.request('%s'%method, url, params=params, headers=headers, auth=None, data=data, verify=False,
                                   timeout=120)  # ToDo set timeout parameter
            http_code = req.status_code
            req.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.logout()
            print('e is %s\n'%e)
            print('req.status_code is %s\n'%req.status_code)
            raise HTTPError(e, req.status_code)
        except (requests.exceptions.Timeout,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.RequestException) as e:
            self.logout()
            raise HTTPError(e)

        print("Returned HTTP code %d\n"%http_code)

        response = req.raw.read()
        response = req.text
        print(response)
        response_content = json.loads(response)
        try:
            response_content = req.json()
        except requests.exceptions.HTTPError as e:
            self.logout()
            raise CloudConnectAPIError(e)
        # Have to do some error handling here....
        if self._token is None:
            self._token = req.headers['X-Auth-Token']
        return response_content

    def login(self):
        """The login operation is used to authenticate a client to the REST
        API, begin a session and return a security token to the client.
        """
        token = None
        data = {}
        data['path'] = 'auth?actn=lgin'
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Content-Type': 'application/json;ext=nn'}
        req = {
            "in": {
                "un": self._username,
                "pswd": self._password
            }
        }
        data['body'] = json.dumps(req)
        return self._post(data)

    def logout(self):
        """The logout operation is used to terminate the current
        REST API session. At this point the security token can no
        longer be used to access the system."""
        data = {}
        data['path'] = 'auth?actn=lgout'
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Content-Type': 'application/json;ext=nn'}
        req = None
        data['body'] = json.dumps(req)
        req = requests.request('POST', "%s/%s"%(self._server, data['path']), params=None,
                               headers=self._modifyHeaders(data['headers']), auth=None,
                               data=data['body'], verify=False, timeout=120)
        http_code = req.status_code
        print("Returned HTTP code %d\n"%http_code)

    def keepalive(self):
        """The keepalive operation is used to reset the
        session inactivity timer."""
        data = {}
        data['path'] = 'auth?actn=ka'
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Content-Type': 'application/json;ext=nn'}
        req = None
        data['body'] = json.dumps(req)
        req = requests.request('POST', "%s/%s"%(self._server, data['path']), params=None,
                               headers=self._modifyHeaders(data['headers']), auth=None,
                               data=data['body'], verify=False, timeout=120)
        http_code = req.status_code
        print("Returned HTTP code %d\n"%http_code)

    def GetSlotInventory(self):
        """Retreives inventory information from all slots of shelf 1"""
        data = {}
        data['path'] = 'col/eqh?filter={"sl":{"$exists":true},"$ancestorsIn":["/mit/me/1/eqh/sh,1"]}'
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetConfignStatus(self, shelf, slot):
        """Retrieves configuration and status information for an MP-2B4CT"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card'%(shelf, slot)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetSubnetworkConnections(self, shelf, slot):
        """Retrieves Subnetwork connections are cross connections"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/sn/odu4/snc'%(shelf, slot)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetAlarmSummary(self):
        """Retrieves a summary of all alarms on the node/shelf."""
        data = {}
        data['path'] = 'mit/me/1/almsum'
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetAllSystemAlarms(self):
        """Retrieves all active alarms on the node"""
        data = {}
        data['path'] = 'mit/me/1/alm'
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetModulePMData(self, shelf):
        """Retrieves module PM data"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,cem/eq/card/pm/crnt'%(shelf)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetPMDataNetworkPort(self, shelf, slot, port):
        """Retrieves  the current performance monitoring bin for a port,shelf,slot"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt/pm/crnt'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetPMDataClientNetworkPort(self, shelf, slot, port):
        """Retrieves  the current performance monitoring bin for a port,shelf,slot"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/cl,%d/ctp/et100/ety6/pm/crnt'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def AddSubnetworkConnection(self, entname, shelf, slot):
        """Provisions the client and network ports"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/sn/odu4/snc/%d'%(shelf, slot, entname)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        req = {"entname": str(entname),
               "aendlist": ["/mit/me/1/eqh/shelf," + str(shelf) + "/eqh/slot," +
                            str(slot) + "/eq/card/ptp/cl," + str(entname) +
                            "/ctp/et100/ctp/odu4"],
               "zendlist": ["/mit/me/1/eqh/shelf," + str(shelf) + "/eqh/slot," +
                            str(slot) + "/eq/card/ptp/nw,2/ctp/ot400/ctp/odu4-2"]
               }
        data['body'] = json.dumps(req)
        return self._post(data)

    def GetPMData(self, shelf, slot, port):
        """Retrieves  the current performance monitoring bin for a port,shelf,slot"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt/pm/crnt'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def SetMaxOutputPower(self, shelf, slot, port, power):
        """Sets Maximum Output Power"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/otsomsso'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'X-Auth-Token': '2|1:0|10:1462386840|12:',
                           'Connection': 'keep-alive',
                           'Content-Length': '59',
                           'Content-Type': 'application/json-patch+json;ext=nn',
                           'User-Agent': 'python-requests/2.9.1'}
        req = [{"op": "replace",
                "path": "/aspctl/maxppc",
                "value": power}]
        data['body'] = json.dumps(req)
        return self._patch(data)

    def SetToMaintenance(self, shelf, slot, port):
        """Set the network port admin is-substate to maintenance."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/sm'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json-patch+json;ext=nn'}
        req = [{"op": "add",
                "path": "/isst",
                "value": ["mt"]}]
        data['body'] = json.dumps(req)
        return self._patch(data)

    def SetReverseMaintenance(self, shelf, slot, port):
        """Set the network port admin is-substate from maintenance."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/sm'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Connection': 'keep-alive',
                           'Content-Type': 'application/json-patch+json;ext=nn'}
        req = [{"op": "replace",
                "path": "/isst",
                "value": []}]
        data['body'] = json.dumps(req)
        return self._patch(data)

    def SetPower(self, shelf, slot, port, power):
        """Set the operating power level of the network port."""
        power = power*10
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json-patch+json; ext=nn'}
        req = [{"op": "replace",
                "path": "/optset",
                "value": power}]
        data['body'] = json.dumps(req)
        return self._patch(data)

    def SetFrequency(self, shelf, slot, port, freq):
        """Set the frequency of the network port."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json-patch+json; ext=nn'}
        req = [{"op": "replace",
                "path": "/freq",
                "value": freq}]
        data['body'] = json.dumps(req)
        return self._patch(data)

    def SetModulation(self, shelf, slot, port, mod, bpsym=None):
        """Set the modulation scheme of the network port."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/ochcfg'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json-patch+json; ext=nn'}
        if bpsym is None:
            req = [{"op": "replace", "path": "/mod", "value": mod}]
        else:
            req = [{"op": "replace", "path": "/mod", "value": mod},
                   {"op": "replace", "path": "/bitpsym", "value": bpsym}]

        data['body'] = json.dumps(req)
        return self._patch(data)

    def GetPMDataCurrent(self, shelf, slot, port):
        """Retrieves  the current performance monitoring bin for a port,shelf,slot"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/pm/crnt'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json;ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json;ext=nn'}
        return self._get(data)

    def GetModulation(self, shelf, slot, port):
        """Retrieve the modulation information."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/ochcfg'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        return self._get(data)

    def GetOpt(self, shelf, slot, port):
        """Retrieve the current PM Data for T-MP-2D12CT Port PTP"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt/pm/crnt'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        return self._get(data)

    def GetSNR(self, shelf, slot, port):
        """Retrieve the SNR/OSNR performance data."""
        check = self.GetModulation(shelf, slot, port)
        mod = check['mod']
        mod_dict = {}
        mod_dict['16qam'] = '16Q'
        mod_dict['32qam'] = '32Q'
        mod_dict['64qam'] = '64Q'
        mod_dict['32n64qam'] = '32h64Q'
        mod_dict['16n32qam'] = '16h32Q'
        data = {}
        data[
            'path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/pm/crnt/nint,QualityTF400g%s'%(
        shelf, slot, port, mod_dict[mod])
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        return self._get(data)

    def GetFEC(self, shelf, slot, port):
        """Retrieve the BER performance data for FEC"""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otuc4pa/pm/crnt/nint,FEC'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        return self._get(data)

    def ConfigurePower(self, shelf, slot, port, power):
        """Configure the operating power"""
        self.SetToMaintenance(shelf, slot, port)
        self.SetPower(shelf, slot, port, power)
        self.SetReverseMaintenance(shelf, slot, port)

    def ConfigureFrequency(self, shelf, slot, port, freq):
        """Configure the operating frequency"""
        self.SetToMaintenance(shelf, slot, port)
        self.SetFrequency(shelf, slot, port, freq)
        self.SetReverseMaintenance(shelf, slot, port)

    def ConfigureModulation(self, shelf, slot, port, mod, bpsym=None):
        """Configure the modulation scheme"""
        self.SetToMaintenance(shelf, slot, port)
        self.SetModulation(shelf, slot, port, mod, bpsym)
        self.SetReverseMaintenance(shelf, slot, port)

    def GetAverageBER(self, shelf, slot, port):
        BERs = np.zeros(5)
        for i in range(0, 4):
            BER = self.GetFEC(shelf, slot, port)["pmdata"]["fecber"]
            if BER == '':
                BER = 0
            BERs[i] = BER
        BER_avg = BERs.mean()
        return BER_avg

    def GetModScheme(self, shelf, slot, port):
        """Retrieve the modulation information."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/ochcfg'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        Modulation_Inf = self._get(data)
        Modulation_Scheme = Modulation_Inf['mod']
        return Modulation_Scheme

    def GetFrequency(self, shelf, slot, port):
        """Set the frequency of the network port."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        opt = self._get(data)
        freq = opt["freq"]
        return freq

    def GetTxPower(self, shelf, slot, port):
        """Set the transmit power of the network port."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt/pm/crnt/nint,IFTFnw'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        Power_Tx = self._get(data)["pmdata"]["opt"]
        return Power_Tx

    def GetRxPower(self, shelf, slot, port):
        """Set the receive power of the network port."""
        data = {}
        data['path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/opt/pm/crnt/nint,IFTFnw'%(shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        Power_Rx = self._get(data)["pmdata"]["opr"]
        return Power_Rx

    def GetSNRval(self, shelf, slot, port):
        """Retrieve the SNR performance data."""
        pmdata = self.GetSNR(shelf, slot, port)['pmdata']
        SNR = pmdata['snr']
        return SNR

    def GetOSNRval(self, shelf, slot, port):
        """Retrieve the SNR performance data."""
        pmdata = self.GetSNR(shelf, slot, port)['pmdata']
        OSNR = pmdata['osnr']
        return OSNR

    def GetQFactor(self, shelf, slot, port):
        """Set the Q-factor of the channel."""
        data = {}
        data[
            'path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/pm/crnt/nint,QualityTF'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        pmdata = self._get(data)['pmdata']
        QFactor = pmdata['qfact']
        return QFactor

    def GetCarrierFrequencyOffset(self, shelf, slot, port):
        """Set the carrier frequency of the channel."""
        data = {}
        data[
            'path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/pm/crnt/nint,QualityTF'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        pmdata = self._get(data)['pmdata']
        cfot = pmdata['cfot']
        return cfot

    def GetPolarizationDependentLoss(self, shelf, slot, port):
        """Set the polarization dependent loss of the channel."""
        data = {}
        data[
            'path'] = 'mit/me/1/eqh/shelf,%d/eqh/slot,%d/eq/card/ptp/nw,%d/ctp/ot400/otsia/otsi/1/pm/crnt/nint,QualityTF'%(
        shelf, slot, port)
        data['headers'] = {'Accept': 'application/json; ext=nn',
                           'Accept-Encoding': 'gzip',
                           'Content-Type': 'application/json; ext=nn'}
        pmdata = self._get(data)['pmdata']
        pdl = pmdata['pdl']
        return pdl
