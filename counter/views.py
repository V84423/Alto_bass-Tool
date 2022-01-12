import requests
import os
import re
import pandas as pd
import urllib
import threading

from datetime import datetime
from threading import Thread
from time import sleep

from bs4 import BeautifulSoup
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils.crypto import get_random_string

from .models import Counter, User, Url

from django.shortcuts import render, HttpResponse
from django.core.mail import send_mail as sm


headers = {

    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7','Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive',

}

def biccamera(url):
    print(url)
    page = requests.get(url, headers=headers).text
    soup = BeautifulSoup(page, 'html.parser')
    ###############JP####################
    # soup.decode('utf-8','replace')

    goods = soup.find('h1').getText()
    print(goods)

    tbody = soup.findAll('tbody')[0]
    trs = tbody.findAll(class_='bcs_variationOff')
    onsale = 0
    inventory = 0

    onsale_tr = trs[0].getText().strip()
    if onsale_tr != '':
        onsale_str = trs[0].findAll('li')[0].getText()
        onsale = ''.join(filter(str.isdigit, onsale_str))

    
    inventory_attr = trs[3].findAll('p')[0].find('span').attrs['class']
    if inventory_attr[0] == 'label_green':
        inventory = 1
    if inventory_attr[0] == 'label_orange':
        inventory = 0
    if inventory_attr[0] == 'label_gray':
        inventory = -1

    arr = {'goods':goods, 'company':'biccamera', 'onsale':onsale, 'inventory':inventory}
    return arr


def yamada(url):
    print(url)
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    soup.decode('utf-8','replace')
    goods = soup.find('h1').getText()

    block = soup.find(class_='item-detail-block-right')
    parts = block.findAll(class_='parts-block')
    onsale = 0
    inventory = 0

    inventory_str = parts[0].find(class_='note').getText()

    if inventory_str == '24時間以内に出荷' or inventory_str == 'お取り寄せ':
        inventory = 1
    if inventory_str == '好評につき売り切れました' or inventory_str == '売り切れました':
        inventory = 0
    if inventory_str == '販売終了':
        inventory = -1

    onsale_str = parts[1].find(class_='point').getText()
    onsale_arr = re.findall('\d+', onsale_str)
    onsale = onsale_arr[1]

    arr = {'goods':goods, 'company':'yamada', 'onsale':onsale, 'inventory':inventory}
    return arr


def yodobashi(url):
    print(url)
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    goods = soup.find('h1').getText()
    block = soup.find(class_='buyBoxMain')
    onsale = 0
    inventory = 0
    onsale_str = soup.find(id="js_scl_pointrate")
    if onsale_str != None:
        onsale_str = onsale_str.getText()
        onsale = ''.join(filter(str.isdigit, onsale_str))

    inventory_str = block.find('li')
    if inventory_str != None:
        inventory_str = inventory_str.getText()
        if inventory_str == 'ショッピングカートに入れる':
            inventory = 1
        if inventory_str == '予定数の販売を終了しました':
            inventory = 0
    else:
        inventory = -1

    arr = {'goods':goods, 'company':'yodobashi', 'onsale':onsale, 'inventory':inventory}
    return arr


def registerUrl(url):

    if url.find("biccamera") != -1:
        return biccamera(url)

    if url.find("yamada") != -1:
        return yamada(url)

    if url.find("yodobashi") != -1:
        return yodobashi(url)


args = dict()
scrap_flag = False

def threaded_scrap():
    while True: 
        
        if scrap_flag:
            print('start')
            global args

            checkedItems = args['checkedItems']
            if checkedItems == 'all':
                urls = [{'url': url.url,'goods': url.goods,'company': url.company,'onsale': url.onsale,'inventory': url.inventory,'status': url.status} for url in Url.objects.all().order_by("-created_at")]
            else:
                ids = checkedItems.split(',')    
                urls = [{'url': url.url,'goods': url.goods,'company': url.company,'onsale': url.onsale,'inventory': url.inventory,'status': url.status} for url in Url.objects.filter(id__in=ids).order_by("-created_at")]
            
            msg = []

            for url in urls:
                diff = 'None'
                if url['url'].find("biccamera") != -1:
                    diff = check(biccamera(url['url']),url)

                if url['url'].find("yamada") != -1:
                    diff = check(yamada(url['url']),url)

                if url['url'].find("yodobashi") != -1:
                    diff = check(yodobashi(url['url']),url)
                
                print(diff)

                if diff != 'None':
                    msg.append([{'url':url['url'], 'note':diff}])
            
            print(msg)
            ############### set during time with sleep ###########################
            sleep(3)
        else:            
            print('stopping')
            sleep(3)


thread = Thread(target=threaded_scrap)
# thread.start()


def send_mail(request):

    global args
    emailAddress = args['emailAddress']

    res = sm(
        subject = 'Subject here',
        message = 'Here is the message.',
        from_email = 'info@todoku-yo.net',
        recipient_list = [emailAddress],
        fail_silently=False,
    )

    return res


