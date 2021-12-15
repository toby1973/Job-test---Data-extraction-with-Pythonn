import datetime
import re 
import requests
from bs4 import BeautifulSoup
import csv

def geturl(inputdepart, inputarrival, inputcurency, inputdepartdays, inputreturndays, inputadult, inputchild, inputinfant): # Creating URL acording to filters

    TodayDepart = datetime.date.today() + datetime.timedelta(days=inputdepartdays)
    TodayReturn = datetime.date.today() + datetime.timedelta(days=inputreturndays+inputdepartdays)

    datefrom = TodayDepart.strftime("%a$2C+%d+%b+%Y")
    dateto = TodayReturn.strftime("%a$2C+%d+%b+%Y")

    datefrom = datefrom.replace("$", "%")
    dateto = dateto.replace("$", "%")

    Urlm = "https://www.fly540.com/flights/nairobi-to-mombasa?isoneway=0&currency="+inputcurency+"&depairportcode="+inputdepart+"&arrvairportcode="+inputarrival+"&date_from="+datefrom+"&date_to="+dateto+"&adult_no="+inputadult+"&children_no="+inputchild+"&infant_no="+inputinfant+"&searchFlight=&change_flight="
    print("URL "+ str(inputdepartdays) +" days = ", Urlm)
    return(Urlm)

def Timezone(h, d): #Formating time for end result
    if re.search("^\w+\:\w+pm$", h):
        h = h.replace("pm", " pm")
        in_time = datetime.datetime.strptime(h, "%I:%M %p")
        out_time = datetime.datetime.strftime(in_time, "%H:%M")
        return d + out_time + " GMT+3 2021"
    else: return  d + h.replace("am", " ") + " GMT+3 2021" 

def Tax(inputadult, inputchild, inputcurency):
    if inputcurency == "USD":
        taxa = 6*float(inputadult)*2
        taxc = 6*float(inputchild)*2
        return taxa+taxc
    elif inputcurency == "KES":
        taxa = 600*inputadult*2
        taxc = 600*inputchild*2
        return taxa+taxc

def mergeDict(dict1, dict2): # Merging two dictionaries
   dict3 = {**dict1, **dict2}
   for key, value in dict3.items():
       if key in dict1 and key in dict2:
               dict3[key] = value + dict1[key] 
   return dict3

def Bsoup(r, tax): 
    """ Temporary variables"""
    ftemp=[]
    ftemp2 = []
    biglist = []

    soup = BeautifulSoup(r.content, 'lxml') # Gettings the content of the required page 

    flighthtml = soup.find_all('td', class_='fdetails') #Creating a list of flight details
    for x in (flighthtml):
        ftemp.append(x.text.strip().replace("\n", "$").split("$", 1)[0])


    for idx1, i in enumerate(ftemp): #editing the list of flighthtml
        if re.search("stop$", i):
            ftemp.pop(idx1)
        if re.search("^USD", i) or re.search("^KES", i):
            ftemp[idx1] = i.split('See')[0]
        ftemp2.append(ftemp[idx1].replace(")", "").replace('  ', '(').split('('))
        
    for idx1, i in enumerate(ftemp2): #editing the list o flighthtml
        for j in i:
            if(len(ftemp2[idx1]) == 5): 
                ftemp2[idx1].pop(-2)
            if re.search("^USD", j or re.search("^KES", j)):
                biglist.append(ftemp2[idx1-2] + ftemp2[idx1-1]+ ftemp2[idx1])

    outcontent=[]
    incontent=[]
    for idz, i in enumerate(biglist): # Filling dictionaries with the flight information
        outdictemp={}
        indictemp={}
        for idx, j in enumerate(i):
            if i[3] == inputdepart:
                if(inputdepart == j):
                    outdictemp["outbound_departure_airport"] = j
                if(inputarrival == j):
                    outdictemp["outbound_arrival_airport"] = j     
                if re.search("^USD", j or re.search("^KES", j)):
                    outdictemp["total_price"] = float(j.split(" ",2)[1])
                if re.search("^\w+\:\w+pm$", j) and i[idx+2] == inputdepart or re.search("^\w+\:\w+am$", j) and i[idx+2] == inputdepart:
                    outdictemp["outbound_departure_time"] = (Timezone(j, i[idx+1]))
                elif re.search("^\w+\:\w+pm$", j) and i[idx+2] == inputarrival or re.search("^\w+\:\w+am$", j) and i[idx+2] == inputarrival:
                    outdictemp["outbound_arrival_time"] = (Timezone(j, i[idx+1]))               
            elif i[3] == inputarrival:
                if(inputarrival == j):
                    indictemp["inbound_departure_airport"] = (j)
                if(inputdepart == j):
                    indictemp["inbound_arrival_airport"] = (j)
                if re.search("^USD", j or re.search("^KES", i)):
                    indictemp["total_price"] = float(j.split(" ",2)[1])
                if re.search("^\w+\:\w+pm$", j) and i[idx+2] == inputarrival or re.search("^\w+\:\w+am$", j) and i[idx+2] == inputarrival:
                    indictemp["inbound_departure_time"] = (Timezone(j, i[idx+1]))
                elif re.search("^\w+\:\w+pm$", j) and i[idx+2] == inputdepart or re.search("^\w+\:\w+am$", j) and i[idx+2] == inputdepart:
                    indictemp["inbound_arrival_time"] = (Timezone(j, i[idx+1]))
        if outdictemp:
            outcontent.append(outdictemp)
        if indictemp:
            incontent.append(indictemp)

    flightdetails=[]
    for i in outcontent:
        for j in incontent: #1-3
            flightdetails.append(mergeDict(i, j))

    for idx, i in enumerate(flightdetails):
        flightdetails[idx]['taxes'] = tax
            
    return flightdetails

def write(flightdetails, inputdepartdays): # converting dictionary to csv
    csv_file = "output"+str(inputdepartdays)+".csv"
    csv_columns=['outbound_departure_airport', 'outbound_arrival_airport','outbound_departure_time','outbound_arrival_time',"inbound_departure_airport", "inbound_arrival_airport", "inbound_departure_time", "inbound_arrival_time",'total_price','taxes']

    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns, delimiter=";")
            writer.writeheader()
            writer.writerows(flightdetails)

        print(csv_file +" was created")    
    except:
        print("An exception occurred") 


""" Inputs """
inputdepart = "NBO"
inputarrival = "MBA"
inputcurency= "USD"
inputdepartdays10= 10
inputdepartdays20= 20 
inputreturndays= 7
inputadult = '1' # Tax 6 USD or 600 KES each
inputchild = '0' # Tax 6 USD or 600 KES each
inputinfant = '0' # No tax

headers ={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.10; Win64; x64 rv:84.0) Gecko.20100101 Firefox.84.0',
}

proxy={'http':'','https':''}

"""Getting the required page"""
r10 = requests.get(geturl(inputdepart, inputarrival, inputcurency, inputdepartdays10, inputreturndays, inputadult, inputchild, inputinfant), headers=headers, proxies=proxy)
r20 = requests.get(geturl(inputdepart, inputarrival, inputcurency, inputdepartdays20 , inputreturndays, inputadult, inputchild, inputinfant), headers=headers, proxies=proxy)

write(Bsoup(r10, Tax(inputadult, inputchild, inputcurency)), inputdepartdays10) 
write(Bsoup(r20, Tax(inputadult, inputchild, inputcurency)), inputdepartdays20)