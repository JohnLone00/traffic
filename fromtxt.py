import redis
r = redis.Redis(host='localhost',port=6379,decode_responses=True)
with open(r'./torTraffic/10-10-supply.txt') as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        r.rpush('supply', line)