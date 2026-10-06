

import streamlit as st
import altair as alt
from dotenv import load_dotenv



from agents.orchestrator import investigate_transaction
from automation import dispatch_case_event



from database import (

    initialize_database,

    save_investigation,

    get_investigations,

    update_review_status,
    save_review_workflow,
    case_requires_human_review,

    initialize_audit_table,

    record_audit_event,

    get_audit_events,

)



load_dotenv()


# --------------------------------------------------

# 1. Initialization

# --------------------------------------------------



st.set_page_config(

    page_title="Banking Fraud Investigation",

    page_icon="🏦",

    layout="wide",

)



initialize_database()

initialize_audit_table()



st.title("🏦 Banking Fraud Investigation System")

st.caption("Governed Agentic AI | Fraud Investigation Prototype")



st.info(

    "Demonstration only. Risk scores use illustrative rules, "

    "not a validated fraud detection model."

)



# --------------------------------------------------
# Dashboard overview
# --------------------------------------------------

st.divider()
st.subheader("Fraud Investigation Dashboard")

dashboard_cases = get_investigations(limit=100)

total_cases = len(dashboard_cases)
high_risk_cases = sum(
    1 for case in dashboard_cases
    if str(case.get("risk_level", "")).upper() == "HIGH"
)
pending_human_review = sum(
    1 for case in dashboard_cases
    if bool(case.get("human_review_required", False))
    and case.get("review_status", "Pending Review") != "Closed After Review"
)
open_cases = sum(
    1 for case in dashboard_cases
    if case.get("review_status", "Pending Review") != "Closed After Review"
)

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("Total Cases", total_cases)
metric2.metric("High-Risk Cases", high_risk_cases)
metric3.metric("Pending Human Review", pending_human_review)
metric4.metric("Open Investigations", open_cases)

