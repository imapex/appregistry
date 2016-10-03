import json
import requests


class Controller(object):
    """
    an APIC-EM controller
    """

    def __init__(self, url, username, password, ssl_verify=False):
        if url.endswith('/'):
            url = url[:-1]
        self.base_url = url + '/api/v1'
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify
        self.headers = {"content-type": "application/json"}
        self._ticket = None

    def _get_service_ticket(self):
        payload = {"username": self.username,
                   "password": self.password}
        url = self.base_url + "/ticket"
        headers = {"content-type": "application/json"}
        response = requests.post(url,
                                 data=json.dumps(payload),
                                 headers=headers,
                                 verify=self.ssl_verify)
        print url
        print response.text
        # Check if a response was received. If not, print an error message.
        if (not response):
            print ("No data returned!")
        else:
            r_json = response.json()

            ticket = r_json["response"]["serviceTicket"]
        return ticket

    def login(self):
        if not self._ticket:
            self._ticket = self._get_service_ticket()

    def get(self, url):
        if not self._ticket:
            self._ticket = self._get_service_ticket()
        header = {"X-Auth-Token": self._ticket,
                  "content-type": "application/json"
                  }
        url = self.base_url + url
        r = requests.get(url, headers=header, verify=False)
        return r.json()

    def post(self, url, data):
        if not self._ticket:
            self._ticket = self._get_service_ticket()
        header = {"X-Auth-Token": self._ticket,
                  "content-type": "application/json"}
        url = self.base_url + url
        print url, data
        r = requests.post(url,
                          headers=header,
                          data=json.dumps(data),
                          verify=self.ssl_verify
                          )
        return r.json()
