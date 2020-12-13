import socket
import time
from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
#import smtplib
import json
import datetime
import select

class ScraperServer:

    def __init__(self, *args, **kwargs):

        self.ip = kwargs.pop('ip', None)
        self.port = kwargs.pop('port', None)
        self.clients = []
        self.db = None
        self.browser = None
        self.actions = None
        self.link = 'https://www.easyjet.com/en'

        if self.ip and self.port:
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.ip, self.port))
                #self.socket_list = [self.server_socket]
            except Exception as e:
                print('Error while setting up socket')
                print(e)
        else:
            print('Arguments missing: ip=, port=')

        self.db_init()

    def db_update(self):
        with open('dbs.json', 'w') as f:
            json.dump(self.db, f, indent=1)

    def db_init(self):
        with open('dbs.json', 'r') as f:
            self.db = json.load(f)

    def close_policy_pop(self):
        try:
            cookie_policy = self.browser.find_element_by_xpath(
                "//button[@class='ej-button rounded-corners'][@ng-click='DoAcceptCookiePolicy()']")
            cookie_policy.click()
        except:
            pass

    def choose_dest(self, dest):

        fly_to = self.browser.find_element_by_xpath("//input[@name='destination']")
        time.sleep(2)
        fly_to.clear()
        time.sleep(2.5)
        fly_to.send_keys(dest)
        first_item = self.browser.find_element_by_xpath("//li[@id='selected-autocomplete-item']")
        time.sleep(1.5)
        first_item.click()

    def choose_src(self, src):

        fly_to = self.browser.find_element_by_xpath("//input[@name='origin']")
        time.sleep(2)
        fly_to.clear()
        time.sleep(2.5)
        fly_to.send_keys(src)
        first_item = self.browser.find_element_by_xpath("//li[@id='selected-autocomplete-item']")
        time.sleep(1.5)
        first_item.click()

    def choose_dates(self, dep_date, return_date, one_w=False):

        if one_w:
            fly_out_path = "//div[@class='drawer-tab-content active'][@data-tab='Date Calendar Outbound']//div[@data-date='{}']/a[@class='selectable']".format(
            dep_date)
            one_way_path = "//div[@class='ej-checkbox one-way-checkbox']//span[@class='checkbox-container']"
            one_way = self.browser.find_element_by_xpath(one_way_path)
            #one_way = self.browser.find_element_by_id('one-way')
            #time.sleep(3)
            one_way.click()

        else:
            fly_out_path = "//div[@class='drawer-tab-content active'][@data-tab='Date Calendar Outbound']//div[@data-date='{}']/a[@class='selectable']".format(
                dep_date)
            fly_in_path = "//div[@class='drawer-tab-content active'][@data-tab='Date Calendar Return']//div[@data-date='{}']/a[@class='selectable']".format(
            return_date)
        cal = self.browser.find_element_by_xpath("//button[starts-with(@id, 'routedatepicker-')]")
        time.sleep(3)
        cal.click()
        time.sleep(5)

        try:
            fly_out = self.browser.find_element_by_xpath(fly_out_path)
            self.actions.move_to_element(fly_out).perform()

        except:
            print('Exception triggered')
            time.sleep(3)
            fly_out = self.browser.find_element_by_xpath(fly_out_path)
            self.actions.move_to_element(fly_out).perform()

        time.sleep(2)
        fly_out.click()
        if not one_w:
            time.sleep(3)
            fly_in = self.browser.find_element_by_xpath(fly_in_path)
            #self.actions.move_to_element(fly_in).perform()
            fly_in.click()

    def add_passenger(self, adult, children):

        if adult > 1:
            adult = adult - 1
            adult_elem = self.browser.find_element_by_xpath(
                "//div[@class='search-passengers-adults search-row']//button[@class='quantity-button-add']")
            for i in range(0, adult):
                adult_elem.click()
                time.sleep(1)

        if children > 0:
            child_elem = self.browser.find_element_by_xpath(
                "//div[@class='search-passengers-children search-row']//button[@class='quantity-button-add']")
            for i in range(0, children):
                child_elem.click()
                time.sleep(1)

    def retrieve_prices(self, one_way):

        submit = self.browser.find_element_by_xpath(
            "//button[@class='ej-button rounded-corners arrow-button search-submit']")
        submit.click()

        time.sleep(10)
        if len(self.browser.window_handles) > 1:
            self.browser.switch_to.window(self.browser.window_handles[1])
        if one_way:
           try:
                to = self.browser.find_element_by_xpath(
                    "//div[@class='funnel-flight outbound']//div[@class='flight-grid-day-wrapper']//span[@class='price-container']//span[@class='major']").get_attribute(
                    'textContent')
                back = None
           except:
                to = self.browser.find_element_by_xpath(
                   "//div[@class='funnel-flight outbound']//div[@class='flight-grid-day-wrapper']//span[@class='text-container greyed-out']").get_attribute(
                   'textContent')
                to = to.strip()
                back = None

        else:
            try:
                to = self.browser.find_element_by_xpath(
                    "//div[@class='funnel-flight outbound has-return']//div[@class='flight-grid-day-wrapper']//span[@class='price-container']//span[@class='major']").get_attribute(
                    'textContent')
                back = self.browser.find_element_by_xpath(
                    "//div[@class='funnel-flight return']//div[@class='flight-grid-day-wrapper']//span[@class='price-container']//span[@class='major']").get_attribute(
                    'textContent')
            except:
                to = self.browser.find_element_by_xpath(
                    "//div[@class='funnel-flight outbound has-return']//div[@class='flight-grid-day-wrapper']//span[@class='text-container greyed-out']").get_attribute(
                    'textContent')
                back = self.browser.find_element_by_xpath(
                    "//div[@class='funnel-flight return']//div[@class='flight-grid-day-wrapper']//span[@class='text-container greyed-out']").get_attribute(
                    'textContent')
                to = to.strp()
                back = back.strip()

        return [to, back]

    def get_trips_data(self, t):

        for trip in self.db:
            src = trip.get('src_city', None)
            dst = trip.get('dst_city', None)
            date_to = trip.get('to_date', None)
            date_back = trip.get('back_date', None)
            one_way = trip.get('one_way')
            adult = trip.get('adult', None)
            child = trip.get('child', None)
            #adult = trip.pop('adult', None)
            #child = trip.pop('child', None)
            self.browser = webdriver.Chrome('chromedriver.exe')  # options=chrome_options
            # browser = webdriver.Chrome(executable_path='C:/Users/kamil/OneDrive/Desktop/my scripts/chromedriver')
            self.actions = ActionChains(self.browser)

            if not one_way:
                self.browser.get(self.link)
                time.sleep(7)
                self.browser.maximize_window()
                self.close_policy_pop()
                self.choose_src(src)
                time.sleep(1)
                self.choose_dest(dst)
                time.sleep(2)
                self.choose_dates(self.reverse_date(date_to), self.reverse_date(date_back))
                time.sleep(2)
                self.add_passenger(adult, child)
                time.sleep(2)
                to, back = self.retrieve_prices(False)
                self.browser.quit()
                dt = self.reverse_date(str(datetime.datetime.now()).split(' ')[0])[:-2]
                if to == 'Sold Out' or back == 'Sold Out':
                    if to == 'Sold Out':
                        trip['sold_out'] += 'sold'
                    if back == 'Sold Out':
                        trip['sold_out'] += 'sold'
                else:
                    trip['trip_data']['to'][dt + ' ' + t] = int(to)
                    trip['trip_data']['back'][dt + ' ' + t] = int(back)
            else:
                self.browser.get(self.link)
                time.sleep(7)
                self.browser.maximize_window()
                self.close_policy_pop()
                self.choose_src(src)
                time.sleep(1)
                self.choose_dest(dst)
                time.sleep(2)
                self.choose_dates(self.reverse_date(date_to), date_back, True)
                time.sleep(2)
                self.add_passenger(adult, child)
                time.sleep(2)
                to, back = self.retrieve_prices(True)
                self.browser.quit()
                dt = str(datetime.datetime.now()).split(' ')[0]

                if to == 'Sold Out':
                    trip['sold_out'] += 'sold'
                else:
                    trip['trip_data']['to'][dt + ' ' + t] = int(to)

        self.db_update()

    def send_data(self, sock):
        sock.sendall(json.dumps(self.db).encode())

    @staticmethod
    def reverse_date(date):
        rev_date = []
        parts = date.split('-')
        rev_date.extend([parts[2], parts[1], parts[0]])
        return '-'.join(rev_date)

    def run(self):
        print('Listening...')
        while True:
            try:
                self.server_socket.listen(1)
                self.server_socket.settimeout(0.5)
                client_socket, client_address = self.server_socket.accept()
                if client_address[0] not in self.clients:
                    self.clients.append(client_address[0])
                    print('New client connected. Address: ', client_address)
                    if len(self.clients) > 1:
                        print('Client limit exceeded!')
                        print(self.clients)
                        break
                #client_socket.settimeout(2.0)
                msg = json.loads(client_socket.recv(4096).decode())

                if 'update' in msg[0]:
                    self.send_data(client_socket)
                if 'remove' in msg[0]:
                    t_id = int(msg[0]['remove'])
                    record = next((t for t in self.db if t['trip_id'] == t_id), None)
                    if record:
                        self.db.remove(record)
                        self.db_update()
                        self.send_data(client_socket)
                if 'trip_id' in msg[0]:
                    for trip in msg:
                        self.db.append(trip)
                        self.db_update()
            except socket.timeout:
                pass
            #client_socket.settimeout(None)

            now = str(datetime.datetime.now()).split(' ')[1][:5]

            if now in {'05:00', '11:00', '17:00', '23:00', '09:11'}:
                self.get_trips_data(now)


def main():
    crawler = ScraperServer(ip='127.0.0.1', port=64535)
    crawler.run()


if __name__ == '__main__':
    main()