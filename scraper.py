from bs4 import BeautifulSoup
from urllib2 import urlopen
import gspread
import sys
import scrapers
import argparse
from oauth import get_credentials, clear_credentials

def send_mail(title, link, price, date_posted, location, bedrooms, square_feet, email, search_terms):

    if not email:
        return

    import smtplib
    import os

    GMAIL_PASSWORD = os.environ['GMAIL_APTSNATCH_APP_SPECIFIC_PASSWORD']
    GMAIL_USERNAME = 'sverch724'

    # The below code never changes, though obviously those variables need values.
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.login(GMAIL_USERNAME, GMAIL_PASSWORD)

    email_subject = "Looking to live in %s" % title
    recipient = email

    import json

    template = open("email_template.txt").read()

    body_of_email = template % {'href':link,'query':search_terms}

    print body_of_email

    # TODO: Use something better to construct this rather than doing it manually.  See:
    # https://docs.python.org/2/library/email-examples.html#email-examples
    # TODO: Sent HTML email rather than plaintext?
    headers = "\r\n".join(["from: " + GMAIL_USERNAME,
                        "subject: " + email_subject,
                        "to: " + recipient,
                        "mime-version: 1.0"])

    # body_of_email can be plaintext or html!
    content = headers + "\r\n\r\n" + body_of_email
    session.sendmail(GMAIL_USERNAME, recipient, content)
    print content

def post_listings(listings, sheet_name, username=None, password=None):
    if username or password:
        google = gspread.login(username, password)
    else:
        credentials = get_credentials()
        try:
            google = gspread.authorize(credentials)
        except Exception, e:
            print "Exception trying to authenticate with google: %s" % e
            print "Clearing any credentials saved in keyring..."
            clear_credentials()
            sys.exit(1)

    spread = google.open(sheet_name).sheet1

    # Retrieve listings already in the spreadsheet, and use these to
    # filter current <listings> to prevent duplicates. We consider two
    # listings different from each other if their links don't match
    cur_listings = [l for l in spread.col_values(2) if l]
    listings = [l for l in listings if l[1] not in cur_listings]

    if len(cur_listings) == 0:
        print "Sheet %s is empty, adding title line." % sheet_name
        for col, header in enumerate(['Title', 'Link', 'Price', 'Date Posted', 'Location',
            'Bedrooms', 'Square Feet', 'Email', 'Search Terms'], 1):
            spread.update_cell(1, col, header)
        cur_listings.append('Link')

    if len(listings) > 0:
        plural = "listing" if len(listings) == 1 else "listings"
        print "Found %d new %s!"%(len(listings), plural)
    else:
        print "No new listings were found."
        return

    print "Posting results to Google Drive... this may take awhile"

    # Start at row 2, so we can keep the title row
    # Note that rows/columns are indexed starting at 1
    for row, listing in enumerate(listings, len(cur_listings)+1):
        for col, datum in enumerate(listing, 1):
            spread.update_cell(row, col, datum)

    print "Sending emails for new postings!"

    for listing in listings:
        send_mail(title=listing.title,
                link=listing.href,
                price=listing.price,
                date_posted=listing.date,
                location=listing.address,
                bedrooms=listing.bdrm,
                square_feet=listing.sqft,
                email=listing.mailto,
                search_terms=listing.query)

def csv_listings(listings):
    print ",".join(['title', 'href', 'price', 'date', 'address', 'bdrm', 'sqft', 'mailto', 'query'])
    for listing in listings:
        bdrm = listing.bdrm if listing.bdrm else "could not find bedroom count"
        sqft = listing.sqft if listing.sqft else "could not find sqft count"
        price = listing.price if listing.price else "could not find price"
        address = listing.address if listing.address else "could not find location"
        mailto = listing.mailto if listing.mailto else "could not find email address"
        title = listing.title.replace(",", ".")
        print ",".join([title, listing.href, price, listing.date, address, bdrm, sqft, mailto, listing.query])

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Parse craigslist and upload to a google spreadsheet",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--csv", help="Output as csv rather than uploading to a google "
            "spreadsheet", action="store_true")
    parser.add_argument("--sheet-name", help="Spreadsheet name", default="Snatched Apartments")
    parser.add_argument("--craigslist-url", help="Craigslist URL for your location",
            default="http://washingtondc.craigslist.org")
    parser.add_argument("--keywords", help="Comma separated list of search keywords",
            default="friendship heights,tenleytown")
    parser.add_argument("--max-price", help="Maximum monthly rent", default=1000, type=int)
    parser.add_argument("--min-bedrooms", help="Minimum number of bedrooms", default=1, type=int)
    parser.add_argument("--min-square-feet", help="Minimum square feet", default=800, type=int)
    parser.add_argument("--username", help="Google username.  Don't set this or --password to use oauth.")
    parser.add_argument("--password", help="Google password.  Don't set this or --username to use oauth.")
    args = parser.parse_args()
    listings = scrapers.scrape_craigslist(root_url=args.craigslist_url, keywords=args.keywords.split(","),
            max_price=args.max_price, min_bedrooms=args.min_bedrooms,
            min_square_feet=args.min_square_feet)
    if args.csv:
        csv_listings(listings)
    else:
        post_listings(listings, args.sheet_name, args.username, args.password)
