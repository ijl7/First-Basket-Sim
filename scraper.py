import nba_scraper.nba_scraper as ns

i = 22200714
while i < 22201231:
    nba_df = ns.scrape_game([i])

    ns.scrape_game([i], data_format='csv', data_dir="2022")
    i += 1