if dashboard_cases:
    st.markdown("#### Risk Distribution")
    risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "OTHER": 0}
    for case in dashboard_cases:
        level = str(case.get("risk_level", "")).upper()
        if level in risk_counts:
            risk_counts[level] += 1
        else:
            risk_counts["OTHER"] += 1

    risk_chart_data = [
        {"Risk Level": level, "Cases": count}
        for level, count in risk_counts.items()
        if count > 0
    ]
    risk_chart = (
        alt.Chart(alt.Data(values=risk_chart_data))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            y=alt.Y("Risk Level:N", sort=["HIGH", "MEDIUM", "LOW", "OTHER"], title=None),
            x=alt.X("Cases:Q", title="Number of cases", axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("Risk Level:N"), alt.Tooltip("Cases:Q")],
        )
        .properties(height=max(150, 42 * len(risk_chart_data)))
    )
    st.altair_chart(risk_chart, use_container_width=True)

    st.markdown("#### Review Workflow Overview")
    status_counts = {}
    for case in dashboard_cases:
        status = case.get("review_status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    status_data = [
        {"Review Status": status, "Cases": count}
        for status, count in status_counts.items()
    ]
    st.caption("Review workflow statuses for saved investigations.")
    status_chart = (
        alt.Chart(alt.Data(values=status_data))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            y=alt.Y("Review Status:N", sort="-x", title=None, axis=alt.Axis(labelLimit=280, labelOverlap=False)),
            x=alt.X("Cases:Q", title="Number of cases", axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("Review Status:N"), alt.Tooltip("Cases:Q")],
        )
        .properties(height=max(170, 42 * len(status_data)))
    )
    st.altair_chart(status_chart, use_container_width=True)

    st.markdown("#### Actual Routing Decisions")
    known_route_counts = {}
    unknown_route_count = 0
    urgent_count = 0
    escalated_count = 0

    for case in dashboard_cases:
        route = str(case.get("route", "UNKNOWN") or "UNKNOWN").strip().upper()
        priority = str(case.get("route_priority", "UNKNOWN") or "UNKNOWN").strip().upper()

        if route == "UNKNOWN":
            unknown_route_count += 1
        else:
            known_route_counts[route] = known_route_counts.get(route, 0) + 1

        if priority == "URGENT":
            urgent_count += 1
        if case.get("review_status") == "Escalated":
            escalated_count += 1

    route_col1, route_col2, route_col3 = st.columns(3)
    route_col1.metric("Urgent Route Priority", urgent_count)
    route_col2.metric("Escalated Cases", escalated_count)
    route_col3.metric("Missing Route Data", unknown_route_count)

    if known_route_counts:
        route_data = [
            {"Route": route, "Cases": count}
            for route, count in sorted(known_route_counts.items())
        ]
        route_chart = (
            alt.Chart(alt.Data(values=route_data))
            .mark_bar(cornerRadiusEnd=5)
            .encode(
                y=alt.Y("Route:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False)),
                x=alt.X("Cases:Q", title="Number of cases", axis=alt.Axis(tickMinStep=1)),
                tooltip=[alt.Tooltip("Route:N"), alt.Tooltip("Cases:Q")],
            )
            .properties(height=max(180, 46 * len(route_data)))
        )
        st.altair_chart(route_chart, use_container_width=True)
    else:
        st.info("No saved routing decisions are available yet.")

    if unknown_route_count:
        st.caption(
            f"{unknown_route_count} older case(s) have no stored routing decision. "
            "They are excluded from the known-route chart; their original routes "
            "are not inferred or fabricated."
        )
    else:
        st.caption("All cases in the displayed history have saved routing decisions.")

else:
    st.info("Dashboard metrics will appear after you save your first investigation.")

# --------------------------------------------------

# 2. Transaction input

# --------------------------------------------------



st.subheader("Transaction Details")



with st.form("transaction_form"):

    col1, col2 = st.columns(2)



    with col1:

        transaction_id = st.text_input(

            "Transaction ID",

            value="TXN-1001",

        )



        amount = st.number_input(

            "Transaction Amount (₹)",

            min_value=0.0,

            value=5000.0,

            step=500.0,

        )



        channel = st.selectbox(

            "Transaction Channel",

            [

                "UPI",

                "Mobile Banking",

                "Internet Banking",

                "ATM",

                "Card",

            ],

        )



    with col2:

        location = st.selectbox(

            "Transaction Location",

            [

                "Usual Location",

                "New Location",

                "Unknown",

            ],

        )



        device = st.selectbox(

            "Device Status",

            [

                "Recognised Device",

                "New Device",

                "Unknown",

            ],

        )



        recent_failures = st.number_input(

            "Recent Failed Login Attempts",

            min_value=0,

            max_value=20,

            value=0,

            step=1,

        )



    submitted = st.form_submit_button(

        "Analyze Transaction",

        type="primary",

    )



# --------------------------------------------------

# 3. Execute workflow and save case

# --------------------------------------------------



if submitted:

    if not transaction_id.strip():

        st.error("Please enter a transaction ID.")



    else:

        try:

            result = investigate_transaction(

                amount=amount,

                channel=channel,

                location=location,

                device=device,

                failed_logins=int(recent_failures),

            )



            risk_result = result["risk_assessment"]

            recommendation_result = result["recommendation"]

            routing_result = result["routing"]



            incomplete_evidence = (

                location == "Unknown"

                or device == "Unknown"

            )



            human_review_required = (

                result["human_review_required"]

                or incomplete_evidence

            )



            # Ensure incomplete evidence remains visible in

            # the saved recommendation.

            effective_risk_result = dict(risk_result)



            if incomplete_evidence:

                effective_risk_result["recommendation"] = (

                    "Human review required: verify unknown "

                    "location or device information."

                )



            case_id = save_investigation(

                transaction_id=transaction_id.strip(),

                amount=amount,

                channel=channel,

                location=location,

                device=device,

                failed_logins=int(recent_failures),

                risk_result=effective_risk_result,

                recommendation_result=recommendation_result,

                human_review_required=human_review_required,
                routing_result=routing_result,

            )



            record_audit_event(

                investigation_id=case_id,

                action="Investigation created",

                old_value="",

                new_value="Pending Review",

                actor="Demo Investigator",

            )

            # Optional n8n integration: the investigation remains saved even if
            # the external automation endpoint is unavailable.
            automation_result = dispatch_case_event(
                {
                    "case_id": case_id,
                    "transaction_id": transaction_id.strip(),
                    "risk_level": risk_result.get("risk_level", "UNKNOWN"),
                    "risk_score": risk_result.get("total_risk_points", 0),
                    "route": routing_result.get("route", "UNKNOWN"),
                    "priority": routing_result.get("priority", "UNKNOWN"),
                    "human_review_required": bool(human_review_required),
                    "location": location,
                    "device": device,
                    "review_status": "Pending Review",
                    "event_type": "investigation.created",
                }
            )

            if automation_result["status"] == "sent":
                record_audit_event(
                    investigation_id=case_id,
                    action="Automation webhook sent",
                    old_value="Not Sent",
                    new_value=automation_result.get("message", "Webhook accepted"),
                    actor="System Automation",
                )
            elif automation_result["status"] == "failed":
                record_audit_event(
                    investigation_id=case_id,
                    action="Automation webhook failed",
                    old_value="Pending Dispatch",
                    new_value=automation_result.get("message", "Webhook failed"),
                    actor="System Automation",
                )



            st.session_state["last_investigation"] = {

                "case_id": case_id,

                "transaction_id": transaction_id.strip(),

                "amount": amount,

                "channel": channel,

                "location": location,

                "device": device,

                "failed_logins": int(recent_failures),

                "result": result,

                "human_review_required": human_review_required,

                "incomplete_evidence": incomplete_evidence,

            }



            st.success(f"Investigation saved. Case ID: {case_id}")
            if automation_result["status"] == "sent":
                st.success("n8n automation webhook accepted the case event.")
            elif automation_result["status"] == "failed":
                st.warning(
                    "The case was saved, but the n8n webhook failed. "
                    "Check the webhook URL and n8n execution history."
                )
            else:
                st.caption("n8n integration is disabled until N8N_WEBHOOK_URL is configured.")



        except Exception as error:

            st.error(

                "The investigation could not be completed. "

                "Check the VS Code terminal for details."

            )

            print(f"Investigation error: {error}")



# --------------------------------------------------

# 4. Results and routing

# --------------------------------------------------



if "last_investigation" in st.session_state:

    investigation = st.session_state["last_investigation"]

    result = investigation["result"]



    case_id = investigation["case_id"]

    risk_result = result["risk_assessment"]

    recommendation = result["recommendation"]

    routing = result["routing"]



    risk_level = risk_result["risk_level"]

    risk_score = risk_result["total_risk_points"]

    human_review_required = investigation["human_review_required"]

    incomplete_evidence = investigation["incomplete_evidence"]



    st.divider()

    st.subheader("Investigation Results")



    col1, col2, col3 = st.columns(3)



    col1.metric("Case ID", case_id)

    col2.metric("Illustrative Risk Score", f"{risk_score}/9")

    col3.metric("Risk Level", risk_level)



    if incomplete_evidence:

        st.warning(

            "Human review required: verify unknown location "

            "or device information before making a decision."

        )

    elif risk_level == "HIGH":

        st.error(risk_result["recommendation"])

    elif risk_level == "MEDIUM":

        st.warning(risk_result["recommendation"])

    else:

        st.success(risk_result["recommendation"])



    st.markdown("### Investigation Routing")



    route_col1, route_col2, route_col3 = st.columns(3)



    route_col1.metric("Selected Route", routing["route"])

    route_col2.metric("Priority", routing["priority"])

    route_col3.metric(

        "Human Review",

        "Required" if human_review_required else "Not Required",

    )



    st.write("**Routing reason:**", routing["reason"])



    if human_review_required:

        st.warning(

            "This case requires human oversight. Routing is a "

            "recommendation; no external team is contacted."

        )



    # Evidence.

    st.markdown("### Evidence and Risk Indicators")



    findings = risk_result.get("findings", [])



    if findings:

        for finding in findings:

            st.write(f"- {finding}")

    else:

        st.write("No elevated risk indicators were triggered.")



    # Agent results.

    st.markdown("### Agent Execution Details")



    agent_results = [

        result["transaction_analysis"],

        result["behavior_analysis"],

        risk_result,

        recommendation,

        routing,

    ]



    for agent_result in agent_results:

        with st.expander(agent_result.get("agent", "Agent")):

            st.json(agent_result)



    # Recommended next steps.

    st.markdown("### Recommended Investigation Steps")



    for step in recommendation.get("recommended_next_steps", []):

        st.write(f"- {step}")



    # --------------------------------------------------

    # 5. Review status and audit trail

    # --------------------------------------------------



    st.markdown("### Investigator Review and Approval")
    saved_cases_for_review = get_investigations(limit=100)

    if not saved_cases_for_review:
        st.info("No saved cases are available to review yet.")
    else:
        case_options = {
            f"Case {case['id']} | {case['transaction_id']} | {case['risk_level']} | {case['review_status']}": case
            for case in saved_cases_for_review
        }
        selected_case_label = st.selectbox(
            "Select Case ID to Review", list(case_options.keys()), key="review_case_selector"
        )
        selected_case = case_options[selected_case_label]
        review_case_id = selected_case["id"]
        current_status = selected_case.get("review_status", "Pending Review")
        current_approval = selected_case.get("approval_status", "Pending Approval") or "Pending Approval"
        case_requires_review = case_requires_human_review(selected_case)

        review_options = ["Pending Review", "Under Investigation", "Escalated", "Closed After Review"]
        approval_options = ["Pending Approval", "Approved", "Rejected", "Not Required"]
        if current_status not in review_options:
            current_status = "Pending Review"
        if current_approval not in approval_options:
            current_approval = "Pending Approval"

        st.caption(
            f"Case ID: {review_case_id} | Transaction: {selected_case['transaction_id']} | "
            f"Risk: {selected_case['risk_level']} | Human review required: {'Yes' if case_requires_review else 'No'}"
        )
        if case_requires_review:
            st.warning("Human review is required. Closure is permitted only after documented review notes and an Approved decision.")
        else:
            st.info("Document the review before closure. Approval may be marked Not Required when justified.")

        if selected_case.get("approved_at"):
            st.caption(f"Last approval metadata: {selected_case.get('approval_status')} by {selected_case.get('approved_by')} at {selected_case.get('approved_at')} (UTC)")

        with st.form(f"review_form_{review_case_id}"):
            actor = st.text_input("Investigator / Reviewer Name (demo)", value="Demo Investigator")
            selected_status = st.selectbox(
                "Review Status", review_options, index=review_options.index(current_status)
            )
            selected_approval = st.selectbox(
                "Human Approval Decision", approval_options, index=approval_options.index(current_approval),
                help="For cases requiring human review, select Approved only after checking the evidence."
            )
            review_notes = st.text_area(
                "Review Notes / Evidence Checked",
                value=selected_case.get("review_notes", "") or "",
                placeholder="Record evidence reviewed, checks performed, findings, and rationale for the decision.",
                height=130,
            )
            save_review = st.form_submit_button("Save Review and Approval", type="primary")

        if save_review:
            try:
                if selected_approval == "Approved" and selected_status == "Pending Review":
                    raise ValueError("Move the case to Under Investigation or Escalated before approval.")
                saved = save_review_workflow(
                    investigation_id=review_case_id,
                    review_status=selected_status,
                    review_notes=review_notes,
                    actor=actor,
                    approval_status=selected_approval,
                )
                if saved:
                    st.success("Review notes, status, approval decision, and audit events saved.")
                    st.rerun()
                else:
                    st.error("The investigation case was not found.")
            except ValueError as error:
                if selected_status == "Closed After Review" and "Closure blocked" in str(error):
                    try:
                        record_audit_event(
                            investigation_id=review_case_id,
                            action="Closure attempt blocked",
                            old_value=current_status,
                            new_value="Closed After Review (BLOCKED): " + str(error),
                            actor=actor.strip() or "Unknown Investigator",
                        )
                    except Exception as audit_error:
                        print(f"Could not record blocked closure attempt: {audit_error}")
                st.error(str(error))
            except Exception as error:
                st.error(f"Could not save the review workflow: {error}")
                print(f"Review workflow error: {error}")

        st.caption(
            "Prototype limitation: the investigator name is manually entered and not authenticated. "
            "The local SQLite audit trail is not tamper-proof. Approval metadata is not a digital signature."
        )

        st.markdown("### Case Audit Trail")
        events = get_audit_events(review_case_id)
        if events:
            st.dataframe(
                [
                    {
                        "Event ID": event["id"],
                        "Action": event["action"],
                        "Previous Value": event["old_value"],
                        "New Value": event["new_value"],
                        "Actor": event["actor"],
                        "Timestamp (UTC)": event["timestamp"],
                    }
                    for event in events
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No audit events are recorded for this case.")

    st.divider()

st.subheader("Investigation Case History")



saved_cases = get_investigations(limit=100)



if saved_cases:

    st.dataframe(

        [

            {

                "Case ID": case["id"],

                "Transaction ID": case["transaction_id"],

                "Amount (₹)": case["amount"],

                "Risk Score": f"{case['risk_score']}/9",

                "Risk Level": case["risk_level"],

                "Human Review": (

                    "Required"

                    if case["human_review_required"]

                    else "Not Required"

                ),

                "Review Status": case["review_status"],

                "Approval Status": case.get("approval_status", "Pending Approval"),

                "Approved By": case.get("approved_by", ""),

                "Created At (UTC)": case["created_at"],

            }

            for case in saved_cases

        ],

        use_container_width=True,

        hide_index=True,

    )



    st.caption(

        "Showing the 100 most recent cases stored in the local "

        "SQLite database."

    )

else:

    st.info("No investigation cases have been saved yet.")



st.divider()

st.caption(

    "Demonstration only. This prototype uses illustrative rules "

    "and is not validated for real banking decisions."

)
