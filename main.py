#!/usr/bin/env python3

# Program imports
import os

# Custom imports
from bs4 import BeautifulSoup
from fpdf import FPDF
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

    print("Extracted the information for the websites")

    ### Create the full PDF document ###
    # Create it
    pdf = FPDF(orientation = 'P', unit = "mm", format="A4")
    pdf.set_title("Met Eireann and BBC Weathers") # TODO add time
    pdf.set_author("Robot")
    pdf.set_creator("Automatic bot from https://github.com/luis-caldas/get-weathers")

    # Add page
    pdf.add_page()

    # Add custom font
    pdf.add_font("Etoile", "", "./fonts/IosevkaEtoile-Regular.ttf", uni=True)
    pdf.add_font("Etoile", "B", "./fonts/IosevkaEtoile-Bold.ttf", uni=True)
    pdf.add_font("Etoile", "I", "./fonts/IosevkaEtoile-Italic.ttf", uni=True)
    pdf.add_font("Etoile", "BI", "./fonts/IosevkaEtoile-BoldItalic.ttf", uni=True)
    pdf.set_font("Etoile")

    ### Start writing
    local_tab = ' ' * 8;

    # BBC
    pdf.set_font("", "I", 16)
    pdf.write(10, "BBC Weathers")
    pdf.ln()
    pdf.set_font("", "I", 13)
    pdf.write(5, bbc_data["title"])
    pdf.ln(15)
    pdf.set_font("", "IU", 10)
    pdf.write(5, bbc_data["valid"])
    pdf.ln()
    pdf.set_font("", "I", 10)
    pdf.write(5, bbc_data["issued"])
    pdf.ln(15)
    pdf.set_font("", "B", 13)
    pdf.write(5, "The general synopsis")
    pdf.ln(10)
    pdf.set_font("", "", 10)
    pdf.write(5, local_tab + bbc_data["synopsis-text"])
    pdf.ln(20)

    # Iterate list places
    for item_index, each_place in enumerate(bbc_data["list"]):
        pdf.set_font("", "BU", 12)
        pdf.write(5, each_place["title"])
        pdf.ln(10)
        pdf.set_font("", "", 10)
        # Iterate inside info
        for index in range(int(len(each_place["info"]) / 2)):
            pdf.write(5, "%s:" % each_place["info"][index * 2])
            pdf.ln()
            pdf.write(5, local_tab + each_place["info"][(index * 2) + 1])
            pdf.ln()
        pdf.ln(15)
        # Break page if three items have been populated
        if (item_index == 2):
            pdf.add_page()

    # Break page for MET
    pdf.add_page()

    # Start MET
    pdf.set_font("", "I", 16)
    pdf.write(10, "Met Éireann Weathers")
    pdf.ln()
    pdf.set_font("", "I", 13)
    pdf.write(5, met_data["title"])
    pdf.ln(15)
    pdf.set_font("", "IU", 10)
    pdf.write(5, met_data["valid"])
    pdf.ln()
    pdf.set_font("", "I", 10)
    pdf.write(5, met_data["issued"])
    pdf.ln(15)

    # Iterate the items
    for each_item in met_data["list"]:
        pdf.set_font("", "BU", 12)
        pdf.write(5, each_item["title"])
        pdf.ln(8)
        pdf.set_font("", "", 10)
        # Check for body and write it
        if "body" in each_item:
            pdf.write(5, local_tab + each_item["body"])
            pdf.ln()
        # Iterate inside info if present
        if "info" in each_item:
            for each_entry in each_item["info"]:
                pdf.write(5, local_tab + each_entry)
                pdf.ln()
        pdf.ln(7)

    # Sent file to output
    pdf.output("WEATHERS.PDF", 'F')

    print("Created the document")

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
    with open("WEATHERS.PDF", "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to sent by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        "attachment; filename= %s" % "WEATHERS.PDF", # TODO add DTG
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
