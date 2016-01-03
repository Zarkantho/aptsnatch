from bs4 import BeautifulSoup
from urllib2 import urlopen
import gspread
import sys
import scrapers

# IMPORTANT: Set these to your Google acct username and password
GOOGLE_USER = "username"
GOOGLE_PW = "password"

# *** Set the search criteria ***
MAX_PRICE = 5000
# Must have this many bedrooms-
MIN_BDRM = 1
# -OR have at least this square footage
MIN_SQFT = 800
# Search terms
KEYWORDS = ("tenleytown",)

def post_listings(listings):
    google = gspread.login(GOOGLE_USER, GOOGLE_PW)
    spread = google.open("Snatched Apartments").sheet1

    # Retrieve listings already in the spreadsheet, and use these to
    # filter current <listings> to prevent duplicates. We consider two
    # listings different from each other if their links don't match
    cur_listings = spread.col_values(2)
    listings = [l for l in listings if l[1] not in cur_listings]

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

def csv_listings(listings):
    print ",".join(['title', 'href', 'price', 'date', 'address', 'bdrm', 'sqft', 'mailto'])
    for listing in listings:
        bdrm = listing.bdrm if listing.bdrm else "could not find bedroom count"
        sqft = listing.sqft if listing.sqft else "could not find sqft count"
        price = listing.price if listing.price else "could not find price"
        address = listing.address if listing.address else "could not find location"
        mailto = listing.mailto if listing.mailto else "could not find email address"
        print ",".join([listing.title, listing.href, price, listing.date, address, bdrm, sqft, mailto])

if __name__ == '__main__':
    root_url = "http://washingtondc.craigslist.org"
    scrape_funcs = [f for f in dir(scrapers) if f.startswith('scrape_')]
    all_scraped = [getattr(scrapers,scrape_func)(root_url=root_url, keywords=KEYWORDS,
        max_price=MAX_PRICE, min_bedrooms=MIN_BDRM, min_square_feet=MIN_SQFT) for scrape_func in
        scrape_funcs]
    listings = []
    for scraped in all_scraped:
        listings.extend(scraped)

    csv_listings(listings)
