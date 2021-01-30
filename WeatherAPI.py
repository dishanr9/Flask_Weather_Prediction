
import shutil
import os
import csv
import json
import tempfile
from flask import Flask, request,render_template,jsonify
from flask_restful import Resource, Api ,reqparse
from flask_restplus import Resource, Api ,reqparse,Namespace,fields
import sys,requests
from geopy.geocoders import Nominatim
from flask_cors import CORS, cross_origin
import datetime
from datetime import timedelta
import numpy as np

import sys,requests
app = Flask(__name__)

CORS(app)

api = Api(app, version="1", title="Weather REST API",
          description="This API provides endpoints such as Historical and Forecast in combination with and[or] without parameters")

weatherAPI = Namespace('HistoricalWeather', description='Historical Weather')
api.add_namespace(weatherAPI)

parser = reqparse.RequestParser()
parser.add_argument('DATE')
parser.add_argument('TMAX')
parser.add_argument('TMIN')

postModel = api.model('AccountModel', {
    'DATE': fields.String(required=True, description='Date in YYYYMMDD format'),
    'TMAX': fields.Integer(required=True, description='Max temp'),
    'TMIN': fields.Integer(required=True, description='Min temp'),
})

args1 = {
    'DATE': fields.String(required=True, description='Date in YYYYMMDD format'),
    'TMAX': fields.Integer(required=True, description='Max temp'),
    'TMIN': fields.Integer(required=True, description='Min temp')
}

class WeatherApplication(Resource):
    def get(self):
        return "/Historical/ , /Historical/'<DATE>' and /Forecast/'<DATE>' as GET Requests \n /Historical/ with date as POST and Delete Requests"


@api.doc(False)
def SaveWeatherData(newEntryForOperation):
    fieldNames = ["DATE","TMAX","TMIN"]
    with open('dailyweather.csv','r+',newline='') as csvFile,open('tempFile.csv','r+') as tempFile:
        dictReader = csv.DictReader(csvFile,fieldnames=fieldNames)
        dictWriter = csv.DictWriter(tempFile,fieldnames=fieldNames,newline='')
        newEntryForOperation["TMAX"]=int(newEntryForOperation["TMAX"])
        newEntryForOperation["TMIN"] = int(newEntryForOperation["TMIN"])
        for row in dictReader:
            print(row)
            if row["DATE"] != str(newEntryForOperation["DATE"]):
                dictWriter.writerow(row)
            else:
                dictWriter.writerow(newEntryForOperation)
    os.remove("dailyweather.csv")
    os.rename("tempFile.csv","dailyweather.csv")
    return

@api.doc(False)
def StoreWeatherData( newEntryForOperation ):
    fieldNames = ["DATE","TMAX","TMIN"]
    bFound = False
    tempcsvFile = tempfile.NamedTemporaryFile(mode="w",delete=False)
    with open('dailyweather.csv',newline='') as csvFile,tempcsvFile:
        dictReader = csv.DictReader(csvFile,fieldnames=fieldNames)
        dictWriter = csv.DictWriter(tempcsvFile, fieldnames=fieldNames)
        newEntryForOperation["TMAX"]=float(newEntryForOperation["TMAX"])
        newEntryForOperation["TMIN"] = float(newEntryForOperation["TMIN"])
        for row in dictReader:
            if row["DATE"] == str(newEntryForOperation["DATE"]):
                dictWriter.writerow(newEntryForOperation)
                bFound = True
            else:
                dictWriter.writerow(row)
        if not bFound:
            dictWriter.writerow(newEntryForOperation)
    shutil.move(tempcsvFile.name,'dailyweather.csv')

@api.doc(False)
def DeleteWeatherData(delRow):
    with open('dailyweather.csv','r+',newline='') as csvFile:
        dateToDelete = delRow["DATE"]
        fieldNames = ["DATE","TMAX","TMIN"]
        csvReader = csv.DictReader(csvFile,fieldnames=fieldNames)
        csvWriter = csv.DictWriter(csvFile,fieldnames=fieldNames)

        updatedList = [row for row in csvReader if row["DATE"] != dateToDelete]

        csvFile.seek(0)
        csvWriter.writerows(updatedList)
        csvFile.truncate()
    return

