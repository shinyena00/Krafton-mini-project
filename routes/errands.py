
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, jsonify, render_template, request

from routes.auth import get_current_user
from db import users_collection, errands_collection
from image_utils import save_uploaded_image, delete_uploaded_image


errands = Blueprint("errands", __name__)


def remaining_time_parts(deadline_at):
    if deadline_at is None:
        return None

    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(
            tzinfo=timezone.utc
        )

    now = datetime.now(timezone.utc)

    remaining_seconds = int(
        (deadline_at - now).total_seconds()
    )

    if remaining_seconds <= 0:
        return None


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

    return days, hours, minutes


def format_remaining_time(deadline_at):
    if deadline_at is None:
        return "무기한"

    parts = remaining_time_parts(deadline_at)

    if parts is None:
        return "마감"

    days, hours, minutes = parts
    labels = []

    if days > 0:
        labels.append(f"{days}일")

    if hours > 0:
        labels.append(f"{hours}시")

    if minutes > 0:
        labels.append(f"{minutes}분")

    return " ".join(labels) + "까지"


def not_expired_conditions():
    return [
        {"deadline_at": None},
        {"deadline_at": {"$exists": False}},
        {"deadline_at": {"$gt": datetime.now(timezone.utc)}}
    ]


def is_expired(errand):
    deadline_at = errand.get("deadline_at")

    if deadline_at is None:
        return False

    if deadline_at.tzinfo is None:
        deadline_at = deadline_at.replace(
            tzinfo=timezone.utc
        )

    return deadline_at <= datetime.now(timezone.utc)


def set_display_time(errand):
    if "deadline_at" in errand:
        errand["time"] = format_remaining_time(
            errand["deadline_at"]
        )
    else:
        errand["time"] = errand.get(
            "time",
            "기한 미정"
        )

    return errand


