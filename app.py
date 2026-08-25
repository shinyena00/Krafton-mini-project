{
  "user": {
    "user_id": "user_1024",                   // 문자열 (고유 식별자)
    "nickname": "용인번개",              // 문자열
    "password": "hashed_password_123",   // 문자열 (비밀번호는 암호화 문자열)
    "registered_list": ["errand_5892"],      // 배열 (등록한 심부름 목록)
    "accepteded_list": ["errand_8999"],      // 배열 (수락한 심부름 목록)
    "point": 33                          // 숫자 (포인트/수치)
  },
  "errand": {
    "errand_id": "errand_5892",          // 문자열 또는 숫자
    "title": "편의점에서 감기약 좀 사다주세요", // 문자열
    "image": "https://example.com/img.jpg", // 문자열 (이미지 URL 경로)
    "status": "MATCHED",                 // 문자열 (상태값: REQUESTED, MATCHED, DONE)
    "time": "2026-08-25T15:30:00",       // 문자열 (날짜/시간 ISO 표준)
    "location": "경기도 용인시 수지구",  // 문자열 (주소)
    "reward": 500,                     // 숫자 (보수 금액)
    "register_id": "user_1024",          // 문자열 (등록한 유저 ID)
    "accepter_id": "user_2048"             // 문자열 (수락한 유저 ID, 오타 수정)
  }
}