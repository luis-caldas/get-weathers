#!/usr/bin/env python3

# Program imports
import os
import re
from glob import glob
from copy import deepcopy
from datetime import datetime

# Custom imports
from bs4 import BeautifulSoup
from fpdf import FPDF, php
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

CACHE_FILE_MET = "/tmp/weather-time-cache-met"
CACHE_FILE_BBC = "/tmp/weather-time-cache-bbc"

PDF_EXTENSION = "PDF"

# New printing function with timestamps
def printn(label, message):
    time_now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print("[%s] [%s] %s" % (
        time_now,
        label,
        message
    ))

# Main function
def main():

    ### Request ###
    # Get pages
    try:
        met_page = requests.get(WEBSITE_MET)
        bbc_page = requests.get(WEBSITE_BBC)
    except Exception as e:
        printn ("ERROR", "Exception %s raised when getting pages" % e.__class__.__name__)
        return

    # Check if pages were successful
    if (met_page.status_code != 200):
        printn ("INFO", "Unable to fetch MET page")
        return
    if (met_page.status_code != 200):
        printn ("INFO", "Unable to fetch BBC page")
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
    print(met_data_all, len(met_data_all))
    met_issued_found = met_data_all[-2].find_all("p")[-1]
    met_data["issued"] = met_issued_found.get_text() if met_issued_found else "No issued time found"
    met_data_extra = met_data_all[0].find_all("div")
    met_data["list"] = [
        {
            "title": met_data_all[0].find_all("h2")[-1].get_text(),
            "info": [ each_paragraph.get_text() for each_paragraph in \
                    met_data_all[0].find_all("h2")[-1].find_next_siblings("p")[:-1] ]
        }
    ] + [
        {
            "title": each_block.find("h2").get_text(),
            "info": [ each_paragraph.get_text().strip(" \n") for each_paragraph in each_block.find_all("p") ]
        } for each_block in met_data_extra
    ] + [
        { "title": each_block.find("h2").get_text(),
          "info": [ each_paragraph.get_text().strip(" \n") for each_paragraph in each_block.find_all("p") ]
          } for each_block in met_data_all[3:-2]
    ] + [
        {
            "title": met_data_all[-2].find("h2").get_text(),
            "body": met_data_all[-2].find_all("p")[0].get_text().strip(" \n")
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
    bbc_data_split = [
            (bbc_data_all.find("section", {"id": each_area}), each_area) for each_area in ["sole", "lundy", "fastnet", "irishsea", "shannon", "rockall", "malin"]
    ]
    bbc_data["list"] = list()
    # Iterate the list and populate the list
    for (each_entry, each_area_out) in bbc_data_split:
        # Create a local disctionary
        local_dict = {
            "title": bbc_data_all.find("section", {"id": each_area_out}).find("h2").get_text()
        }
        local_dict["info"] = list()
        # Check if issued time is shouwn and add it if so
        let_issued_time = each_entry.find("p", {"class": "forecast-issue-time"})
        if let_issued_time:
            local_dict["info"].extend([
                "Time",
                let_issued_time.get_text().strip()
            ])
        local_dict["info"].extend([
            value for pair in zip(
                [ individual_entry.get_text() for individual_entry in each_entry.find_all("dt") ],
                [ individual_entry.get_text() for individual_entry in each_entry.find_all("dd") ]
            ) for value in pair
        ])
        # Add it to master list
        bbc_data["list"].append(local_dict)

    printn ("INFO", "Extracted the information for the websites")

    ### Check times ###
    # Replace multiple spaces in strings
    bbc_data["valid"] = re.sub(' +', ' ', bbc_data["valid"]);
    bbc_data["issued"] = re.sub(' +', ' ', bbc_data["issued"]);
    met_data["valid"] = re.sub(' +', ' ', met_data["valid"]);
    met_data["issued"] = re.sub(' +', ' ', met_data["issued"]);
    # Extract website times
    bbc_time = re.search(\
            "For the period ([0-2]\d):([0-5]\d) \(([^ ]*)\) on [^ ]+ (\d+) ([a-zA-Z]{3}) (\d{4}) to", \
            bbc_data["valid"])
    met_time = re.search(\
            "Forecast valid from: ([0-2]\d):([0-5]\d), [^ ]+ (\d+) ([^ ]+) (\d+) until", \
            met_data["valid"])

    # Digest all times
    if bbc_time:
        bbc_datetime_month = datetime.strptime(bbc_time.group(5), "%b")
        bbc_datetime = bbc_datetime_month.replace(
            hour=int(bbc_time.group(1)), minute=int(bbc_time.group(2)),
            day=int(bbc_time.group(4)), year=int(bbc_time.group(6))
        )
    else:
        printn ("ERROR", bbc_data["valid"])
        return

    if met_time:
        met_datetime_month = datetime.strptime(met_time.group(4), "%B")
        met_datetime = met_datetime_month.replace(
            hour=int(met_time.group(1)), minute=int(met_time.group(2)),
            day=int(met_time.group(3)), year=int(met_time.group(5))
        )
    else:
        printn ("ERROR", met_data["valid"])
        return

    # Check disparity between time
    time_disparity_hours = abs(divmod((bbc_datetime - met_datetime).total_seconds(), 3600)[0])
    if (time_disparity_hours > 3):
        printn ("ERROR", "Time disparity was too big")
        printn ("INFO", "MET Time is %s" % met_datetime.strftime("%d%H%MZ%b%y").upper())
        printn ("INFO", "BBC Time is %s" % bbc_datetime.strftime("%d%H%MZ%b%y").upper())
        return

    # Create the full military time
    mil_time_met = met_datetime.strftime("%d%H%MZ%b%y").upper()
    mil_time_bbc = bbc_datetime.strftime("%d%H%MZ%b%y").upper()

    # Truth table for updated times
    updated_times = {
        "met": True,
        "bbc": True
    }

    ### Cached runs ###
    # Check if we should run this time
    if os.path.isfile(CACHE_FILE_MET):
        with open(CACHE_FILE_MET, "r") as cachefile:
            met_time_file = cachefile.read()
            datetime_before = datetime.fromisoformat(met_time_file)
            cachefile.close()
            # Check if we are a newer time
            if (met_datetime <= datetime_before):
                printn ("WARNING", "Met Eireann still hasnt updated the time")
                updated_times["met"] = False

    if os.path.isfile(CACHE_FILE_BBC):
        with open(CACHE_FILE_BBC, "r") as cachefile:
            bbc_time_file = cachefile.read()
            datetime_before = datetime.fromisoformat(bbc_time_file)
            cachefile.close()
            # Check if we are a newer time
            if (bbc_datetime <= datetime_before):
                printn ("WARNING", "BBC still hasnt updated the time")
                updated_times["bbc"] = False

    # Check truth table
    if ((updated_times["met"] == False) or (updated_times["bbc"] == False)):
        return

    ### Create the full PDF document ###

    # Create a new footer method
    class PDF(FPDF):

        # Init with custom variables for page grouping
        def __init__(self, *args, **kwargs):
            FPDF.__init__(self, *args, **kwargs)
            self.new_page_group = False
            self.page_groups = dict()
            self.curr_page_group = None

        def start_page_group(self):
            self.new_page_group = True

        # Return page number for group
        def group_page_no(self):
            return self.page_groups[self.curr_page_group]

        def page_group_alias(self):
            return self.curr_page_group

        # Overwrite the begin page function with custom one
        # that uses page groups
        def _beginpage(self, *args, **kwargs):

            FPDF._beginpage(self, *args, **kwargs)

            if self.new_page_group:
                group_size = len(self.page_groups) + 1
                alias_figure = "{{{nb%d}}}" % group_size
                self.page_groups[alias_figure] = 1
                self.curr_page_group = alias_figure
                self.new_page_group = False
            elif self.curr_page_group:
                self.page_groups[self.curr_page_group] += 1

        # Overwrite putpages function
        def _putpages(self, *args, **kwargs):

            nb = self.page

            if self.page_groups:
                for each_key in self.page_groups:
                    for each_index in range(1, nb + 1):
                        self.pages[each_index] = \
                            self.pages[each_index].replace(
                                self._escape(php.UTF8ToUTF16BE(each_key, False)),
                                self._escape(php.UTF8ToUTF16BE(str(self.page_groups[each_key]), False))
                             )

            FPDF._putpages(self, *args, **kwargs)

        def footer(self):
            self.set_y(-15)
            self.set_font("", "I", 8)
            self.cell(
                0, 10,
                "Page %s of %s" % (self.group_page_no(), self.page_group_alias()),
                0, 0, 'C'
            )

    # Create it
    left_margin = 20
    pdf = PDF(orientation = 'P', unit = "mm", format="A4")
    pdf.set_margins(left_margin, 10, 10)
    pdf.set_title("Met Eireann @ %s & BBC Weathers @ %s" % (mil_time_met, mil_time_bbc))
    pdf.set_author("Robot")
    pdf.set_creator("Automatic bot from https://github.com/luis-caldas/get-weathers")

    # Add page
    pdf.start_page_group()
    pdf.add_page()

    # Add custom font
    pdf.add_font("Etoile", "", "./fonts/IosevkaEtoile-Regular.ttf", uni=True)
    pdf.add_font("Etoile", "B", "./fonts/IosevkaEtoile-Bold.ttf", uni=True)
    pdf.add_font("Etoile", "I", "./fonts/IosevkaEtoile-Italic.ttf", uni=True)
    pdf.add_font("Etoile", "BI", "./fonts/IosevkaEtoile-BoldItalic.ttf", uni=True)
    pdf.set_font("Etoile")

    # Create two PDFs for both documents
    bbc_pdf = deepcopy(pdf)
    met_pdf = deepcopy(pdf)

    ### Start writing
    local_tab = ' ' * 8;

    # BBC
    bbc_pdf.set_font("", "I", 16)
    bbc_pdf.write(10, "BBC Weathers @ %s" % mil_time_bbc)
    bbc_pdf.ln()
    bbc_pdf.set_font("", "I", 13)
    bbc_pdf.write(5, bbc_data["title"])
    bbc_pdf.ln(15)
    bbc_pdf.set_font("", "IU", 10)
    bbc_pdf.write(5, bbc_data["valid"])
    bbc_pdf.ln()
    bbc_pdf.set_font("", "I", 10)
    bbc_pdf.write(5, bbc_data["issued"])
    bbc_pdf.ln(15)
    bbc_pdf.set_font("", "B", 13)
    bbc_pdf.write(5, "The general synopsis")
    bbc_pdf.ln(10)
    bbc_pdf.set_font("", "", 10)
    bbc_pdf.write(5, local_tab + bbc_data["synopsis-text"])
    bbc_pdf.ln(15)

    # Iterate list places
    for item_index, each_place in enumerate(bbc_data["list"]):

        # Create full copy of current document to experiment
        experiment_copy = deepcopy(bbc_pdf)

        # Keep doing until we have it at the right spot
        effective_run = False
        while True:

            # Save page to check if we broke page
            page_now = bbc_pdf.page_no()

            # Determine which document should be changed
            doc = bbc_pdf if effective_run else experiment_copy

            doc.set_font("", "BU", 12)
            doc.write(5, each_place["title"])
            doc.ln(8)
            doc.set_font("", "", 10)

            # Iterate inside info
            for index, item in enumerate(each_place["info"]):

                # Check if even and make it a item
                if (index % 2 == 0):
                    doc.write(5, local_tab + "%s: " % item.strip())

                else:
                    # Iterate all the lines and print them
                    all_lines = [each for each in item.splitlines() if each]
                    for line_i, each_line in enumerate(all_lines):
                        doc.write(5, "%s%s" % (
                            each_line.strip(),
                            (
                                ("." if each_line[-1] != "." else "") if
                                (line_i >= len(all_lines) -1) else
                                (", " if each_line[-1] not in [":", ",", "."] else " ")
                            )
                        ))
                    # Add newline after block
                    doc.ln()

            # Check if we broke page
            if page_now == doc.page_no():
                # If not we can continue the loop
                doc.ln(7)
                bbc_pdf = doc
                break

            else:
                # If it overflew return and add page
                printn("PDF", "Overflow found rebuilding the block")
                effective_run = True
                bbc_pdf.add_page()

    # Start MET
    met_pdf.set_font("", "I", 16)
    met_pdf.write(10, "Met Éireann Weathers @ %s" % mil_time_met)
    met_pdf.ln()
    met_pdf.set_font("", "I", 13)
    met_pdf.write(5, met_data["title"])
    met_pdf.ln(15)
    met_pdf.set_font("", "IU", 10)
    met_pdf.write(5, met_data["valid"])
    met_pdf.ln()
    met_pdf.set_font("", "I", 10)
    met_pdf.write(5, met_data["issued"])
    met_pdf.ln(15)

    # Iterate the items
    for each_item in met_data["list"]:

        # Create full copy of current document to experiment
        experiment_copy = deepcopy(met_pdf)

        # Keep looping until the bockis in the proper position
        effective_run = False
        while True:

            # Save page to check if we broke page
            page_now = met_pdf.page_no()

            # Determine which document should be changed
            doc = met_pdf if effective_run else experiment_copy

            doc.set_font("", "B", 12)
            doc.write(5, each_item["title"])
            doc.ln(8)
            doc.set_font("", "", 10)
            # Check for body and write it
            if "body" in each_item:
                doc.write(5, local_tab + each_item["body"])
                doc.ln()
            # Iterate inside info if present
            if "info" in each_item:
                for each_entry in each_item["info"]:
                    doc.write(5, local_tab + each_entry)
                    doc.ln()

            # Check if we broke page
            if page_now == doc.page_no():
                # If not we can continue the loop
                doc.ln(7)
                met_pdf = doc
                break

            else:
                # If it overflew return and add page
                printn("PDF", "Overflow found rebuilding the block")
                effective_run = True
                met_pdf.add_page()

    # Create PDF filename
    met_pdf_filename = "%s_MET_WEATHERS.%s" % (mil_time_met, PDF_EXTENSION)
    bbc_pdf_filename = "%s_BBC_WEATHERS.%s" % (mil_time_bbc, PDF_EXTENSION)

    # Sent file to output
    met_pdf.output(met_pdf_filename, 'F')
    bbc_pdf.output(bbc_pdf_filename, 'F')

    printn ("INFO", "Created the documents")

    ### Send email ###
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = SMTP_MAIL_TO
    message["Subject"] = "Met Eireann @ %s & BBC Weathers @ %s" % \
            (mil_time_met, mil_time_bbc)

    # Message body
    body = "PLS FIND ATT %sMET %sBBC WEATHERS" % (mil_time_met, mil_time_bbc)

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    # Iterate the files
    for each_file in [bbc_pdf_filename, met_pdf_filename]:

        # Open PDF file in binary mode
        with open(each_file, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        # Encode file in ASCII characters to sent by email
        encoders.encode_base64(part)

        # Add header as key/value pair to attachment part
        part.add_header(
            "Content-Disposition",
            "attachment; filename= %s" % each_file,
        )

        # Add attachment to message
        message.attach(part)

    # Convert message to string
    text = message.as_string()

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Send actual mail
    with smtplib.SMTP_SSL(SMTP_SERVER, 465, context=context) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, SMTP_MAIL_TO, text)

    printn ("INFO", "Successfuly Sent the mail")

    # Remove old pdfs
    for each_pdf in glob("./*.%s" % PDF_EXTENSION):
        os.remove(each_pdf)

    printn ("INFO", "Removed old PDF files")

    # Store the time last sent email
    with open(CACHE_FILE_MET, "w") as cachefile:
        cachefile.write(met_datetime.isoformat())
        cachefile.close()
    with open(CACHE_FILE_BBC, "w") as cachefile:
        cachefile.write(bbc_datetime.isoformat())
        cachefile.close()

if __name__ == '__main__':
    main()

