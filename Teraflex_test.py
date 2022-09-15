import requests
from FSP3000C_Teraflex import RestAPI

Api_Client = RestAPI()
Api_Client.login()

try:
    a = Api_Client.GetPMDataCurrent(1,1,1)
except:
    Api_Client.logout()
    raise Exception

try:
    b = Api_Client.GetQFactor(1,1,1)
except:
    Api_Client.logout()
    raise Exception

try:
    c = Api_Client.GetCarrierFrequencyOffset(1,1,1)
except:
    Api_Client.logout()
    raise Exception

Api_Client.logout()


