def show():
    with open('banner.txt','r',encoding="utf-8") as f:
        l = f.readlines()
        for i in l:
            print(i.replace('\n',''))