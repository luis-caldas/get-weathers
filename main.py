#!/usr/bin/env python3

# Program imports
import os

# Custom imports
from PyPDF2 import PdfFileWriter
from bs4 import BeautifulSoup
import requests

# Email imports
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# Initialize global variables from env
SMTP_USER = os.getenv('SMTP_USER')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SMTP_MAIL_TO = os.environ.get('SMTP_MAIL_TO')

# Global variables
WEBSITE_MET = "https://www.met.ie/forecasts/marine-inland-lakes/sea-area-forecast"
WEBSITE_BBC = "https://www.metoffice.gov.uk/weather/specialist-forecasts/coast-and-sea/shipping-forecast"

# Main function
def main():

    ### Request ###
    # Get pages
    met_page = requests.get(WEBSITE_MET)
    bbc_page = requests.get(WEBSITE_BBC)

    # Check if pages were successful
    if (met_page.status_code != 200):
        print ("Unable to fetch MET page")
        return
    if (met_page.status_code != 200):
        print ("Unable to fetch BBC page")
        return

    # Input pages to soup
    met_soup = BeautifulSoup(met_page.text, 'html.parser')
    bbc_soup = BeautifulSoup(bbc_page.text, 'html.parser')

    # Extract MET data
    met_data = dict()
    met_data["title"] = met_soup.find("h1").find("span").get_text()
    met_data_all = met_soup.find("div", {"class": "row"}).find("div").find_all("div")
    met_data["footer"] = met_data_all[-1].get_text().strip('\n')
    met_data["valid"] = met_data_all[0].find("p").get_text()
    met_data["issued"] = met_data_all[6].find_all("p")[-1].get_text()
    met_data["list"] = [
        {
            "title": met_data_all[0].find_all("div")[-1].find("h2").get_text(),
            "body": met_data_all[0].find_all("div")[-1].find_all("p")[0].get_text(),
        }, {
            "title": met_data_all[0].find_all("h2")[-1].get_text(),
            "body": met_data_all[0].find_all("p")[-3].get_text(),
            "info": [
                met_data_all[0].find_all("p")[-2].get_text()
            ]
        }, {
            "title": met_data_all[3].find("h2").get_text(),
            "info": [
                met_data_all[3].find_all("p")[0].get_text(),
                met_data_all[3].find_all("p")[1].get_text(),
                met_data_all[3].find_all("p")[2].get_text()
            ]
        }, {
            "title": met_data_all[4].find("h2").get_text(),
            "info": [
                met_data_all[4].find_all("p")[0].get_text(),
                met_data_all[4].find_all("p")[1].get_text(),
                met_data_all[4].find_all("p")[2].get_text()
            ]
        }, {
            "title": met_data_all[5].find("h2").get_text(),
            "info": [
                met_data_all[5].find_all("p")[0].get_text(),
                met_data_all[5].find_all("p")[1].get_text(),
                met_data_all[5].find_all("p")[2].get_text()
            ]
        }, {
            "title": met_data_all[6].find("h2").get_text(),
            "body": met_data_all[6].find_all("p")[0].get_text().strip(" \n")
        }
    ]

    # Extract BBC data
    bbc_data = dict()
    bbc_data["title"] = bbc_soup.find("h1", {"class": "article-heading"}).get_text()
    bbc_data_all_header = bbc_soup.find("div", {"id": "summary"})
    bbc_data["synopsis"] = bbc_data_all_header.find("p", {"class": "synopsis-time"}).get_text().strip()
    bbc_data["synopsis-text"] = bbc_data_all_header.find("p", {"class": "synopsis-text"}).get_text().strip()
    bbc_data["issued"] = bbc_data_all_header.find("div", {"id": "sea-forecast-time"}).\
        find_all("p")[0].get_text().replace('\n', ' ').strip()
    bbc_data["valid"] = bbc_data_all_header.find("div", {"id": "sea-forecast-time"}).\
        find_all("p")[-1].get_text().replace('\n', ' ').strip()
    bbc_data_all = bbc_soup.find("div", {"id": "shipping-forecast-areas"})
    bbc_data["list"] = [
        {
            "title": bbc_data_all.find("section", {"id": "sole"}).find("h2").get_text(),
            "info": [
                bbc_data_all.find("section", {"id": "sole"}).find_all("dt")[0].get_text(),
                bbc_data_all.find("section", {"id": "sole"}).find_all("dd")[0].get_text(),
                bbc_data_all.find("section", {"id": "sole"}).find_all("dt")[1].get_text(),
                bbc_data_all.find("section", {"id": "sole"}).find_all("dd")[1].get_text(),
                bbc_data_all.find("section", {"id": "sole"}).find_all("dt")[2].get_text(),
                bbc_data_all.find("section", {"id": "sole"}).find_all("dd")[2].get_text(),
                bbc_data_all.find("section", {"id": "sole"}).find_all("dt")[3].get_text(),
                bbc_data_all.find("section", {"id": "sole"}).find_all("dd")[3].get_text()
            ]
        }, {
            "title": bbc_data_all.find("section", {"id": "lundy"}).find("h2").get_text(),
            "info": [
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dt")[0].get_text(),
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dd")[0].get_text(),
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dt")[1].get_text(),
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dd")[1].get_text(),
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dt")[2].get_text(),
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dd")[2].get_text(),
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dt")[3].get_text(),
                bbc_data_all.find("section", {"id": "lundy"}).find_all("dd")[3].get_text()
            ]
        }, {
            "title": bbc_data_all.find("section", {"id": "fastnet"}).find("h2").get_text(),
            "info": [
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dt")[0].get_text(),
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dd")[0].get_text(),
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dt")[1].get_text(),
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dd")[1].get_text(),
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dt")[2].get_text(),
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dd")[2].get_text(),
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dt")[3].get_text(),
                bbc_data_all.find("section", {"id": "fastnet"}).find_all("dd")[3].get_text()
            ]
        }, {
            "title": bbc_data_all.find("section", {"id": "irishsea"}).find("h2").get_text(),
            "info": [
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dt")[0].get_text(),
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dd")[0].get_text(),
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dt")[1].get_text(),
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dd")[1].get_text(),
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dt")[2].get_text(),
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dd")[2].get_text(),
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dt")[3].get_text(),
                bbc_data_all.find("section", {"id": "irishsea"}).find_all("dd")[3].get_text()
            ]
        }, {
            "title": bbc_data_all.find("section", {"id": "shannon"}).find("h2").get_text(),
            "info": [
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dt")[0].get_text(),
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dd")[0].get_text(),
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dt")[1].get_text(),
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dd")[1].get_text(),
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dt")[2].get_text(),
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dd")[2].get_text(),
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dt")[3].get_text(),
                bbc_data_all.find("section", {"id": "shannon"}).find_all("dd")[3].get_text()
            ]
        }, {
            "title": bbc_data_all.find("section", {"id": "rockall"}).find("h2").get_text(),
            "info": [
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dt")[0].get_text(),
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dd")[0].get_text(),
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dt")[1].get_text(),
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dd")[1].get_text(),
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dt")[2].get_text(),
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dd")[2].get_text(),
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dt")[3].get_text(),
                bbc_data_all.find("section", {"id": "rockall"}).find_all("dd")[3].get_text()
            ]
        }, {
            "title": bbc_data_all.find("section", {"id": "malin"}).find("h2").get_text(),
            "info": [
                bbc_data_all.find("section", {"id": "malin"}).find_all("dt")[0].get_text(),
                bbc_data_all.find("section", {"id": "malin"}).find_all("dd")[0].get_text(),
                bbc_data_all.find("section", {"id": "malin"}).find_all("dt")[1].get_text(),
                bbc_data_all.find("section", {"id": "malin"}).find_all("dd")[1].get_text(),
                bbc_data_all.find("section", {"id": "malin"}).find_all("dt")[2].get_text(),
                bbc_data_all.find("section", {"id": "malin"}).find_all("dd")[2].get_text(),
                bbc_data_all.find("section", {"id": "malin"}).find_all("dt")[3].get_text(),
                bbc_data_all.find("section", {"id": "malin"}).find_all("dd")[3].get_text()
            ]
        }
    ]

    import json
    print(json.dumps(bbc_data, indent=4))

    return

    ### Send email ###
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = SMTP_MAIL_TO
    message["Subject"] = "MET + BBC Weathers"

    # Message body
    body = "PLS FIND ATT WEATHERS X2"

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    # Open PDF file in binary mode
    with open("test.pdf", "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to sent by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        "attachment; filename= %s" % "weathers-INFO-DTC.pdf",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Send actual mail
    with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, SMTP_MAIL_TO, text)

    print("Successfuly Sent the mail")

if __name__ == '__main__':
    main()
