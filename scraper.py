import nba_scraper.nba_scraper as ns

nba_df = ns.scrape_season(2022)

ns.scrape_season(2022, data_format='csv', data_dir="C:\\Users\\isaac\\FirstBasket\\2022")
