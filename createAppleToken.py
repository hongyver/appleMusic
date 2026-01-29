import jwt
import time
from datetime import datetime, timedelta, timezone

'''
Apple Music API를 사용하기 위한 Developer Token을 생성하는 코드입니다.
'''
def generate_apple_music_token(team_id: str, key_id: str, key_file: str) -> str:
   with open(key_file, 'r') as file:
       private_key = file.read()

   now = datetime.now(timezone.utc)
   six_months = now + timedelta(days=30 * 6)
   
   token = jwt.encode(
       payload={
           'iss': team_id,
           'iat': int(now.timestamp()),
           'exp': int(six_months.timestamp())
       },
       key=private_key,
       algorithm='ES256',
       headers={
           'alg': 'ES256', 
           'kid': key_id,
           'typ': 'JWT'
       }
   )
   
   return token if isinstance(token, str) else token.decode('utf-8')

# 사용 예시
if __name__ == "__main__":
    TEAM_ID = "R2PBZJ465V"       # Apple Developer Account Team ID
    KEY_ID = "6598LR43L7"         # Apple Developer Portal에서 발급받은 Key ID
    PRIVATE_KEY_PATH = "./AuthKey_6598LR43L7.p8"  # 다운로드받은 p8 파일 경로

    dev_token = generate_apple_music_token(
        team_id=TEAM_ID,
        key_id=KEY_ID,
        key_file=PRIVATE_KEY_PATH
    )
    print("Generated Apple Music Developer Token:")
    print(dev_token)
