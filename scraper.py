import nba_scraper.nba_scraper as ns

i = 42200405
while i < 42200406:
    try:
        ns.scrape_game([i], data_format='csv', data_dir="2022 PLAY")
    except:
        i += 1
        continue
    #ns.scrape_date_range('2023-10-25','2023-10-25',data_format='csv', data_dir='2023')
    #ns.scrape_season(2024,data_format='csv', data_dir='2023')
    i += 1

#Missing Files
#22100717, 22101171, 22200674, 22200714
#Broken Files
#22100773