import nba_scraper.nba_scraper as ns

i = 22400617
while i < 22400618:
    try:
        ns.scrape_game([i], data_format='csv', data_dir="2024")
    except:
        print('Game ' + str(i) + ' not added.')
        i += 1
        continue
    #ns.scrape_date_range('2023-10-30','2023-10-30',data_format='csv', data_dir='2023')
    #ns.scrape_season(2024,data_format='csv', data_dir='2023')
    i += 1

#Missing Files
#22100717, 22101171, 22200674, 22200714, 22300425, 22300589, 22301130, 22400495
#Broken Files
#22100773