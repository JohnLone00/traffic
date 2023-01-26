import time
import redis
import requests
import socket
import os
import requests
import subprocess
from bs4 import  BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.common import exceptions
import re
import psutil
import signal

proxies = {
    'http': 'socks5h://localhost:9051',
    'https': 'socks5h://localhost:9051'
}

itertimes = 30
serverIP = "localhost"
serverTorPort = 9052
serverTcpdumpPath = r"./torPCAP/"
badPcapLog = r"./torTrafficLog/badPcapLog.txt"
#websitesFile = r"./torTraffic/10-20.txt"
websitesFile = ''
executable_path=r'./torTraffic/geckodriver'  # selenium启动firefox需要的驱动
#executable_path=r'./torTraffic/geckodriver.exe'
keeptime = 80
r = redis.Redis(host='localhost',port=6379,decode_responses=True)
pattern = re.compile(r'\d{1,}')

def initDriver():
    #  配置浏览器代理

    firefox_profile = FirefoxProfile()
    # set socks proxy
    firefox_profile.set_preference("network.proxy.type", 1)
    firefox_profile.set_preference("network.proxy.socks_version", 5)
    firefox_profile.set_preference("network.proxy.socks", serverIP)
    firefox_profile.set_preference("network.proxy.socks_port", serverTorPort)
    firefox_profile.set_preference("network.proxy.socks_remote_dns", True)
    firefox_profile.set_preference("browser.download.folderList", 2)
    # 禁用缓存
    firefox_profile.set_preference("browser.cache.disk.enable", False)
    firefox_profile.set_preference("browser.cache.memory.enable", False)
    firefox_profile.set_preference("browser.cache.offline.enable", False)
    firefox_profile.set_preference("network.http.use-cache", False)

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument('--headless')
    firefox_options.add_argument('--disable-gpu')

    driver = webdriver.Firefox(executable_path=executable_path,
                               firefox_profile=firefox_profile,
                               options=firefox_options)
    return driver

def startTcpdump(filename):
    #cmd = "tcpdump tcp port \(8443 or 9001 or 443 or 8140 or 8080 or 80 or 9030 or 9040 or 9050 or 9051 or 9150 or 9003 or 500\) -w " + filename
    #cmd = "tcpdump tcp port \(8443 or 9001 or 443 or 500\) -w " + filename
    #cmd  = "tcpdump tcp and \(\(src host 192.210.190.98 and src port 17602\) or \(dst host 192.210.190.98 and dst port 17602\)\) -w " + filename
    cmd = "tcpdump tcp and not port \(9052 or 22 or 6010 or 6011\) -w " + filename
    os.popen(cmd)

def closeTcpdump():
    time.sleep(2)

    pids = psutil.pids()
    for pid in pids:
        try:
            p = psutil.Process(pid)
            # get process name according to pid
            process_name = p.name()
            # kill process "sleep_test1"

            if 'tcpdump' == process_name:
                print("kill specific process: name(%s)-pid(%s)" % (process_name, pid))
                os.kill(pid, signal.SIGKILL)
        except:
            try:
                proid = os.popen('ps -a | grep tcpdump')
                pids = pattern.findall(proid.read()[:6])
                print(pids)
                for i in pids:
                    os.popen('kill ' + i)
            except:
                print('have not closed!!')



def requestss(times,webId,url):
    '''采用requests进行请求（速度快）'''
    if not os.path.exists(serverTcpdumpPath + str(times)):
        os.makedirs(serverTcpdumpPath + str(times))
    filepath = serverTcpdumpPath + str(times) + '/' +str(times) +'+'+ webId + '.pcap'
    print(filepath)
    startTcpdump(filepath)
    time.sleep(1)
    try:
        print(url)
        response = requests.get(url,timeout=60, proxies=proxies)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            pagetitle = soup.find("title")
            pagetitle = pagetitle.text
            pagetitle = pagetitle.replace('\n','')
            print(pagetitle)
            if pagetitle == '':
                with open(badPcapLog, 'a') as f:
                    f.write(str(times) + '.' + webId + '.' + 'title=')
        with open(badPcapLog, 'a') as f:
            f.write(str(times) + '.' + webId + '.' + '404 NO FOUND!')
    except BaseException as e:
        print(e)
        with open(badPcapLog,'a') as f:
            f.write(str(times) +'.'+webId +'.'+'BadRequest!' )
    closeTcpdump()


