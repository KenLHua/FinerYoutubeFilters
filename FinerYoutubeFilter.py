import pandas as pd
import numpy as np
import json


from urllib.parse import urlencode
from urllib.request import urlopen
import math
import time
import dateutil



endpoints = {"channel": 'channels', "video": "videos", "vid": "videos"}
#loading bot credentials
def get_credentials():
    try:
        file = open("input/config.json", "r")
    except FileNotFoundError:
        # no credentials found, create a holder file for user to add
        file = open("input/config.json", "a")
        file.write('{ \n "YOUTUBE_API_KEY\": \"INPUT_API_KEY_HERE\" \n}')
        file.close()

    file = open("input/config.json", "r")
    file = json.load(file)
    return file['YOUTUBE_API_KEY']
    

def send_endpoint(api_params, item_type, printable):
    api_endpoint = 'https://www.googleapis.com/youtube/v3/' + item_type
    encoded_params = urlencode(api_params)
    url = f'{api_endpoint}?{encoded_params}'
    if printable:
        print(url)
    
    with urlopen(url) as response:
        return [json.load(response)]


def get_videos_by_channel(api_token, channelId):
    #getting channel's playlist
    api_params = {
        'part' : "contentDetails",
        'key' : api_token,
        'id': channelId,
    }
    response = send_endpoint(api_params, "channels", False)
    uploads_playlist = response[0]['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    #getting uploads
    videoIds = []
    nextPageToken = None
    while(True):
        api_params = {
            'part' : "snippet",
            'key' : api_token,
            'playlist_id': uploads_playlist,
            'maxResult' : "25"
        }
        if(nextPageToken):
            api_params["pageToken"] = nextPageToken
        
        response = send_endpoint(api_params, "playlistItems", False)
        for item in response[0]["items"]:
            videoIds.append(item["snippet"]["resourceId"]["videoId"])
            
        try:
            nextPageToken = response[0]["nextPageToken"]
        except KeyError:
            nextPageToken = None
        if not nextPageToken:
            break
    return videoIds
    
    

def get_channel_by_video(api_token, video_id):
    api_params = {
        'part': "snippet",
        'key': api_token,
        'id' : video_id
    
    }
    response = send_endpoint(api_params, "videos", False)
    channelId = response[0]["items"][0]["snippet"]["channelId"]
    #statistics = response[0]["items"][0]["statistics"]
    return response[0]["items"][0]["snippet"]["channelId"]
def get_video_details(api_token, videoIds):
    video_deets = []
    for i in range(math.ceil(len(videoIds)/50)):

        video_query = ','.join(videoIds[50*i:(50*i)+50])
        api_params = {
            "key": YOUTUBE_API_KEY,
            "id": video_query,
            "part": "statistics, snippet"
        }
        response = send_endpoint(api_params, "videos", False)
        for vid in response[0]["items"]:
            unixTime = int(dateutil.parser.parse(vid["snippet"]["publishedAt"][:10]).timestamp())
            video_deets.append([vid["id"], vid["snippet"]["title"],int(vid["statistics"]["viewCount"]),unixTime])
    return pd.DataFrame(video_deets, columns=["id", "title","views", "unix"])
def unix_timeframe(years=0,months=0,weeks=0,days=0,hours=0):
    return int(time.time()) - (31556926*years + 2629743*months + 604800*weeks + 86400*days + 3600*hours)




# making it a script

if __name__ == '__main__':
    #args = parseargs()
    
    #arguments
    video_id_from_channel = "2SkSXn3mQIk"
    view_threshold = 2000000
    timeframe = unix_timeframe(weeks=2)
    

    YOUTUBE_API_KEY = get_credentials()
    channelId = get_channel_by_video(YOUTUBE_API_KEY, video_id_from_channel)
    videoIds = get_videos_by_channel(YOUTUBE_API_KEY, channelId)
    video_df = get_video_details(YOUTUBE_API_KEY, videoIds)
    
    
    
    # date threshold
    filtered_df = video_df[video_df['unix'] > timeframe]
    
    #views threshold
    filtered_df = filtered_df[video_df["views"] > view_threshold]
    
    #print out remaining videos
    i = 1
    print("In no particular order: \n")
    for ind,row in filtered_df.iterrows():
        print(f'{i}. {row["title"]} | https://www.youtube.com/watch?v=o{row["id"]}')
        i+=1
    