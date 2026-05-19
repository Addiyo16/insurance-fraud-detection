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


def _employee_checklist(domain, decision):
    if decision == "Approve":
        return [
            "Confirm mandatory documents are present and readable.",
            "Proceed with normal settlement authority and audit sampling.",
        ]

    domain_checks = {
        "Vehicle": [
            "Compare RC vehicle number, policy IDV, accident images, police/FIR report, and garage/surveyor estimate.",
            "For minor accidents above 50% of IDV, require independent surveyor confirmation before any settlement.",
            "Check policy start date, report delay, prior claims, salvage/total-loss possibility, and estimate line items.",
        ],
        "Health": [
            "Compare final bill, diagnosis, admission days, discharge summary, ICU use, medicine charges, and hospital network status.",
            "Verify medical necessity when minor diagnosis has planned admission, ICU charges, or high per-day cost.",
            "Check duplicate bills, inflated consumables, unbundled line items, and prior claim frequency.",
        ],
        "Life": [
            "Compare death certificate, policy status, sum assured, cause of death, medical records, and police/FIR report where applicable.",
            "Escalate early-duration and high-sum-assured claims for contestability and underwriting review.",
            "Verify nominee, event date, premium status, prior related claims, and cause-of-death consistency.",
        ],
        "Financial": [
            "Compare KYC, income proof, bank statement, loan document, EMI, tenure, loan amount, and claim amount.",
            "Review debt-to-income, EMI affordability, early claim timing, and full-loan claim behavior.",
            "Validate bank statement cashflow and check for inflated income or altered loan documents.",
        ],
    }
    return domain_checks.get(domain, ["Verify policy, documents, amounts, timing, history, and external evidence."])


def generate_explanation(
    domain,
    fraud_score,
    reasons,
    decision=None,
    claim_data=None,
    rule_score=None,
    ml_score=None,
):
    try:
        decision = decision or "Pending"
        reasons = reasons or ["No material fraud indicators were found during automated checks."]
        context = retrieve_context(domain, reasons=reasons, claim_data=claim_data, top_k=3)

        lines = [
            "Claim review summary",
            f"Domain: {domain}",
            f"Decision: {decision}",
            f"Fraud risk score: {fraud_score}%",
        ]
        if rule_score is not None:
            lines.append(f"Rule/evidence score: {rule_score}%")
        if ml_score is not None:
            lines.append(f"ML anomaly score: {ml_score}%")
        lines.extend(["", "Decision rationale:"])

        if decision == "Approve":
            lines.append(
                "- The claim passed mandatory document, policy, amount, timing, and consistency checks."
            )
            lines.append(
                "- No hard-stop rule was triggered and the combined rule/ML score stayed within approval tolerance."
            )
        elif decision == "Needs Review":
            if any("could not extract" in reason.lower() for reason in reasons):
                lines.append(
                    "- Uploaded documents are not readable enough to verify key claim facts automatically."
                )
                lines.append(
                    "- Do not approve until the document team obtains readable evidence or manually verifies the missing fields."
                )
            else:
                lines.append(
                    "- The claim has one or more risk indicators that are not enough for automatic rejection."
                )
                lines.append(
                    "- A reviewer should validate the evidence before payment or denial."
                )
        else:
            if any("invalid claim details" in reason.lower() for reason in reasons):
                lines.append(
                    "- The claim form conflicts with uploaded document evidence."
                )
                lines.append(
                    "- Treat this as invalid claim detail entry or possible misrepresentation until corrected by verified documents."
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

        lines.extend(["", "Fast employee checklist:"])
        lines.extend([f"- {item}" for item in _employee_checklist(domain, decision)])

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
