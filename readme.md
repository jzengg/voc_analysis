# Summary
Data about the contestants and coaches from each season of Voice of China and Sing China collected from their wiki pages.

## Data
### season_overall_results
each of the contestants that were selected by a coach and how far they got in the season (won, eliminated in playoffs). 

#### Contestant ID
We can uniquely identify a contestant with a combination of their english name, chinese name and the season number. 
Data about a contestant can be compared between season_overall_results and blind_auditions using the
contestant_id which follows this format:

`english_name:<ENGLISH_NAME>|chinese_name:<CHINESE_NAME>|season_num:<SEASON_NUM>`

For example, from season 1, we would have id

`english_name:Kim Ji-mun|chinese_name:金志文|season_num:1`


#### Ranking category
Each contestant is categorized by far how far they made it in the season. 
This is captured by the rank_category (won the season, was eliminated during the playoffs) 
and rank_value (from 0..n where lower value means they survived longer in the season). 
Each season's format is slightly different, so the category name may not be completely accurate,
but the rank_value should still be comparable between seasons i.e. a rank value of 3 in season 3 
should still be considered making it farther than rank value of 5 in season 1

### blind_auditions
coaches that turned for each contestant and which coach a contestant ultimately joined

### coaches
listing of all the coaches that have been on the show and which coaches were on which seasons

### all_data
aggregates the coach, season overall results and blind auditions into one data set

### wiki_dump
dump of the html for all the wiki pages that can be used to do processing offline

## Wiki
Example wiki pages 

https://en.wikipedia.org/wiki/The_Voice_of_China_(season_1)

https://en.wikipedia.org/wiki/Sing!_China_(season_1)