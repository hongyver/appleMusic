import time
from appleApi import create_apple_music_playlist, add_tracks_to_playlist, find_apple_music_track_id
from apple import get_play_list

from flask import Flask, render_template, request, jsonify, session, Response

import threading
import os

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder="static")

app.secret_key = "hongyver-makes-apple-music-playlist"

DEV_TOKEN = os.environ["APPLE_MUSIC_DEV_TOKEN"]

@app.route("/")
def index():
    return render_template("index.html", dev_token=DEV_TOKEN)

@app.route("/receive_token", methods=["POST"])
def receive_token():
    data = request.get_json()
    user_token = data.get("userToken")
    session["userToken"] = user_token
    return jsonify({"status": "ok"})

current_status = ""

def status_change(status):
    global current_status
    print("상태: ", current_status)
    current_status = status
    
@app.route("/make_playlist", methods=["POST"])
def make_playlist():    
    data = request.get_json()
    prompt = data.get("prompt")
    count = data.get("count")

    if not prompt:
        print("텍스트가 입력되지 않았습니다.")
        return jsonify({"status": "fail", "result": "텍스트가 입력되지 않았습니다."})
    
    if "userToken" not in session:
        return jsonify({"status": "nousertoken", "result": "사용자 토큰이 없습니다."}) 
    
    user_token = session["userToken"]
    
    status_change("request")
    
    print(f"ChatGTP 에 {prompt} {count}곡 요청중....")
    songs = get_play_list(prompt, count)

    print("ChatGTP 에게 추천받은 노래")    
    for song in songs:
        print(f"가수: {song[0]}, 노래: {song[1]}, 내용: {song[2]}")
    
    status_change("find")
    
    play_list = []
    for song in songs:
        track_id = find_apple_music_track_id(DEV_TOKEN, artist=song[0], title=song[1], storefront="kr")
        if track_id:
            play_list.append(track_id)
            # print(f"가수: {song['artist']}, 노래: {song['title']},  Track ID: {track_id} - 추가됨")
        # else:
            # print(f"가수: {song['artist']}, 노래: {song['title']}, Track ID: {track_id}")
            
    if(len(play_list) == 0):
        status_change("")
        print("추천된 노래가 없습니다.")
        return jsonify({"status": "nolist", "result": "추천된 노래가 없습니다."})
    
    status_change("make")
    
    new_playlist_id = create_apple_music_playlist(
        developer_token=DEV_TOKEN,
        user_token=user_token,
        playlist_name=prompt,
        playlist_description="홍가이버가 만든 chatGPT로 생성한 apple music playlist"
    )
    
    if new_playlist_id:
        add_tracks_to_playlist(DEV_TOKEN, user_token, new_playlist_id, play_list)
    else:
        return jsonify({"status": "fail", "result": "플레이리스트 생성에 실패했습니다."})

    status_change("")

    return jsonify({"status": "ok", "result": new_playlist_id})


# SSE status
@app.route("/status")
def status():
    def event_stream():
        last_status = None
        while True:
            if current_status != last_status:
                last_status = current_status
                yield f"data: {current_status}\n\n"
            time.sleep(1)
    return Response(event_stream(), content_type="text/event-stream")

threading.Thread(target=status_change, daemon=True).start()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9876)
