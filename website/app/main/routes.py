from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/pricing")
def pricing():
    plans = [
        {
            "id": "free",
            "name": "Free",
            "features": [
                "5 documents/month",
                "Basic summarisation",
                "Email support",
            ],
        },
        {
            "id": "pro",
            "name": "Pro",
            "features": [
                "Unlimited documents",
                "Advanced AI analysis",
                "Entity extraction",
                "Priority support",
            ],
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "features": [
                "Everything in Pro",
                "Custom integrations",
                "Dedicated account manager",
                "SLA guarantee",
            ],
        },
    ]
    return render_template("pricing.html", plans=plans, selected=None)


@main_bp.route("/pricing/select", methods=["POST"])
def pricing_select():
    from flask import request

    plan_id = request.form.get("plan_id")
    plans = [
        {
            "id": "free",
            "name": "Free",
            "features": [
                "5 documents/month",
                "Basic summarisation",
                "Email support",
            ],
        },
        {
            "id": "pro",
            "name": "Pro",
            "features": [
                "Unlimited documents",
                "Advanced AI analysis",
                "Entity extraction",
                "Priority support",
            ],
        },
        {
            "id": "enterprise",
            "name": "Enterprise",
            "features": [
                "Everything in Pro",
                "Custom integrations",
                "Dedicated account manager",
                "SLA guarantee",
            ],
        },
    ]
    # Return only the pricing grid fragment for HTMX requests
    if request.headers.get("HX-Request"):
        return render_template("_pricing_grid.html", plans=plans, selected=plan_id)
    return render_template("pricing.html", plans=plans, selected=plan_id)
