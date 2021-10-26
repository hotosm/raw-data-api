from osm_stats import Mapathon
from configparser import ConfigParser

# Reading database credentials from config.txt
config = ConfigParser()
config.read("config.txt")

my_mapathon = Mapathon(dict(config.items("INSIGHTS_PG")),{
    "project_ids": [
        11224, 10042, 9906, 1381, 11203, 10681, 8055, 8732, 11193, 7305, 11210,
        10985, 10988, 11190, 6658, 5644, 10913, 6495, 4229
    ],
    "fromTimestamp":
    "2021-08-27T9:00:00",
    "toTimestamp":
    "2021-08-27T11:00:00",
    "hashtags": ["mapandchathour2021"]
})
summary_report = my_mapathon.get_summary()
detailed_report = my_mapathon.get_detailed_report()
print("Summary report \n")

print(summary_report)
print("\n Detailed report \n")
print(detailed_report)