# Function to retrieve Historical weather data
# Returns an array of JSON objects containing "DATE","TMAX" and "TMIN"
# @app.route("/",methods=["GET"])
@api.doc(False)
def getWeatherData():
    with open('dailyweather.csv','r') as csvFile:
        reader = csv.DictReader(csvFile)
        csvToJsonData = json.dumps([row for row in reader])
        jsonDataOutput = json.loads(csvToJsonData)
        jsonData=[]
        for row in jsonDataOutput:
            jsonData.append(row)
        return jsonData

@api.route('/historical/',methods=["GET","POST"])
class HistoryOfAllDatesOfWeatherData(Resource):
    @api.doc(responses={200: 'Available dates retrieved successfully'})
    def get(self):
        jsonDataOutput = getWeatherData()
        jsonDataOfDates = []
        for row in jsonDataOutput:
             val = row["DATE"]
             jsonDataOfDates.append({"DATE":str(val)})
        return jsonDataOfDates,200

    @api.doc(responses={201: 'Data inserted/updated successfully'})
    @api.expect(postModel,validate=True)
    #@api.doc(params={"DATE": 'string', "TMAX": 'float', "TMIN": 'float'})
    def post(self):
        historicalData = getWeatherData()
        args = parser.parse_args()
        newObj = {'DATE': (args['DATE']), 'TMAX': float(args['TMAX']), 'TMIN': float(args['TMIN'])}
        print(newObj)
        historicalData.append(newObj)
        StoreWeatherData(newObj)
        return {'DATE':(args['DATE'])}, 201

# Function to retrieve records of an existing date.
# Returns JSON object containing "DATE", "TMAX" and "TMIN"
# Handles GET(date)

@api.doc(True)
@api.route('/historical/<date_id>', methods=["GET","DELETE"])
class HistoricalDataOfDate(Resource):
    @api.doc(responses={200: 'Data retrieved successfully'})
    @api.doc(responses={404: 'Date not found!'})
    def get(self,date_id):
        historicalData = getWeatherData()
        for row in historicalData:
            if (row["DATE"] == date_id):
                return row,200
        return "DATE not found! Try again",404

    @api.doc(responses={204: 'Data deleted successfully'})
    @api.doc(responses={404: 'Data to delete not found!'})
    def delete(self,date_id):
        historicalData = getWeatherData()
        args = parser.parse_args()
        for row in historicalData:
            if(row["DATE"] == date_id):
                delRow = row
                break
        if(delRow != None):
            historicalData.remove(delRow)
            DeleteWeatherData({"DATE":delRow["DATE"]})
            return {"DATE": str(delRow["DATE"])},204
        else:
            return "Data of the date to be deleted doesn't exist!",404

# @api.route('/historical/',methods=["POST"])
# #@api.doc(params={'DATE':'string','TMAX':'float',"TMIN":'float'})
# class PostDataOfDate(Resource):
#     @api.doc(responses={201: 'Data inserted/updated successfully'})
#     @api.expect(postModel,validate=True)
#     #@api.doc(params={"DATE": 'string', "TMAX": 'float', "TMIN": 'float'})
#     def post(self):
#         historicalData = getWeatherData()
#         args = parser.parse_args()
#         newObj = {'DATE': (args['DATE']), 'TMAX': float(args['TMAX']), 'TMIN': float(args['TMIN'])}
#         print(newObj)
#         historicalData.append(newObj)
#         StoreWeatherData(newObj)
#         return {'DATE':(args['DATE'])}, 201

@api.doc(False)
def forecastFromDarkSky(userDate):
    from datetime import datetime
    app_id = "69485ca3ec9cbbf91c55176a54d8115d"
    toExclude = "exclude=currently,minutely,hourly,alerts&amp;units=si"
    location = Nominatim(user_agent="Disha's API").geocode("Cincinnati", language='en_US')
    d_from_date = datetime.strptime(userDate, '%Y%m%d')

    latitude = str(location.latitude)
    longitude = str(location.longitude)
    forecastArray=[]

    for i in range(7):
        new_date = (d_from_date + timedelta(days=i)).strftime('%Y-%m-%d')
        search_date = new_date + "T00:00:00"
        response = requests.get(
            "https://api.darksky.net/forecast/" + app_id + "/" + latitude + "," + longitude + "," + search_date + "?" + toExclude)
        json_res = response.json()
        json_tmin = json_res['daily']['data'][0]['apparentTemperatureMin']
        json_tmax = json_res['daily']['data'][0]['apparentTemperatureMax']
        json_summary =  json_res['daily']['data'][0]['summary']
        unit_type = '°F' if json_res['flags']['units'] == 'us' else '°C'
        forecastArray.append({"DATE":search_date,"TMAX":json_tmax,"TMIN":json_tmin,"SUMMARY":json_summary})

    return forecastArray

