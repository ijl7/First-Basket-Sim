import nba_scraper.nba_scraper as ns

nba_df = ns.scrape_game([21800002, 21800003])

ns.scrape_game([21800002, 21800003], data_format='csv', data_dir="2022")
