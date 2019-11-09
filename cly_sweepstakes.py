import sys
import os

from bson.regex import Regex
from pymongo import MongoClient
import PySimpleGUI as sg

client = MongoClient("mongodb://mongouserprod_ro:XCQrDH91AjghUHrqJ6Tw@cluster-panel-prod-shard-00-00-fg5bg.mongodb.net:27017,cluster-panel-prod-shard-00-01-fg5bg.mongodb.net:27017,cluster-panel-prod-shard-00-02-fg5bg.mongodb.net:27017/test?ssl=true&replicaSet=Cluster-Panel-Prod-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client.conversationally
# from here we need name, email, panelist_id, paypal_email, referral
panelists = db.panelists
panelist_demographics = db.panelist_demographics  # from here we need city, state
# from here we need unique_daily_interactions and unique_daily_interactions_google
panelist_report_current = db.panelist_report_current

inputs = sg.Window('Conversational.ly Sweepstakes Data Runner').Layout([
    [sg.Text('File location?', size=(10, 1)), sg.InputText('conversationally_data', size=(
        30, 1)), sg.SaveAs("Choose location", file_types=(("Spreadsheets", "*.csv"),))],
    [sg.Checkbox('Open csv file with default csv program?')],
    [sg.Checkbox('Open folder in file explorer?')],
    [sg.CloseButton('Cancel', button_color=('white', "red")),
     sg.CloseButton('Confirm', pad=((325, 0), (0, 0)))]
]).Read()
test_id = inputs[1][0]
file_destination = inputs[1][0] + ".csv"
file_checked = inputs[1][1]
folder_checked = inputs[1][2]
return_file = open(file_destination, "w")
return_file.write(
    "Panelist Id,First name,Email,referral.utm_medium,referral.panel_id,City,State,Paypal,Daily Alexa Count,Daily Google Count,Entries,Payment\n")

data = {}
query = {}
query["user_email"] = {
    u"$not": Regex(u"^.*@pulselabs\\.ai$", "i")
}

for p in panelists.find(query, {"_id": 0, "first_name": 1, "user_email": 1, "panelist_id": 1, "paypal_email": 1, "referral": 1}):
    if('panelist_id' not in p):
        sg.Popup(
            "Bad error", "There's a panelist with no panelist_id, i hope this never happens")
        return_file.write(
            "There's a panelist with no panelist_id, i hope this never happens" + p)
        return_file.close()
        raise SystemExit("There's a panelist with no panelist_id that's bad")
    else:
        panelist_id = p['panelist_id']
        # if(panelist_id already in data):
        # duplicate panelist_id
        # throw some errors

        data[panelist_id] = [" ", " ", " ", " ", " ", " ", " ", 0, 0]
        if('first_name' in p):
            data[panelist_id][0] = p['first_name']
        if('user_email' in p):
            data[panelist_id][1] = p['user_email']
        if('paypal_email' in p):
            data[panelist_id][6] = p['paypal_email']

    if('referral' in p and 'utm_campaign' in p['referral'] and p['referral']['utm_campaign'] == "$2referral"):
        if('utm_medium' in p['referral']):
            data[panelist_id][2] = p['referral']['utm_medium']
        else:
            data[panelist_id][2] = "$2ref, but no medium data"

        if('panel_id' in p['referral']):
            data[panelist_id][3] = p['referral']['panel_id']
        else:
            data[panelist_id][3] = "$2ref, but no panel id (likely vl)"

for p in panelist_demographics.find(query, {"_id": 0, "panelist_id": 1, "city": 1, "state": 1}):
    if('panelist_id' not in p):
        sg.Popup(
            "Bad error", "There's a panelist with no panelist_id, i hope this never happens")
        return_file.write(
            "There's a panelist with no panelist_id, i hope this never happens" + p)
        return_file.close()
        raise SystemExit("There's a panelist with no panelist_id that's bad")
    else:
        panelist_id = p['panelist_id']
        if(panelist_id in data):
            if("city" in p):
                data[panelist_id][4] = p['city']
            if("state" in p):
                data[panelist_id][5] = p['state']

for p in panelist_report_current.find(query, {"_id": 0, "panelist_id": 1, "unique_daily_interactions": 1, "unique_daily_interactions_google": 1}):
    if('panelist_id' not in p):
        sg.Popup(
            "Bad error", "There's a panelist with no panelist_id, i hope this never happens")
        return_file.write(
            "There's a panelist with no panelist_id, i hope this never happens" + p)
        return_file.close()
        raise SystemExit("There's a panelist with no panelist_id that's bad")
    else:
        panelist_id = p['panelist_id']
        if(panelist_id in data):
            if("unique_daily_interactions" in p and not isinstance(p['unique_daily_interactions'], str)):
                data[panelist_id][7] = p['unique_daily_interactions']

            if("unique_daily_interactions_google" in p and not isinstance(p['unique_daily_interactions_google'], str)):
                data[panelist_id][8] = p['unique_daily_interactions_google']


for d in data:
    return_file.write("{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
        d, data[d][0], data[d][1], data[d][2], data[d][3], data[d][4], data[d][5], data[d][6], data[d][7], data[d][8], data[d][7] + data[d][8], 5 if (data[d][7] >= 5 or data[d][8] >= 5) else ""))

return_file.close()

if folder_checked:
    if (file_destination.find('/') > -1):
        os.startfile(file_destination[0:file_destination.rfind('/')])
    else:
        os.startfile('')

if file_checked:
    os.startfile(file_destination)