@app.route("/UI")
def index():
    return render_template("googleCanvas.html")

@api.doc(True)
@api.route('/thirdPartyWeatherForecasting/<date_id>',methods=["GET"])
class thirdPartyWeatherForecasting(Resource):
    def get(self,date_id):
        jsonForecastArray = forecastFromDarkSky(date_id)
        if len(jsonForecastArray):
            #jsonForecastArray.headers.add('Access-Control-Allow-Origin','*')
            return jsonForecastArray, 200
        else:
            return "Forecast retrieval failed! Contact Disha", 400
        #return jsonForecastArray,200 if len(jsonForecastArray) else "Forecast retrieval failed! Contact Disha",400

# REVIEW NEEDED
# TO-DO : CUSTOM CODE FOR LINEAR REGRESSION
def forecastLinearRegression(date_id):
    with open('dailyweather.csv', "rt") as f:
        reader = csv.DictReader(f, delimiter=',')
        dateList = []
        tmaxList = []
        tminList = []
        for row in reader:
            dateList.append(int(row["DATE"]))
            tmaxList.append(np.float(row["TMAX"]))
            tminList.append(np.float(row["TMIN"]))

    #DateEntry = input('Enter Date of your choice YYYYMMDD')
    DateEntry = date_id
    DateEntry = int(DateEntry)
    DateEntrydateMonth = int(repr(DateEntry)[-4:-2]) #date_id[:5]
    #DateEntrydateMonth=int(date_id[:4])
    ##print (DateEntrydateMonth)
    DateEntrydateday = int(repr(DateEntry)[-2:]) #date_id[4:6]
    #DateEntrydateday=int(date_id[4:6])
    ##print (DateEntrydateday)
    DateEntryLD = int(repr(DateEntry)[-4:])
    DateEntryFD = int(repr(DateEntry)[:-4])
    date1 = datetime.date(DateEntryFD, DateEntrydateMonth, DateEntrydateday)
    YearMTminT = []
    Xaxi = []
    YaxiMax1 = []
    YaxiMin1 = []
    YaxiMax2 = []
    YaxiMin2 = []
    YaxiMax3 = []
    YaxiMin3 = []
    YaxiMax4 = []
    YaxiMin4 = []
    YaxiMax5 = []
    YaxiMin5 = []
    YaxiMax6 = []
    YaxiMin6 = []
    YaxiMax7 = []
    YaxiMin7 = []
    YaxiMax8 = []
    YaxiMin8 = []
    for jj in range(len(dateList)):
        dateListLD = int(repr(dateList[jj])[-4:])
        if DateEntryLD == dateListLD:
            year = int(repr(dateList[jj])[:-4])
            YearMTminTPut = [year, tmaxList[jj], tminList[jj]]
            YearMTminT.append(YearMTminTPut)
            Xaxi.append(year)
            YaxiMax1.append(tmaxList[jj])
            YaxiMin1.append(tminList[jj])
            YaxiMax2.append(tmaxList[jj + 1])
            YaxiMin2.append(tminList[jj + 1])
            YaxiMax3.append(tmaxList[jj + 2])
            YaxiMin3.append(tminList[jj + 2])
            YaxiMax4.append(tmaxList[jj + 3])
            YaxiMin4.append(tminList[jj + 3])
            YaxiMax5.append(tmaxList[jj + 4])
            YaxiMin5.append(tminList[jj + 4])
            YaxiMax6.append(tmaxList[jj + 5])
            YaxiMin6.append(tminList[jj + 5])
            YaxiMax7.append(tmaxList[jj + 6])
            YaxiMin7.append(tminList[jj + 6])
            YaxiMax8.append(tmaxList[jj + 7])
            YaxiMin8.append(tminList[jj + 7])
    YaxiMaxVari = [YaxiMax1, YaxiMax2, YaxiMax3, YaxiMax4, YaxiMax5, YaxiMax6, YaxiMax7, YaxiMax8]
    YaxiMinVari = [YaxiMin1, YaxiMin2, YaxiMin3, YaxiMin4, YaxiMin5, YaxiMin6, YaxiMin7, YaxiMin8]
    XaxiUpdateMax = []
    XaxiUpdateMin = []
    MaxTempRange = []
    MinTempRange = []
    YaxiUpdateMax = []
    YaxiUpdateMin = []
    for e in range(len(YaxiMaxVari)):
        FornowMax = YaxiMaxVari[e]
        FornowMin = YaxiMinVari[e]
        YaxiMaxVarimean = np.mean(YaxiMaxVari[e])
        YaxiMaxVarimean = np.mean(YaxiMaxVari[e])
        YaxiMinVarimean = np.mean(YaxiMinVari[e])
        YaxiMaxVariSTD = np.std(YaxiMaxVari[e])
        YaxiMinVariSTD = np.std(YaxiMinVari[e])
        MaxTempRange = ([(YaxiMaxVarimean - YaxiMaxVariSTD), (YaxiMaxVarimean + YaxiMaxVariSTD)])
        MinTempRange = ([(YaxiMinVarimean - YaxiMinVariSTD), (YaxiMinVarimean + YaxiMinVariSTD)])
        XaxiUpdateMax.append('XaxiUpdateMax' + str(e))
        XaxiUpdateMax[e] = []
        YaxiUpdateMax.append('YaxiUpdateMax' + str(e))
        YaxiUpdateMax[e] = []
        XaxiUpdateMin.append('XaxiUpdateMin' + str(e))
        XaxiUpdateMin[e] = []
        YaxiUpdateMin.append('YaxiUpdateMin' + str(e))
        YaxiUpdateMin[e] = []
        for f in range(len(FornowMax)):
            if FornowMax[f] < MaxTempRange[1]:
                if FornowMax[f] > MaxTempRange[0]:
                    XaxiUpdateMax[e].append(Xaxi[f])
                    YaxiUpdateMax[e].append(FornowMax[f])
        FornowMax = []
        for f in range(len(FornowMin)):
            if FornowMin[f] < MinTempRange[1]:
                if FornowMin[f] > MinTempRange[0]:
                    XaxiUpdateMin[e].append(Xaxi[f])
                    YaxiUpdateMin[e].append(FornowMin[f])
        FornowMin = []
        YaxiUpdateMax1=[]
        YaxiUpdateMin1=[]
        for r in range(len(YaxiUpdateMax)):
            fmax= np.sort(YaxiUpdateMax[r])
            fmax= np.array(fmax).tolist()
            fmin= np.sort(YaxiUpdateMin[r])
            fmin= np.array(fmin).tolist()
            YaxiUpdateMax1.append(fmax)
            YaxiUpdateMin1.append(fmin)
    dates = []
    dateString=[]
    MaxTemp = []
    MinTemp = []
    for t in range(len(YaxiUpdateMax)):
        [b0, b10] = (np.polyfit(XaxiUpdateMin[t], YaxiUpdateMin1[t], 1))
        [b1, b11] = (np.polyfit(XaxiUpdateMax[t], YaxiUpdateMax1[t], 1))
        ##    rmin=(np.polyfit(Xaxi,YaxiMinVari[t],1,full=True))
        ##    rmax= (np.polyfit(Xaxi,YaxiMaxVari[t],1,full=True))

        if (DateEntrydateMonth == 12):
            nextday = DateEntrydateday + t
            if (31 - (nextday) >= 0):
                TempPredMin = b0 * DateEntryFD + b10
                TempPredMax = b1 * DateEntryFD + b11
                ##    print (rmax[1],rmin[1])
                if t == 0:
                    date1 = date1
                    b = date1.strftime('%Y-%m-%dT00:00:00')
                    bs = date1.strftime('%Y%m%d')
                    dates.append(b)
                    dateString.append(bs)
                    if TempPredMax < TempPredMin:
                        a = TempPredMax
                        TempPredMax = TempPredMin
                        TempPredMin = a
                    MaxTemp.append(round(TempPredMax, 2))
                    MinTemp.append(round(TempPredMin, 2))
                    # print ('Date=', date1, 'MaxTemp =', round(TempPredMax,2),'°F', 'Mintemp =', round(TempPredMin,2),'°F')
                else:
                    date1 = date1 + datetime.timedelta(days=1)
                    b = date1.strftime('%Y-%m-%dT00:00:00')
                    bs = date1.strftime('%Y%m%d')
                    dates.append(b)
                    dateString.append(bs)
                    if TempPredMax < TempPredMin:
                        a = TempPredMax
                        TempPredMax = TempPredMin
                        TempPredMin = a
                    MaxTemp.append(round(TempPredMax, 2))
                    MinTemp.append(round(TempPredMin, 2))
                    # print ('Date=', date1, 'MaxTemp =', round(TempPredMax,2),'°F', 'Mintemp =', round(TempPredMin,2),'°F')
            else:
                year = DateEntryFD + 1
                TempPredMin = b0 * year + b10
                TempPredMax = b1 * year + b11
                if t == 0:
                    date1 = date1
                    b = date1.strftime('%Y-%m-%dT00:00:00')
                    bs = date1.strftime('%Y%m%d')
                    dates.append(b)
                    dateString.append(bs)
                    if TempPredMax < TempPredMin:
                        a = TempPredMax
                        TempPredMax = TempPredMin
                        TempPredMin = a
                    MaxTemp.append(round(TempPredMax, 2))
                    MinTemp.append(round(TempPredMin, 2))
                    # print ('Date=', date1, 'MaxTemp =', round(TempPredMax,2),'°F', 'Mintemp =', round(TempPredMin,2),'°F')
                else:
                    date1 = date1 + datetime.timedelta(days=1)
                    b = date1.strftime('%Y-%m-%dT00:00:00')
                    bs = date1.strftime('%Y%m%d')
                    dates.append(b)
                    dateString.append(bs)
                    if TempPredMax < TempPredMin:
                        a = TempPredMax
                        TempPredMax = TempPredMin
                        TempPredMin = a
                    MaxTemp.append(round(TempPredMax, 2))
                    MinTemp.append(round(TempPredMin, 2))
                    # print ('Date=', date1, 'MaxTemp =', round(TempPredMax,2),'°F', 'Mintemp =', round(TempPredMin,2),'°F')
        else:
            TempPredMin = b0 * DateEntryFD + b10
            TempPredMax = b1 * DateEntryFD + b11
            ##    print (rmax[1],rmin[1])
            ##        print ('Date =',t, 'Year =', DateEntryFD, 'MaxTemp =', round(TempPredMax,2),'°F', 'Mintemp =', round(TempPredMin,2),'°F')
            if t == 0:
                date1 = date1
                b = date1.strftime('%Y-%m-%dT00:00:00')
                bs = date1.strftime('%Y%m%d')
                dates.append(b)
                dateString.append(bs)
                if TempPredMax < TempPredMin:
                    a = TempPredMax
                    TempPredMax = TempPredMin
                    TempPredMin = a
                MaxTemp.append(round(TempPredMax, 2))
                MinTemp.append(round(TempPredMin, 2))
                # print ('Date=', date1, 'MaxTemp =', round(TempPredMax,2),'°F', 'Mintemp =', round(TempPredMin,2),'°F')
            else:
                date1 = date1 + datetime.timedelta(days=1)
                b = date1.strftime('%Y-%m-%dT00:00:00')
                bs = date1.strftime('%Y%m%d')
                dates.append(b)
                dateString.append(bs)
                if TempPredMax < TempPredMin:
                    a = TempPredMax
                    TempPredMax = TempPredMin
                    TempPredMin = a
                MaxTemp.append(round(TempPredMax, 2))
                MinTemp.append(round(TempPredMin, 2))
    resultArray = []
    for i in range(8):
        resultArray.append({"DATE":dates[i],"TMAX":MaxTemp[i],"TMIN":MinTemp[i],"DATESTRING":dateString[i]})
    return resultArray

@api.route('/forecast/<date_id>',methods=["GET"])
class approximateWeatherForecasting(Resource):
    def get(self,date_id):
        approxForecastArray = forecastLinearRegression(date_id)
        if len(approxForecastArray):
            return approxForecastArray,200
        else:
            return "Approximate forecast retrieval failed! Contact M13254448",400

# api.add_resource(WeatherApplication,'/')
# api.add_resource(HistoryOfAllDatesOfWeatherData, '/historical/')
# api.add_resource(HistoricalDataOfDate,'/historical/<date_id>')
# api.add_resource(PostDataOfDate,'/historical/')
# api.add_resource(DeleteWeatherDate,'/historical/<date_id>')
# api.add_resource(approximateWeatherForecasting,'/forecast/<string:date_id>')
# api.add_resource(thirdPartyWeatherForecasting,'/thirdPartyWeatherForecasting/<date_id>')

if __name__ == '__main__':
    app.run(host='127.0.0.1',debug=True,port=8000)
