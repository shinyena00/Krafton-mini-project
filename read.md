| 단계 (상태 전이) | HTTP / Endpoint | DB 업데이트 조건 & 내용 (Atomic) | 프론트엔드 (AJAX 및 DOM 변경) |
| :--- | :--- | :--- | :--- |
| **1. 심부름 수락**<br>`OPEN` → `ACCEPTED` | `POST`<br>`/api/errands/<id>/accept` | **조건:** status == "OPEN", register_id != user_id<br>**변경:** status = "ACCEPTED", accepter_id = user_id | • **성공 시:** 버튼을 '완료 요청'으로 변경<br>• **실패 시:** "이미 수락된 심부름입니다" 알림 후 버튼 비활성화 |
| **2. 수락 취소**<br>`ACCEPTED` → `OPEN` | `POST`<br>`/api/errands/<id>/cancel-accept` | **조건:** status == "ACCEPTED", accepter_id == user_id<br>**변경:** status = "OPEN", accepter_id = null | • **성공 시:** 버튼을 다시 '수락하기'로 변경 |
| **3. 완료 요청**<br>`ACCEPTED` → `WAITING_CONFIRM` | `POST`<br>`/api/errands/<id>/request-complete` | **조건:** status == "ACCEPTED", accepter_id == user_id<br>**변경:** status = "WAITING_CONFIRM" | • **성공 시:** 버튼을 '승인 대기 중' 상태로 변경 |
| **4. 완료 승인**<br>`WAITING_CONFIRM` → `COMPLETED` | `POST`<br>`/api/errands/<id>/confirm-complete` | **조건:** status == "WAITING_CONFIRM", register_id == user_id<br>**변경:** status = "COMPLETED"<br>**부가:** 작성자/수행자 point 갱신 | • **성공 시:** '수행 완료' 배지 표시 및 관련 유저의 point 반영 |
