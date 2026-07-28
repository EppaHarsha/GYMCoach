import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import pandas as pd
import time
from database.mongodb import get_database
from services.coaching.voice_pipeline import VoicePipeline,autoplay_audio
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.tracking.metrics import sync_metrics_update
from services.auth.login import login
from services.config.workout_config import Exercise_options
from services.state.session_defaults import initial_session_defaults
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from database.mongodb import get_or_create_user
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from database.mongodb import get_users_exercises


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

    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("API_KEY_OPENAI", "")
            if (not api_key and hasattr(st, "secrets") and "API_KEY_OPENAI" in st.secrets):
                api_key = st.secrets["API_KEY_OPENAI"]
            openAI_client = OpenAI(api_key=api_key)
            st.write("API Loaded:", api_key[:10] if api_key else "No API Key")
            llm_coach = LLMCoach(openAI_client)
            tts = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
        except Exception as e:
            st.error(f"Voice initialization failed: {e}")
            st.session_state.voice_pipeline = None
    
    workout_started = st.session_state.get("workout_started",False)
        
    with st.sidebar:
        
        st.title("AI Coach")
        
        st.write(f"👷Login as {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            
            plan_exercise = st.selectbox("Excercise", options=Exercise_options, key="plan_exercise")
            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)
            plan_reps = st.number_input("Reps per set", min_value=0, max_value=50, key="plan_reps", step=1)
            st.space()
            
            if st.button("Start Session", width="stretch", key="start_session_btn"):
                st.session_state.workout_started = True
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps = 0
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started", exercise=plan_exercise, metrics={}
                    )
                    if result:
                        (
                            st.session_state.audio_to_play,
                            st.session_state.coach_feedback,
                        ) = result
                st.session_state.last_modified_sets_completed = 0
                st.session_state.last_modified_workout_completed = False

                st.rerun()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            if st.button("End Session", key="end_session_btn"):
                st.session_state.workout_started = False
                reps = st.session_state.get("reps", 0)
                sets_completed = st.session_state.get("sets_completed", 0)

                result = None

                if st.session_state.voice_pipeline:

                    if reps == 0:
                        result = st.session_state.voice_pipeline.process_event(
                        event="workout_stopped",
                        exercise=exercise,
                        metrics={"issue": "Ended the session before starting the workout"},
                        )

                    elif sets_completed == 0:
                        result = st.session_state.voice_pipeline.process_event(
                        event="workout_stopped",
                        exercise=exercise,
                        metrics={"issue": "Workout stopped before completing a set"},
                    )

                    else:
                        result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={},
                    )

                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result
                st.rerun()

        if workout_started:
            st.subheader("Progress")
            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            reps_per_set = st.session_state.get("reps_per_set")
            current_set_reps = st.session_state.get("current_set_reps")
            set_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("target_sets")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed ", f"{set_completed} / {target_sets}")

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

    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")
        
        
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
        inject_webrtc_styles()
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            },
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )
        sync_metrics_update(context)
        
        if context.state.playing:
            time.sleep(0.25)
            st.rerun()
        st.divider()
    st.markdown("#### Workout History")
    user_id = st.session_state.get("user_id", 0)

    if user_id:
        history_rows = get_users_exercises(user_id)
        arr = []
        for row in history_rows:
            temp = {
                "Exercise": row["exercise_name"],
                "Reps": row["reps"],
                "Sets": row["sets"],
                "Time(sec)": row["time"],
                "Date": row["created_at"],
            }
            arr.append(temp)

        df = pd.DataFrame(arr)
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            st.table(df, border="horizontal")
        else:
            st.info("No Workout history found.")


if __name__ == "__main__":
    main()
