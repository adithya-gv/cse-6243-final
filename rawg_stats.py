import requests
from tqdm import tqdm
import re
from runningStats import RunningStats
import pandas as pd
import os

api_key = "2ed0d8539ceb48b5964096a487a016ee"

def get_games(limit: int=2000):
    url = 'https://api.rawg.io/api/games'

    game_set = {}

    i = 1
    progress_bar = tqdm(desc=f"Fetching most popular games", unit=" games")
    while i <= limit / 40:
        params = {
            'key': api_key,
            'page_size': 40,
            'page': i,
            'ordering': "-metacritic",
        }

        response = requests.get(url, params=params)


        if response.status_code == 200:
            games = response.json()
            for game in games["results"]:
                game_pkg = {}
                game_name = game['name']
                game_pkg['duration'] = game['playtime']
                game_pkg['critic_rating'] = game['metacritic']
                game_pkg['peer_rating'] = game['rating']
                game_pkg['popularity'] = game['ratings_count']
                game_set[game_name] = game_pkg
            
                progress_bar.update(1)
            
            if not games["next"]:
                break

            i += 1
        else:
            break
    progress_bar.close()
    print(f"Completed fetching data.")
    
    df = pd.DataFrame.from_dict(game_set, orient='index')

    df = df.reset_index().rename(columns={'index': 'game_name'})

    df.to_csv('game_data.csv', index=False)


def compute_statistics_for_year(year: int, limit: int=2000, output_mode='py'):
    url = 'https://api.rawg.io/api/games'

    playtime = RunningStats()
    critic_score = RunningStats()
    peer_score = RunningStats()
    popularity = RunningStats() 

    game_set = [playtime, critic_score, peer_score, popularity]

    i = 1
    progress_bar = tqdm(desc=f"Fetching games for {year}", unit=" games")
    while i <= limit / 40:
        params = {
            'key': api_key,
            'page_size': 40,
            'page': i,
            'dates': f'{year}-01-01,{year}-12-31'
        }

        response = requests.get(url, params=params)


        if response.status_code == 200:
            games = response.json()
            for game in games["results"]:
                if game['playtime'] is not None:
                    game_set[0].add(float(game['playtime']))

                if game['metacritic'] is not None:
                    game_set[1].add(float(game['metacritic']))

                if game['rating'] is not None:
                    game_set[2].add(float(game['rating']))

                if game['ratings_count'] is not None:
                    game_set[3].add(float(game['ratings_count']))

                progress_bar.update(1)
            
            if not games["next"]:
                break

            i += 1
        else:
            break
    progress_bar.close()
    print(f"Completed fetching data for year {year}.")

    result = [year]
    for item in game_set:
        result.append(item.mean)
        result.append(item.standard_deviation)

    if output_mode == 'csv':
        headers = ['year', 'playtime_mean', 'playtime_std_dev', 'critic_mean', 'critic_std_dev', 'peer_mean', 'peer_std_dev', 'count_mean', 'count_std_dev']
        df = pd.DataFrame([result], columns=headers)
        if os.path.isfile('game_stats.csv'):
            df.to_csv('game_stats.csv', index=False, mode='a')
        else:
            df.to_csv('game_stats.csv', index=False, columns=headers)

        return None
    else:
        return game_set

def get_game_stats(name: str):

    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    slug = clean_name.lower().replace(" ", "-")
    url = f'https://api.rawg.io/api/games/{slug}'

    game_set = {}

    params = {
        'key': api_key,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        game = response.json()
        game_set['name'] = game['name']
        game_set['year'] = int(game['released'].split("-")[0])
        game_set['duration'] = game['playtime']
        game_set['critic_rating'] = game['metacritic']
        game_set['peer_rating'] = game['rating']
        game_set['popularity'] = game['ratings_count']
    
    return game_set