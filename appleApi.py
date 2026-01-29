import os
import pprint
from dotenv import load_dotenv
load_dotenv()

from pydantic import Json
import requests
import json

def create_apple_music_playlist(developer_token, user_token, playlist_name, playlist_description=""):
    """
    Apple Music API를 통해 새로운 플레이리스트를 생성 후, 생성된 플레이리스트 ID를 반환한다.
    """

    url = "https://api.music.apple.com/v1/me/library/playlists"
    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Music-User-Token": user_token,
        "Content-Type": "application/json"
    }
    payload = {
        "attributes": {
            "name": playlist_name,
            "description": playlist_description
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        data = response.json()
        # 보통 "data" 배열에 새 플레이리스트 정보가 존재
        playlist_id = data["data"][0]["id"]
        print(f"플레이리스트 생성 완료! ID: {playlist_id}")
        return playlist_id
    else:
        print(f"플레이리스트 생성 실패. 상태코드: {response.status_code}")
        print("응답 내용:", response.text)
        return None

def add_tracks_to_playlist(developer_token, user_token, playlist_id, track_ids):
    """
    지정 플레이리스트(playlist_id)에 Apple Music 트랙(track_ids)을 추가한다.
    track_ids: Apple Music 트랙 ID의 리스트
    """
    
    url = f"https://api.music.apple.com/v1/me/library/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Music-User-Token": user_token,
        "Content-Type": "application/json"
    }
    payload = {
        "data": [
            {"id": track_id, "type": "songs"}
            for track_id in track_ids
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 202:
        # Accepted (비동기로 처리됨)
        print(f"트랙 추가 성공! 응답: {response.json()}")
    elif response.status_code == 204:
        print(f"트랙 추가 성공!")
    else:
        print(f"트랙 추가 실패. 상태코드: {response.status_code}")
        print("응답 내용:", response.text)


import requests

def find_apple_music_track_id(dev_token, artist, title, storefront="kr", limit=10):
    """
    주어진 아티스트(artist)와 곡 제목(title)로 Apple Music 카탈로그를 검색하여,
    가장 유사한 트랙의 Apple Music Track ID를 반환한다.
    
    - dev_token: Apple Developer Token (JWT)
    - artist: 가수명 (문자열)
    - title: 곡 제목 (문자열)
    - storefront: 국가 코드 (예: "us", "kr")
    - limit: 검색 결과 최대 개수
    """
    url = f"https://api.music.apple.com/v1/catalog/{storefront}/search"
    headers = {
        "Authorization": f"Bearer {dev_token}"
    }
    params = {
        "l" : "ko-KR",
        "term": f"{title}",  # 검색어 {artist} {title}
        "types": "songs",
        "limit": limit
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return None

    data = response.json() # .get("results", {}).get("songs", {}).get("data", [])

    # 검색 결과가 없거나 구조가 예상치 못하게 나오면 None 반환
    if ("results" not in data or
        "songs" not in data["results"] or
        "data" not in data["results"]["songs"]):
        return None

    songs_data = data["results"]["songs"]["data"]

    # 간단한 문자열 비교 로직 (소문자 변환 후 부분 문자열로 비교)
    artist_lower = artist.lower()
    title_lower = title.lower()

    best_match_id = None
    for song in songs_data:
        attributes = song.get("attributes", {})
        song_title = attributes.get("name", "").lower()
        artist_name = attributes.get("artistName", "").lower()

        print(f"checking: {artist_lower}:{title_lower} == {artist_name}:{song_title}", end="")
        if (artist_lower.replace(" ", "") in artist_name.replace(" ", "")) and (title_lower.replace(" ", "") in song_title.replace(" ", "")):
        # if title_lower.replace(" ", "") in song_title.replace(" ", ""):
            best_match_id = song["id"]
            print(f"          Found!")
            break
        else:
            print("")

    # 검색된 리스트에 없으면 첫 번째 항목의 ID를 반환
    if best_match_id is None:
        best_match_id= songs_data[0]["id"]
        print(f"          not found! {songs_data[0]["attributes"]["artistName"]}:{songs_data[0]["attributes"]["name"]}")
        
    return best_match_id

if __name__ == "__main__":

    DEV_TOKEN = os.environ["APPLE_MUSIC_DEV_TOKEN"]
    USER_TOKEN = os.environ["APPLE_MUSIC_USER_TOKEN"]

    # new_playlist_id = create_apple_music_playlist(
    #     developer_token=DEV_TOKEN,
    #     user_token=USER_TOKEN,
    #     playlist_name="홍가이버가 생성한 플레이리스트(테스트)",
    #     playlist_description="홍가이버가 만든 chatGPT로 생성한 apple music playlist"
    # )

    # 예시 입력: 'Adele' / 'Hello'
    track_id = find_apple_music_track_id(DEV_TOKEN, artist="볼빨간사춘기", title="나의 사춘기에게", storefront="kr")
    print("Track ID:", track_id)
    
    # # 사전에 new_playlist_id가 있다고 가정
    # sample_tracks = [
    #     track_id,
    # ]
    # if new_playlist_id:
    #     add_tracks_to_playlist(DEV_TOKEN, USER_TOKEN, new_playlist_id, sample_tracks)