def scrapStart(request):
    
    if request.method == "GET":
        global args
        args = {
            'checkedItems' : request.GET['checkedItems'],
            'emailAddress' : request.GET['emailAddress']
        }
        global scrap_flag
        scrap_flag = True      


        send_mail()


        return HttpResponse('started')
    


def scrapStop(request):
    print('stop')
    global scrap_flag
    scrap_flag = False
    return HttpResponse('stopped')


def check(new, old):
    
    diff = 'None'

    if new['inventory'] != old['inventory']:
        
        if new['inventory'] == -1: diff2 = '廃盤表記'
        if new['inventory'] == 0: diff2 = '在庫切れ表記'
        if new['inventory'] == 1: diff2 = '通常表記'

        if old['inventory'] == -1: diff1 = '廃盤表記'
        if old['inventory'] == 0: diff1 = '在庫切れ表記'
        if old['inventory'] == 1: diff1 = '通常表記'

        diff = str(diff1) + '->' + str(diff2)

    if new['onsale'] != old['onsale'] and int(new['onsale']) > 19:

        diff = str(new['onsale']) + '%下落'

    if new['inventory'] != old['inventory'] and new['onsale'] != old['onsale'] and int(new['onsale']) > 19:
        
        if new['inventory'] == -1: diff2 = '廃盤表記'
        if new['inventory'] == 0: diff2 = '在庫切れ表記'
        if new['inventory'] == 1: diff2 = '通常表記'

        if old['inventory'] == -1: diff1 = '廃盤表記'
        if old['inventory'] == 0: diff1 = '在庫切れ表記'
        if old['inventory'] == 1: diff1 = '通常表記'

        diff3 = str(new['onsale']) + '%下落'

        diff = str(diff1) + '->' + str(diff2) + ', ' + diff3
    
    return diff













#########################################################

def index(request):
    if len(Counter.objects.filter(key='counter')) == 0:
        counter = Counter(key='counter', value=0)
        counter.save()
    else:
        counter = get_object_or_404(Counter, key='counter')
    
    counter.value+=1
    counter.save()
    context = {'value': counter.value}
    return render(request, 'counter/index.html', context)

def dashboard(request):
    
    context = {}
    if request.session.keys():
        return render(request, 'dashboard.html', context)
    else:
        return render(request, 'login.html', context)

def login(request):
	context = {}
	return render(request, 'login.html', context)

def register(request):
	context = {}
	return render(request, 'register.html', context)

def goods(request):

    context = {}        
    if request.session.keys():
        return render(request, 'goods.html', context)
    else:
        return render(request, 'login.html', context)

###############################################################
def logout(request):
    request.session.clear()
    context = {}
    return render(request, 'login.html', context)



def loginUser(request):

    if request.method == "POST":
        
        # user = User.objects.filter(email=request.POST['email'])
        user = [{'id': user.id, 'name': user.name, 'email': user.email, 'password': user.password, 'state': user.state} for user in User.objects.filter(email=request.POST['email'])]
        
        if len(user) != 0:

            if(user[0]['password'] == request.POST['password']):
                
                # python manage.py migrate sessions

                request.session['id'] = user[0]['id']
                request.session['name'] = user[0]['name']
                request.session['email'] = user[0]['email']

                context = {}
                return render(request, 'goods.html', context)

            else:
                context = {"msg":"Fail Login - Invalid Password"}
        else:
            context = {"msg":"Fail Login - Nonregistered Email"}
        
        return render(request, 'login.html', context)

def addUrl(request):

    if request.method == "POST":
        arr = registerUrl(request.POST['url'])
        if len(Url.objects.filter(url=request.POST['url'])) == 0:
            url = Url.objects.create(url=request.POST['url'], goods=arr['goods'], company=arr['company'], onsale=arr['onsale'], inventory=arr['inventory'])
            url.save()
            saved_id = Url.objects.latest('id').id
            return JsonResponse({'saved_id':saved_id, 'onsale':arr['onsale'], 'inventory':arr['inventory']})
        else:
            return HttpResponse("exist")

def addUser(request):

    if request.method == "POST":

        if len(User.objects.filter(email=request.POST['email'])) == 0:

            chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            secret_key = get_random_string(60, chars)

            user = User.objects.create(name=request.POST['name'], email=request.POST['email'], password=request.POST['password'], token=secret_key)
            user.save()
            saved_id = User.objects.latest('id').id
            context = {"msg":"User was registered"}
        else:
            context = {"msg":"Fail Registration - Duplicated Email"}
        
        return render(request, 'login.html', context)

def getUrl(request):

    if request.method == "GET":
        url = [{'id': url.id, 'url': url.url,'goods': url.goods,'company': url.company,'onsale': url.onsale,'inventory': url.inventory,'status': url.status, 'created_at':url.created_at} for url in Url.objects.all().order_by("-created_at")]
        return JsonResponse({'url':url})

def delUrl(request):

    if request.method == "GET":
        ids = request.GET['ids']
        arr = []
        arr = ids.split(",")

        for id in arr:
            if id != 'ids':
                url = Url.objects.filter(id=id)
                url.delete()

        return HttpResponse('delUrl')
