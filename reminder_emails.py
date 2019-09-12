import datetime
import sys
from pathlib import Path

import mysql.connector

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, Personalization, Content, Subject, To, Bcc, MimeType, Asm)

from ConnectionHelper import ConnectionHelper
from Logger import Logger

SENDGRID_API_KEY = \
    "OBFUSCATED"
SENDER_NAME = "OBFUSCATED"
SENDER_EMAIL = "OBFUSCATED"
BCC = "OBFUSCATED"

# helper class "static final" variables to connect to databases
DEV = "dev"
PROD = "prod"

# These are the email template-ids on sendgrid
WEEKLY = "OBFUSCATED"
MONTHLY = "OBFUSCATED"
THREE = "OBFUSCATED"
DAILY = "OBFUSCATED"
UNSUBSCRIBE_ID = 4329

sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)

def logResponseData(logger, response):
    log_message = "\nHTTP Response Data\nStatus code: {}\nBody: {}\n\
        \nHeaders:\n{}".format(str(response.status_code),str(response.body),
        str(response.headers))
    logger.write(log_message)

def send_from_template(template, recipient):
    mail = Mail()
    mail.from_email = Email(SENDER_EMAIL,SENDER_NAME)
    mail.template_id = template
    mail.asm = Asm(UNSUBSCRIBE_ID)
    personalization = Personalization()
    personalization.add_to(Email(recipient))
    personalization.add_bcc(Email(BCC))
    mail.add_personalization(personalization)
    response = sg.client.mail.send.post(request_body=mail.get())
    logResponseData(logger,response)

def warn_ops(num_recipients):
    mail = Mail()
    mail.to = To("ops@pulselabs.ai")

    #this declaration looks stupid because of PEP8 rules for line length
    mail.content = Content(MimeType.text, "The script for sending onboarding \
        reminders is sending to {} panelists. That's a big number.".format(
        num_recipients))

    mail.from_email = Email(SENDER_EMAIL,SENDER_NAME)
    mail.subject = Subject("Many onboarding reminders warning")
    mail.bcc = Bcc(BCC)
    response = sg.client.mail.send.post(request_body=mail.get())
    logger.write("Ops warning for many reminders.\n",
        "Number of reminders sent: ", str(num_recipients))
    logResponseData(logger,response)

def clean_log():
    pass

def send_monthly_reminder(recipient):
    send_from_template(MONTHLY, recipient)

def send_weekly_reminder(recipient):
    send_from_template(WEEKLY, recipient)

def send_threely_reminder(recipient):
    send_from_template(THREE, recipient)

def send_daily_reminder(recipient):
    send_from_template(DAILY, recipient)

# if there's a command line argument, use that as log file path
if(len(sys.argv) > 1):
    path = sys.argv[1]

else:
    path = str(Path("var/log/logfile2.log"))

path = "{}.{}".format(path, datetime.date.today())

try:
    logger = Logger(path)

except FileNotFoundError:
    print("The given path was invalid. Make sure the directories exist, then try again.")
    sys.exit(1)

# uses ConnectionHelper.py to connect to dev db
# helper = ConnectionHelper(DEV)

# this would use ConnectionHelper to connect to prod
helper = ConnectionHelper(PROD)

mydb = helper.connect()

# Query panelists for those who are due for reminder emails
mycursor = mydb.cursor()
mycursor.execute(
    """SELECT email,datediff(curdate(),time_modified)
    FROM panelists WHERE time_modified IS NOT NULL AND
    (panelists.status = 'ACCOUNT_CREATED' OR panelists.status =
    'SAMPLE_TEST_PENDING' OR panelists.status = 'SURVEY_COMPLETED')
    AND (datediff(curdate(),time_modified) = 1 OR
    datediff(curdate(),time_modified) = 3 OR datediff(curdate(),time_modified)
    = 7 OR datediff(curdate(),time_modified) = 30)""")
panelists = mycursor.fetchall()

# if there are an alarming number of panelists to onboard, warn ops
if len(panelists) > 150:
    warn_ops(len(panelists))

# don't send reminder if ops was warned
else:
    # For each panelist, send them the proper email
    for p in panelists:
        logger.write("Email: {}\nDays since last activity: {}".format(p[0],p[1]))
        if(p[1] == 30):
            send_monthly_reminder(p[0])

        elif(p[1] == 7):
            send_weekly_reminder(p[0])

        elif(p[1] == 3):
            send_threely_reminder(p[0])

        elif(p[1] == 1):
            send_daily_reminder(p[0])
