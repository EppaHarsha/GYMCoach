import streamlit as st
import os
from services.auth.login import login
from services.config.workout_config import Exercise_options
from services.state.session_defaults import initial_session_defaults
from services.ui.style_loader import load_css, inject_local_font,inject_webrtc_styles
from database.mongodb import get_or_create_user
from streamlit_webrtc import webrtc_streamer,WebRtcMode

def main():
    st.set_page_config(
        page_title="AI Real-time GYM Coach",
        page_icon="🏋️",
        initial_sidebar_state="expanded",
        layout="centered",
    )
    load_css()
    inject_local_font()
    if not login():
        return
    initial_session_defaults()
    if "workout_started" not in st.session_state:
        st.session_state.workout_started = False
    with st.sidebar:
        st.title("AI Coach")
        st.write(f"👷Login as {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not st.session_state.workout_started:
            st.selectbox("Excercise", options=Exercise_options, key="plan_exercise")

            st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

            st.number_input(
                "Reps per set", min_value=0, max_value=50, key="plan_reps", step=1
            )

            st.space()

            if st.button("Start Session", width="stretch", key="start_session_btn"):
                st.session_state.workout_started = True
                st.rerun()
        else:
            exercise = st.session_state.get("plan_exercise")
            sets = st.session_state.get("plan_sets")
            reps = st.session_state.get("plan_reps")
            print(exercise, sets, reps)

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            if st.button("End Session", key="end_session_btn"):
                st.session_state.workout_started = False
                st.rerun()

            # if "current_set_reps" not in st.session_state:
            #     st.session_state.current_set_reps = 0
            # if "sets_completed" not in st.session_state:
            #     st.session_state.sets_completed = 0
            # if "reps" not in st.session_state:
            #     st.session_state.reps = 0

        if st.session_state.workout_started:
            st.subheader("Progress")
            total_reps = st.session_state.get("reps")
            sets_completed = st.session_state.get("sets_completed")
            current_set_reps = st.session_state.get("current_set_reps")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current set Reps", f"{current_set_reps} / {reps}")
            st.metric("Sets Completed ", f"{current_set_reps} / {sets}")

            st.divider()
            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Biceps Curls (Dumbbell)":
                st.subheader("Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Stability", st.session_state.shoulder_status)
                st.metric("Swing Detection", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Arm Extension", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)

    st.title("AI Real-time GYM Coach")
    st.markdown("### Real-time pose detection with proactive AI voice coaching")
    if not st.session_state.workout_started:
        st.markdown(
            """
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
                margin-bottom: 32px;
            ">
                <h2 style="color:#ccc; margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=None,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )
    st.markdown("#### Workout History")
    inject_webrtc_styles()


if __name__ == "__main__":
    main()
