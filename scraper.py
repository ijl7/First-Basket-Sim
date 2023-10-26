import nba_scraper.nba_scraper as ns

i = 22100717
while i < 22100718:

    ns.scrape_game([i], data_format='csv', data_dir="2021")
    #ns.scrape_date_range('2023-10-25','2023-10-25',data_format='csv', data_dir='2023')
    #ns.scrape_season(2024,data_format='csv', data_dir='2023')
    i += 1

#22100717
#22101171 on