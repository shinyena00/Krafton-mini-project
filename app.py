
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# 1. 사용자 더미 데이터
mock_user = {
    "id": "user_1024",                   # 문자열 (고유 식별자)
    "nickname": "용인번개",               # 문자열
    "password": "hashed_password_123",   # 문자열 (비밀번호는 암호화 문자열)
    "point": 33                          # 숫자 (포인트/수치)
}

# 2. 심부름 더미 데이터
mock_errand = {
    "errand_id": "errand_5892",                   # 문자열 또는 숫자
    "title": "편의점에서 감기약 좀 사다주세요",      # 문자열
    "image": None, # 문자열 (이미지 URL 경로)
    "status": "REQUESTED",                        # 문자열 (상태값: REQUESTED, MATCHED, DONE)
    "time": "2026-08-25T15:30:00",                # 문자열 (날짜/시간 ISO 표준)
    "location": "경기도 용인시 수지구",             # 문자열 (주소)
    "reward": 500,                                # 숫자 (보수 금액)
    "register_id": "user_1024",                   # 문자열 (등록한 유저 ID)
    "accepter_id": None                           # 문자열 (수락 전: None, 수락 후: "user_2048")
}

# 상세 페이지 테스트 라우트
@app.route("/errands/<errand_id>")
def test_detail(errand_id):
    return render_template("errand_detail.html", errand=mock_errand, user=mock_user)

# 수정 페이지 테스트 라우트
@app.route("/errands/<errand_id>/edit")
def test_edit(errand_id):
    return render_template("errand_edit.html", errand=mock_errand, user=mock_user)

# AJAX 동작 테스트용 임시 API
@app.route("/api/errands/<errand_id>/<action>", methods=["POST"])
def test_actions(errand_id, action):
    return jsonify({"result": "success", "message": f"{action} 처리 성공"}), 200

@app.route("/api/errands/<errand_id>", methods=["PUT", "DELETE"])
def test_crud(errand_id):
    return jsonify({"result": "success", "message": "처리 성공"}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)