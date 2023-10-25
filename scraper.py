import nba_scraper.nba_scraper as ns

i = 2210189
while i < 22101230:

    ns.scrape_game([i], data_format='csv', data_dir="2021")
    i += 1

#22100717