def simulation(driver,times,webId,url):

    try:
        driver.get(url)
    except exceptions.TimeoutException as e:  # 若页面长时间没有加载完成 则执行js脚本 停止加载
        driver.execute_script("window.stop()")
        print('Time out!!!!')
        with open(badPcapLog,'a') as f:
            f.write(str(times) +'.'+webId +'.'+'Time out!' +"\n")
            r.rpush('supply',str(times)+' '+webId +' '+url)
        return
    except BaseException as e2:
        print(e2)
        print('error!!!!')
        with open(badPcapLog,'a') as f:
            f.write(str(times) +'.'+webId +'.'+'Bad Request!'+"\n")
            r.rpush('supply', str(times) + ' ' + webId + ' ' + url)
        return
    try:
        print(driver.title)
    except BaseException as e3:
        print(e3)
        print('tile miss!!!!')
        with open(badPcapLog,'a') as f:
            f.write(str(times) +'.'+webId +'.'+'tile miss!!!!'+"\n")
            r.rpush('supply', str(times) + ' ' + webId + ' ' + url)
        return
    if driver.title == '' or 'Server Not Found' in driver.title or '404 NOT Found' in driver.title:
        with open(badPcapLog, 'a') as badLog:
            badLog.write(str(times) + '.' + str(webId) + ".title=" + driver.title + "\n")
            f.write(str(times) + '.' + webId + '.' + '404!!!!' + "\n")
            r.rpush('supply', str(times) + ' ' + webId + ' ' + url)

def main(num):
    with open(websitesFile, 'r') as f:
        for line in f.readlines():
            driver = initDriver()
            # 设置页面加载 超时时间
            driver.set_page_load_timeout(keeptime)
            driver.set_script_timeout(keeptime)
            driver.delete_all_cookies()
            websiteId, url = line.strip().split(" ")
            if not os.path.exists(serverTcpdumpPath + str(num)):
                os.makedirs(serverTcpdumpPath + str(num))
            filepath = serverTcpdumpPath + str(num) + '/' + str(num) + '+' + websiteId + '.pcap'
            print(filepath)
            startTcpdump(filepath)
            simulation(driver,num ,websiteId , url)
            closeTcpdump()
            #driver.delete_all_cookies()
            time.sleep(5)
            driver.quit()
    time.sleep(20)


def supply():
    driver = initDriver()
    driver.set_page_load_timeout(keeptime)
    driver.set_script_timeout(keeptime)
    driver.delete_all_cookies()
    count = 0
    while r.llen('supply') != 0:
        if count > 5000:
            break
        try:
            e = r.lindex('supply', 0)
            times,webid,url = e.split(' ')
            if not os.path.exists(serverTcpdumpPath + str(times)):
                os.makedirs(serverTcpdumpPath + str(times))
            filepath = serverTcpdumpPath + str(times) + '/' + str(times) + '+' + webid + '.pcap'
            print(filepath)
            startTcpdump(filepath)
            simulation(driver, times, webid, url)
            closeTcpdump()
            #driver.delete_all_cookies()
            r.lpop('supply')
        except:
            pass
        time.sleep(5)
        count+=1
    driver.quit()
    #time.sleep(20)

def traffic(website,begin,end):
    global websitesFile
    websitesFile = website
    for num in range(begin,end+1):
         main(num)
    supply()
    r.delete('supply')

if __name__ == '__main__':

    supply()
    r.delete('supply')