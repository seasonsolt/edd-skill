REFERENCE_IMPLEMENTATION = r'''
from copy import deepcopy

PRICES = {"starter": 1000, "pro": 3000, "enterprise": 10000}
STATUSES = {"trialing", "active", "canceled", "past_due"}
EVENT_TYPES = {"renewal", "upgrade", "downgrade", "cancel", "payment_failed"}


def _round_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator // 2) // denominator


def _validate_subscription(subscription: dict) -> None:
    if not isinstance(subscription, dict):
        raise ValueError("subscription must be a dict")
    if not isinstance(subscription.get("customer_id"), str) or not subscription["customer_id"]:
        raise ValueError("customer_id must be a non-empty string")
    if subscription.get("plan") not in PRICES:
        raise ValueError("unknown plan")
    if not isinstance(subscription.get("seats"), int) or subscription["seats"] <= 0:
        raise ValueError("seats must be positive")
    if subscription.get("status") not in STATUSES:
        raise ValueError("unknown status")
    start = subscription.get("period_start_day")
    end = subscription.get("period_end_day")
    if not isinstance(start, int) or not isinstance(end, int) or end <= start:
        raise ValueError("invalid period")
    for key in ("trial_end_day", "grace_period_end_day"):
        if key in subscription and not isinstance(subscription[key], int):
            raise ValueError(f"{key} must be an int")
    coupon = subscription.get("coupon_percent", 0)
    if not isinstance(coupon, int) or coupon < 0 or coupon > 100:
        raise ValueError("coupon_percent must be 0..100")
    if "last_event_id" in subscription and not isinstance(subscription["last_event_id"], str):
        raise ValueError("last_event_id must be a string")


def _validate_event(event: dict) -> None:
    if not isinstance(event, dict):
        raise ValueError("event must be a dict")
    if not isinstance(event.get("event_id"), str) or not event["event_id"]:
        raise ValueError("event_id must be a non-empty string")
    if event.get("type") not in EVENT_TYPES:
        raise ValueError("unknown event type")
    if not isinstance(event.get("day"), int):
        raise ValueError("day must be an int")
    if event["type"] in {"upgrade", "downgrade"}:
        if event.get("new_plan") not in PRICES:
            raise ValueError("new_plan is required")
        if "new_seats" in event and (not isinstance(event["new_seats"], int) or event["new_seats"] <= 0):
            raise ValueError("new_seats must be positive")
    if "cancel_at_period_end" in event and not isinstance(event["cancel_at_period_end"], bool):
        raise ValueError("cancel_at_period_end must be boolean")


def _result(subscription: dict, amount: int, reason: str, next_subscription: dict) -> dict:
    return {
        "customer_id": subscription["customer_id"],
        "amount_cents": amount,
        "reason": reason,
        "next_subscription": next_subscription,
    }


def _apply_coupon(amount: int, subscription: dict) -> int:
    percent = subscription.get("coupon_percent", 0)
    if amount <= 0 or not percent:
        return amount
    discount = _round_div(amount * percent, 100)
    return amount - discount


def calculate_invoice(subscription: dict, event: dict) -> dict:
    _validate_subscription(subscription)
    _validate_event(event)
    next_subscription = deepcopy(subscription)

    if subscription.get("last_event_id") == event["event_id"]:
        return _result(subscription, 0, "idempotent_replay", next_subscription)

    event_type = event["type"]
    day = event["day"]
    next_subscription["last_event_id"] = event["event_id"]

    if event_type == "payment_failed":
        next_subscription["status"] = "past_due"
        next_subscription["grace_period_end_day"] = day + 7
        return _result(subscription, 0, "payment_failed", next_subscription)

    if event_type == "cancel":
        if event.get("cancel_at_period_end") is True:
            next_subscription["cancel_at_period_end"] = True
            return _result(subscription, 0, "cancel_at_period_end", next_subscription)
        next_subscription["status"] = "canceled"
        return _result(subscription, 0, "cancel_now", next_subscription)

    if subscription["status"] == "canceled":
        return _result(subscription, 0, "canceled_no_charge", next_subscription)

    if event_type == "renewal":
        if subscription["status"] == "trialing" and day < subscription.get("trial_end_day", day):
            return _result(subscription, 0, "trial_no_charge", next_subscription)
        next_subscription["status"] = "active"
        amount = PRICES[subscription["plan"]] * subscription["seats"]
        return _result(subscription, _apply_coupon(amount, subscription), "renewal", next_subscription)

    if event_type == "upgrade":
        old_amount = PRICES[subscription["plan"]] * subscription["seats"]
        new_plan = event["new_plan"]
        new_seats = event.get("new_seats", subscription["seats"])
        new_amount = PRICES[new_plan] * new_seats
        remaining = max(0, subscription["period_end_day"] - day)
        period = subscription["period_end_day"] - subscription["period_start_day"]
        prorated = _round_div(max(0, new_amount - old_amount) * remaining, period)
        next_subscription["plan"] = new_plan
        next_subscription["seats"] = new_seats
        return _result(subscription, _apply_coupon(prorated, subscription), "upgrade_proration", next_subscription)

    if event_type == "downgrade":
        next_subscription["plan"] = event["new_plan"]
        next_subscription["seats"] = event.get("new_seats", subscription["seats"])
        return _result(subscription, 0, "downgrade_no_credit", next_subscription)

    raise ValueError("unsupported event")
'''
