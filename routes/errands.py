# 심부름 CRUD 및 화면 조회(목록/등록/상세/수정)만 담당한다.
# 상태 전이(수락/완료 확정/취소)는 routes/status.py에서 담당하며, 여기에 추가하지 않는다.

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, render_template, request

from routes.auth import get_current_user
from db import users_collection, errands_collection


errands = Blueprint("errands", __name__)


def format_remaining_time(deadline_at):
    if deadline_at is None:
        return "무기한"

    # PyMongo에서 읽은 시간이 시간대 정보가 없으면 UTC로 처리
    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(
            tzinfo=timezone.utc
        )

    now = datetime.now(timezone.utc)

    remaining_seconds = int(
        (deadline_at - now).total_seconds()
    )

    if remaining_seconds <= 0:
        return "마감"

    # 남은 초를 분 단위로 올림
    total_minutes = (
        remaining_seconds + 59
    ) // 60

    days, remaining_minutes = divmod(
        total_minutes,
        24 * 60
    )

    hours, minutes = divmod(
        remaining_minutes,
        60
    )

    parts = []

    if days > 0:
        parts.append(f"{days}일")

    if hours > 0:
        parts.append(f"{hours}시간")

    if minutes > 0:
        parts.append(f"{minutes}분")

    return " ".join(parts) + " 남음"


def set_display_time(errand):
    if "deadline_at" in errand:
        errand["time"] = format_remaining_time(
            errand["deadline_at"]
        )
    else:
        # 기존 테스트 데이터 호환용
        errand["time"] = errand.get(
            "time",
            "기한 미정"
        )

    return errand


@errands.route("/")
def home():
    errand_list = list(
        errands_collection.find({
            "status": "OPEN"
        }).sort(
            "created_at",
            -1
        )
    )

    for errand in errand_list:
        set_display_time(errand)

    return render_template(
        "index.html",
        errands=errand_list
    )


@errands.route("/new_errand")
def new_errand():
    user = get_current_user()

    if not user:
        return """
        <script>
            alert("로그인을 먼저 진행해주세요.\\n확인을 누르면 로그인 창으로 이동합니다.");
            window.location.href = "/login";
        </script>
        """

    return render_template(
        "new_errand.html",
        user=user
    )


@errands.route("/errand", methods=["POST"])
def post_errand():
    user = get_current_user()

    if not user:
        return jsonify({
            "result": "fail",
            "message": "로그인이 필요합니다."
        })

    title_receive = request.form.get(
        "title_give",
        ""
    ).strip()

    description_receive = request.form.get(
        "description_give",
        ""
    ).strip()

    place_receive = request.form.get(
        "place_give",
        ""
    ).strip()

    point_receive = request.form.get(
        "point_give",
        ""
    ).strip()

    deadline_days_receive = request.form.get(
        "deadline_days_give",
        "0"
    ).strip()

    deadline_hours_receive = request.form.get(
        "deadline_hours_give",
        "0"
    ).strip()

    deadline_minutes_receive = request.form.get(
        "deadline_minutes_give",
        "0"
    ).strip()

    no_limit_receive = request.form.get(
        "no_limit_give",
        "false"
    ).lower()

    no_limit = no_limit_receive == "true"

    if not all([
        title_receive,
        description_receive,
        place_receive,
        point_receive
    ]):
        return jsonify({
            "result": "fail",
            "message": "모든 항목을 입력해주세요."
        })

    try:
        reward = int(point_receive)
    except ValueError:
        return jsonify({
            "result": "fail",
            "message": "포인트는 숫자로 입력해주세요."
        })

    if reward <= 0:
        return jsonify({
            "result": "fail",
            "message": "포인트는 1 이상이어야 합니다."
        })

    try:
        deadline_days = int(
            deadline_days_receive or 0
        )

        deadline_hours = int(
            deadline_hours_receive or 0
        )

        deadline_minutes = int(
            deadline_minutes_receive or 0
        )
    except ValueError:
        return jsonify({
            "result": "fail",
            "message": "기한은 숫자로 입력해주세요."
        })

    if deadline_days < 0:
        return jsonify({
            "result": "fail",
            "message": "일은 0 이상으로 입력해주세요."
        })

    if (
        deadline_hours < 0
        or deadline_hours > 23
    ):
        return jsonify({
            "result": "fail",
            "message": "시간은 0부터 23 사이로 입력해주세요."
        })

    if (
        deadline_minutes < 0
        or deadline_minutes > 59
    ):
        return jsonify({
            "result": "fail",
            "message": "분은 0부터 59 사이로 입력해주세요."
        })

    if (
        not no_limit
        and deadline_days == 0
        and deadline_hours == 0
        and deadline_minutes == 0
    ):
        return jsonify({
            "result": "fail",
            "message": "기한을 1분 이상 입력해주세요."
        })

    created_at = datetime.now(
        timezone.utc
    )

    if no_limit:
        deadline_at = None
    else:
        deadline_at = created_at + timedelta(
            days=deadline_days,
            hours=deadline_hours,
            minutes=deadline_minutes
        )

    errand = {
        "requester_id": user["_id"],
        "worker_id": None,
        "title": title_receive,
        "description": description_receive,
        "location": place_receive,
        "deadline_at": deadline_at,
        "reward": reward,
        "status": "OPEN",
        "created_at": created_at
    }

    result = errands_collection.insert_one(errand)

    return jsonify({
        "result": "success",
        "errand_id": str(result.inserted_id)
    })


@errands.route("/errand", methods=["GET"])
def search_errand():
    result = list(
        errands_collection.find(
            {},
            {
                "_id": 0,
                "requester_id": 0,
                "worker_id": 0,
                "created_at": 0,
                "deadline_at": 0
            }
        )
    )

    return jsonify({
        "point": result
    })


@errands.route("/errands/<errand_id>")
def detail(errand_id):
    try:
        object_id = ObjectId(errand_id)
    except InvalidId:
        return "잘못된 심부름 ID입니다.", 404

    errand = errands_collection.find_one({
        "_id": object_id
    })

    if not errand:
        return "존재하지 않는 심부름입니다.", 404

    set_display_time(errand)

    user = get_current_user()
    requester = None

    requester_id = errand.get(
        "requester_id"
    )

    if requester_id:
        requester = users_collection.find_one({
            "_id": requester_id
        })

    return render_template(
        "errand_detail.html",
        errand=errand,
        user=user,
        requester=requester
    )
