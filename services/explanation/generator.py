from rag.retriever import retrieve_context


def _next_action(decision):
    if decision == "Reject":
        return (
            "Do not auto-settle. Send the case to fraud investigation or repudiation review "
            "with the listed evidence and allow the customer/document team to respond."
        )
    if decision == "Needs Review":
        return (
            "Route to a human claim reviewer. Verify the flagged documents, policy coverage, "
            "claim history, and any external evidence before settlement."
        )
    return (
        "Claim can proceed to normal settlement controls because required documents and "
        "risk checks did not show material inconsistencies."
    )


def generate_explanation(domain, fraud_score, reasons, decision=None, claim_data=None):
    try:
        decision = decision or "Pending"
        reasons = reasons or ["No material fraud indicators were found during automated checks."]
        context = retrieve_context(domain, reasons=reasons, claim_data=claim_data, top_k=3)

        lines = [
            "Claim review summary",
            f"Domain: {domain}",
            f"Decision: {decision}",
            f"Fraud risk score: {fraud_score}%",
            "",
            "Decision rationale:",
        ]

        if decision == "Approve":
            lines.append(
                "- The claim passed mandatory document, policy, amount, timing, and consistency checks."
            )
            lines.append(
                "- No hard-stop rule was triggered and the combined rule/ML score stayed within approval tolerance."
            )
        elif decision == "Needs Review":
            lines.append(
                "- The claim has one or more risk indicators that are not enough for automatic rejection."
            )
            lines.append(
                "- A reviewer should validate the evidence before payment or denial."
            )
        else:
            lines.append(
                "- A hard-stop rule or very high-risk inconsistency was detected."
            )
            lines.append(
                "- The system is recommending rejection/investigation because the claim facts conflict with policy, amount, or evidence controls."
            )

        lines.extend(["", "Evidence considered:"])
        lines.extend([f"- {reason}" for reason in reasons])

        lines.extend(["", "Relevant review standards:"])
        lines.extend([f"- {doc['title']}: {doc['text']}" for doc in context])

        lines.extend(["", "Recommended next action:", f"- {_next_action(decision)}"])

        lines.extend(
            [
                "",
                "Compliance note:",
                "- This output is decision support, not legal proof of fraud. Final denial should use insurer policy wording, regulator requirements, and human review.",
            ]
        )

        return "\n".join(lines)

    except Exception as exc:
        return f"Explanation error: {exc}"
