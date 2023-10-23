import time
import redis
import os
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common import exceptions


proxies = {
    'http': 'socks5h://localhost:9051',
    'https': 'socks5h://localhost:9051'
}

itertimes = 30
serverIP = "localhost"
serverTorPort = 9052
serverTcpdumpPath = r"./torPCAP/"
serverInforPath = r"./torInfor/"
badPcapLog = r"./torTrafficLog/badPcapLog.txt"
#websitesFile = r"./torTraffic/10-20.txt"
websitesFile = ''
executable_path=r'./torTraffic/geckodriver'  # selenium启动firefox需要的驱动
#executable_path=r'./torTraffic/geckodriver.exe'
keeptime = 200
r = redis.Redis(host='localhost',port=6379,decode_responses=True)


def initDriver():
    #  配置浏览器代理

    firefox_profile = FirefoxProfile()
    # set socks proxy
    firefox_profile.set_preference("network.proxy.type", 1)
    firefox_profile.set_preference("network.proxy.socks_version", 5)
    firefox_profile.set_preference("network.proxy.socks", serverIP)
    firefox_profile.set_preference("network.proxy.socks_port", serverTorPort)
    # firefox_profile.set_preference("network.proxy.socks_remote_dns", True)
    firefox_profile.set_preference("browser.download.folderList", 2)
    # 禁用缓存
    firefox_profile.set_preference("browser.cache.disk.enable", False)
    firefox_profile.set_preference("browser.cache.memory.enable", False)
    firefox_profile.set_preference("browser.cache.offline.enable", False)
    firefox_profile.set_preference("network.http.use-cache", False)

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument('--headless')
    firefox_options.add_argument('--disable-gpu')
    # firefox_options.add_experimental_option('useAutomationExtension', False)
    d = DesiredCapabilities.FIREFOX
    d["goog:loggingPrefs"] = {"performance": "ALL"}
    
    driver = webdriver.Firefox(desired_capabilities=d,executable_path=executable_path,
                               firefox_profile=firefox_profile,
                               options=firefox_options)
    return driver

def startTcpdump(filename):
    #cmd = "tcpdump tcp port \(8443 or 9001 or 443 or 8140 or 8080 or 80 or 9030 or 9040 or 9050 or 9051 or 9150 or 9003 or 500\) -w " + filename
    cmd = "tcpdump tcp port \(8443 or 9001 or 443 or 500 or 9003\) -w " + filename
    #cmd  = "tcpdump tcp and \(\(src host 192.210.190.98 and src port 17602\) or \(dst host 192.210.190.98 and dst port 17602\)\) -w " + filename
    # cmd = "tcpdump tcp and not port \(9052 or 22 or 6010 or 6011\) -w " + filename
    os.popen(cmd)

def closeTcpdump():
    time.sleep(2)
    try:
        os.popen('ps -ef | grep tcpdump | grep -v grep | cut -c 10-18 | xargs kill')
    except:
        print('have not closed!!')


def simulation(driver,times,url):

    try:
        driver.get(url)
        time.sleep(30)
    except exceptions.TimeoutException as e:  # 若页面长时间没有加载完成 则执行js脚本 停止加载
        driver.execute_script("window.stop()")
        print('Time out!!!!')
        return

    except BaseException as e2:
        print(e2)
        print('error!!!!')
        with open(badPcapLog,'a') as f:
            r.rpush('supply', str(times) + ' ' + url)
        return

    try:
        print(driver.title)
    except BaseException as e3:
        print('title miss!!!!')
        return



def main(num):
    with open(websitesFile, 'r') as f:
        for line in f.readlines():
            driver = initDriver()
            # 设置页面加载 超时时间
            driver.set_page_load_timeout(keeptime)
            driver.set_script_timeout(keeptime)
            driver.delete_all_cookies()
            url = line.strip()
            if not os.path.exists(serverTcpdumpPath + str(num)):
                os.makedirs(serverTcpdumpPath + str(num))
            u = url
            filepath = serverTcpdumpPath + str(num) + '/'+ u.replace('https://','') +'.pcap'
            print(filepath)
            startTcpdump(filepath)
            simulation(driver,num , url)
            closeTcpdump()
            driver.delete_all_cookies()
            time.sleep(2)
            driver.quit()
            # supply()



def supply():
    driver = initDriver()
    driver.set_page_load_timeout(keeptime)
    driver.set_script_timeout(keeptime)
    driver.delete_all_cookies()

    while r.llen('supply') != 0:
        e = r.lindex('supply', 0)
        times,url = e.split(' ')
        if not os.path.exists(serverTcpdumpPath + str(times)):
            os.makedirs(serverTcpdumpPath + str(times))
        u = url
        filepath = serverTcpdumpPath + str(times) + '/' + u.replace('https://', '') + '.pcap'
        print(filepath)
        startTcpdump(filepath)
        simulation(driver, times, url)
        closeTcpdump()
        r.lpop('supply')

    driver.quit()
    #time.sleep(20)

def traffic(website,begin,end):
    global websitesFile
    websitesFile = "./torTraffic/"+website
    for num in range(begin,end+1):
         main(num)
    supply()
    r.delete('supply')
