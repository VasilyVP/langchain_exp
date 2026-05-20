def collect_decisions(interrupt_payload: dict) -> list[dict]:
    action_requests = interrupt_payload.get("action_requests", [])
    review_configs = interrupt_payload.get("review_configs", [])
    config_map = {cfg.get("action_name"): cfg for cfg in review_configs}

    decisions: list[dict] = []
    for action in action_requests:
        action_name = action.get("name", "unknown")
        allowed_decisions = config_map.get(action_name, {}).get(
            "allowed_decisions", ["approve", "reject"]
        )

        print(f"Approval required for tool: {action_name}")
        print(f"Arguments: {action.get('args', {})}")
        print(f"Allowed decisions: {allowed_decisions}")

        decision = (
            input(f"Enter decision for {action_name} ({'/'.join(allowed_decisions)}): ")
            .strip()
            .lower()
        )

        if decision not in allowed_decisions:
            print("Invalid decision. Defaulting to 'reject'.")
            decision = "reject"

        decisions.append({"type": decision})

    return decisions
