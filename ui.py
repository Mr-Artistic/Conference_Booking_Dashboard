import streamlit as st
from db import add_booking, check_conflict


def st_red_alert(msg: str):
    st.markdown(
        f"""
        <div style="
            padding: 10px 16px;
            margin: 10px 0;
            border-radius: 6px;
            background-color: #ffddd9;   /* red-500 */
            color: black;
            font-weight: 400;
        ">
            {msg}
        </div>
        """,
        unsafe_allow_html=True,
    )


def booking_form():

    st.subheader(":red[**👉 Book Conference Room**]")
    with st.form("booking_form"):
        booking_date = st.date_input("Booking Date")
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")
        conference_type = st.selectbox(
            "Conference Type", ["I-HUB 1st floor", "I-HUB 5th floor", "Mendeleev"]
        )
        person_name = st.text_input("Person Name")
        company_name = st.text_input("Company/Organization")
        affiliation = st.selectbox("Affiliation/Department", ["I-HUB", "AIC"])
        email = st.text_input("Email")

        submitted = st.form_submit_button("Submit Booking")

        if submitted:
            # Collect missing fields
            missing = []
            if not booking_date:
                missing.append("Booking Date")
            if not start_time:
                missing.append("Start Time")
            if not end_time:
                missing.append("End Time")
            if not conference_type:
                missing.append("Conference Type")
            if not person_name.strip():
                missing.append("Person Name")
            if not company_name.strip():
                missing.append("Company/Organization")
            if not affiliation.strip():
                missing.append("Affiliation/Department")
            if not email.strip():
                missing.append("Email")

            if missing:
                st_red_alert(f"Please fill all required fields: {', '.join(missing)}.")
            else:
                conflict, details = check_conflict(booking_date, start_time, end_time)
                if conflict:
                    st_red_alert(f"❌ Time conflict! {details}")
                else:
                    add_booking(
                        booking_date,
                        start_time,
                        end_time,
                        conference_type,
                        person_name,
                        company_name,
                        affiliation,
                        email,
                    )
                    st.session_state["_flash"] = "✅ Booking submitted successfully!"
                    st.cache_data.clear()
                    st.rerun()
