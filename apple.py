import argparse
from ast import arg
import os
from dotenv import load_dotenv
from pydantic_core import ArgsKwargs
load_dotenv("../.env")

import re
# import json
from openai import OpenAI

import tiktoken

from appleApi import create_apple_music_playlist, add_tracks_to_playlist, find_apple_music_track_id

client = OpenAI(
    api_key = os.environ["OPENAI_API_KEY"]
)

def count_chat_tokens(messages, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    tokens_per_message = 3
    total_tokens = 0

    # 메시지가 문자열일 때 처리
    if isinstance(messages, str):
        return len(encoding.encode(messages))

    # 메시지가 리스트일 때 처리
    for message in messages:
        if isinstance(message, dict):
            total_tokens += tokens_per_message
            for key, value in message.items():
                total_tokens += len(encoding.encode(str(value)))

    return total_tokens

def extract_songs(text):
    # 정규 표현식을 사용하여 [가수이름][노래제목][내용] 패턴 추출
    # print(text)
    pattern = r'\[([^\]]+)\]\[([^\]]+)\]\[([^\]]+)\]'
    matches = re.findall(pattern, text)
    # print(matches)
    # 리스트 형태로 변환
    return [list(match) for match in matches]

def get_play_list(text, count=5):
    
    if text == "":
        print("텍스트가 입력되지 않았습니다.")
        return
    
    prompt = f"""
다음 TEXT의 분위기에 맞는 노래를 {count}곡 추천.
[가수이름][노래제목][내용] 형식으로 입력해주세요.
TEXT : {text}
"""

    message = [
        {
            "role": "system", "content": "당신은 대중 음악 전문가입니다. 모든 노래의 제목과 부른 가수의 이름에 대해서 정확히 알고 있습니다.",
            "role": "user", "content": prompt
        }
    ]

    res = client.chat.completions.create(
        model="gpt-4o",
        messages=message,
        temperature=1,  # 창의성과 답변의 일관성을 조절
        top_p=1.0          # 확률 분포 기반 샘플링 설정        
    )

    usd_to_krw = 1350
    input_cost_per_1k_tokens_usd = 0.001
    output_cost_per_1k_tokens_usd = 0.0015
    
    input_tokens = count_chat_tokens(message)
    output_tokens = count_chat_tokens(res.choices[0].message.content)
    
    input_cost_usd = (input_tokens / 1000) * input_cost_per_1k_tokens_usd
    output_cost_usd = (output_tokens / 1000) * output_cost_per_1k_tokens_usd
    
    total_cost_usd = input_cost_usd + output_cost_usd
    total_cost_krw = total_cost_usd * usd_to_krw

    # 결과 출력
    print(f"🔢 input 토큰 수: {input_tokens}개")
    print(f"🔢 output 토큰 수: {output_tokens}개")
    print(f"💲 입력 요금 (USD): ${input_cost_usd:.4f}")
    print(f"💲 출력 요금 (USD): ${output_cost_usd:.4f}")
    print(f"💲 총 요금 (USD): ${total_cost_usd:.4f}")
    print(f"💰 총 요금 (KRW): ￦{total_cost_krw:.2f}")

    playlist = extract_songs(res.choices[0].message.content)

    return playlist



if __name__ == "__main__":

    play_list = []
    
    DEV_TOKEN = os.environ["APPLE_MUSIC_DEV_TOKEN"]
    USER_TOKEN = os.environ["APPLE_MUSIC_USER_TOKEN"]

    argparse = argparse.ArgumentParser()
    argparse.add_argument("-p", required=True, help="Text for generating play list")
    argparse.add_argument("-n", default=5, help="Number of songs to be generated")
    args = argparse.parse_args()

    songs = get_play_list(args.p,args.n)

    print("ChatGTP 에게 추천받은 노래")    
    for song in songs:
        print(f"가수: {song[0]}, 노래: {song[1]}, 내용: {song[2]}")
    
    for song in songs:
        track_id = find_apple_music_track_id(DEV_TOKEN, artist=song[0], title=song[1], storefront="kr")
        if track_id:
            play_list.append(track_id)
            # print(f"가수: {song['artist']}, 노래: {song['title']},  Track ID: {track_id} - 추가됨")
        # else:
            # print(f"가수: {song['artist']}, 노래: {song['title']}, Track ID: {track_id}")
            

    if(len(play_list) == 0):
        print("추천된 노래가 없습니다.")
        exit(0)
        
    new_playlist_id = create_apple_music_playlist(
        developer_token=DEV_TOKEN,
        user_token=USER_TOKEN,
        playlist_name=args.p,
        playlist_description="홍가이버가 만든 chatGPT로 생성한 apple music playlist"
    )
    
    if new_playlist_id:
        add_tracks_to_playlist(DEV_TOKEN, USER_TOKEN, new_playlist_id, play_list)
        
# prompt        
# 다음 TEXT의 분위기에 맞는 노래를 {count}곡 추천하고 싶습니다.
# 반드시 실제로 존재하는 노래를 선정해야 하며, 노래 제목과 가수 이름이 정확히 일치해야 합니다.
# 그리고 가수의 이름이 영어이면 한글로 변경해주세요.

# - 출력 양식:
#     [
#       {{
#         "title": "<노래 제목>",
#         "artist": "<해당 노래를 부른 정확한 가수 이름>"
#       }},
#       ...
#     ]

# - 조건:
#   1. 반드시는 JSON 배열 형태로만 출력
#   2. "title"은 노래 제목, "artist"는 해당 노래의 정확한 가수 이름
#   3. 잘못된 매칭(예: 다른 가수 이름과 곡을 섞는 것)을 하지 않기
#   4. 곡 제목과 가수 이름이 실제 존재해야 함

# TEXT: {text}
#                 """        