@errands.route("/")
def home():
    user = get_current_user()

    errand_list = list(
        errands_collection.find({
            "status": "OPEN",
            "$or": not_expired_conditions()
        }).sort(
            "created_at",
            -1
        )
    )

    for errand in errand_list:
        set_display_time(errand)

    return render_template(
        "index.html",
        errands=errand_list,
        user=user
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

    image_url, image_error = save_uploaded_image(
        request.files.get("image")
    )

    if image_error:
        return jsonify({
            "result": "fail",
            "message": image_error
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

    charge_result = users_collection.update_one(
        {
            "_id": user["_id"],
            "point": {"$gte": reward}
        },
        {
            "$inc": {"point": -reward}
        }
    )

    if charge_result.modified_count == 0:
        return jsonify({
            "result": "fail",
            "message": "보유 포인트가 부족합니다."
        })

    errand = {
        "requester_id": user["_id"],
        "worker_id": None,
        "title": title_receive,
        "description": description_receive,
        "location": place_receive,
        "deadline_at": deadline_at,
        "reward": reward,
        "image": image_url,
        "status": "OPEN",
        "created_at": created_at
    }

    try:
        insert_result = errands_collection.insert_one(errand)
    except Exception:
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$inc": {"point": reward}}
        )

        delete_uploaded_image(image_url)

        return jsonify({
            "result": "fail",
            "message": "등록 중 오류가 발생했습니다."
        })

    return jsonify({
        "result": "success",
        "errand_id": str(insert_result.inserted_id)
    })


@errands.route("/errands/<errand_id>")
def detail(errand_id):
    try:
        object_id = ObjectId(errand_id)
    except InvalidId:
        return "잘못된 심부름 ID입니다."

    errand = errands_collection.find_one({
        "_id": object_id
    })

    if not errand:
        return "존재하지 않는 심부름입니다."

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
        requester=requester,
        expired=is_expired(errand)
    )


@errands.route("/errands/<errand_id>/edit")
def edit_errand(errand_id):
    user = get_current_user()

    if not user:
        return """
        <script>
            alert("로그인을 먼저 진행해주세요.\\n확인을 누르면 로그인 창으로 이동합니다.");
            window.location.href = "/login";
        </script>
        """

    try:
        object_id = ObjectId(errand_id)
    except InvalidId:
        return "잘못된 심부름 ID입니다."

    errand = errands_collection.find_one({
        "_id": object_id
    })

    if not errand:
        return "존재하지 않는 심부름입니다."

    if errand.get("requester_id") != user["_id"]:
        return "수정 권한이 없습니다."

    if errand.get("status") != "OPEN":
        return "수락된 이후에는 수정할 수 없습니다."

    deadline_at = errand.get("deadline_at")

    no_limit = deadline_at is None
    parts = remaining_time_parts(deadline_at)
    deadline_days, deadline_hours, deadline_minutes = parts or (0, 0, 0)

    return render_template(
        "errand_edit.html",
        errand=errand,
        user=user,
        deadline_days=deadline_days,
        deadline_hours=deadline_hours,
        deadline_minutes=deadline_minutes,
        no_limit=no_limit
    )


@errands.route("/api/errands/<errand_id>", methods=["PUT"])
def update_errand(errand_id):
    user = get_current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "로그인이 필요합니다."
        })

    try:
        object_id = ObjectId(errand_id)
    except InvalidId:
        return jsonify({
            "success": False,
            "message": "잘못된 심부름 ID입니다."
        })

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    location = request.form.get("location", "").strip()

    if not all([title, description, location]):
        return jsonify({
            "success": False,
            "message": "모든 항목을 입력해주세요."
        })

    try:
        reward = int(request.form.get("reward"))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "포인트는 숫자로 입력해주세요."
        })

    if reward <= 0:
        return jsonify({
            "success": False,
            "message": "포인트는 1 이상이어야 합니다."
        })

    no_limit = request.form.get("no_limit", "false").lower() == "true"

    try:
        deadline_days = int(request.form.get("deadline_days", 0))
        deadline_hours = int(request.form.get("deadline_hours", 0))
        deadline_minutes = int(request.form.get("deadline_minutes", 0))
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "기한은 숫자로 입력해주세요."
        })

    if deadline_days < 0:
        return jsonify({
            "success": False,
            "message": "일은 0 이상으로 입력해주세요."
        })

    if deadline_hours < 0 or deadline_hours > 23:
        return jsonify({
            "success": False,
            "message": "시간은 0부터 23 사이로 입력해주세요."
        })

    if deadline_minutes < 0 or deadline_minutes > 59:
        return jsonify({
            "success": False,
            "message": "분은 0부터 59 사이로 입력해주세요."
        })

    if (
        not no_limit
        and deadline_days == 0
        and deadline_hours == 0
        and deadline_minutes == 0
    ):
        return jsonify({
            "success": False,
            "message": "기한을 1분 이상 입력해주세요."
        })

    if no_limit:
        deadline_at = None
    else:
        deadline_at = datetime.now(timezone.utc) + timedelta(
            days=deadline_days,
            hours=deadline_hours,
            minutes=deadline_minutes
        )

    new_image_url, image_error = save_uploaded_image(
        request.files.get("image")
    )

    if image_error:
        return jsonify({
            "success": False,
            "message": image_error
        })

    existing = errands_collection.find_one({
        "_id": object_id,
        "requester_id": user["_id"],
        "status": "OPEN"
    })

    if not existing:
        delete_uploaded_image(new_image_url)

        return jsonify({
            "success": False,
            "message": "수정 권한이 없거나 이미 처리된 심부름입니다."
        })

    reward_diff = reward - existing["reward"]

    if reward_diff != 0:
        point_filter = {"_id": user["_id"]}

        if reward_diff > 0:
            point_filter["point"] = {"$gte": reward_diff}

        point_result = users_collection.update_one(
            point_filter,
            {"$inc": {"point": -reward_diff}}
        )

        if reward_diff > 0 and point_result.modified_count == 0:
            return jsonify({
                "success": False,
                "message": "포인트가 부족합니다."
            })

    update_fields = {
        "title": title,
        "description": description,
        "location": location,
        "reward": reward,
        "deadline_at": deadline_at
    }

    if new_image_url:
        update_fields["image"] = new_image_url

    result = errands_collection.update_one(
        {
            "_id": object_id,
            "requester_id": user["_id"],
            "status": "OPEN"
        },
        {
            "$set": update_fields
        }
    )

    if result.matched_count == 0:
        if reward_diff != 0:
            users_collection.update_one(
                {"_id": user["_id"]},
                {"$inc": {"point": reward_diff}}
            )

        delete_uploaded_image(new_image_url)

        return jsonify({
            "success": False,
            "message": "수정 권한이 없거나 이미 처리된 심부름입니다."
        })

    if new_image_url and existing.get("image"):
        delete_uploaded_image(existing["image"])

    return jsonify({
        "success": True,
        "message": "심부름이 수정되었습니다."
    })
