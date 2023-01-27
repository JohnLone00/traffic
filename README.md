# traffic

# tor

#去官网下载源码
mkdir tor
cd tor
wget https://dist.torproject.org/tor-0.4.7.12.tar.gz
tar -zxvf tor-0.4.7.12.tar.gz
cd tor-0.4.7.12

#编译
sudo apt update
sudo apt upgrade
sudo apt-get install make
sudo apt-get install build-essential
sudo apt-get install libevent-dev -y
sudo apt-get install libssl-dev -y
sudo apt-get install zlib1g-dev -y
./configure
make && make install

#运行Tor
screen -R tor
cd src
vim tor
加一行SocksPort localhost:9052
app/tor -f torrc

出现100%即ok

#python脚本环境
sudo apt-get install firefox
sudo apt-get install redis
sudo apt-get install tcpdump
pip3 install selenium
pip3 install requests
pip3 install redis
pip3 install BeautifulSoup4
pip3 install psutil
