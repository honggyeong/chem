import streamlit as st
import numpy as np
import pandas as pd
import time
import wave
from io import BytesIO


def calculate_ph(volume_naoh, initial_volume_vinegar, initial_conc_vinegar=0.8):
    """pH 계산 함수"""
    moles_acid = initial_volume_vinegar * initial_conc_vinegar
    moles_base = volume_naoh * 0.1
    remaining_acid = moles_acid - moles_base

    if remaining_acid > 0:
        h_conc = np.sqrt(remaining_acid * 1.8e-5)  # Ka of acetic acid
        return -np.log10(h_conc)
    elif remaining_acid < 0:
        oh_conc = -remaining_acid
        h_conc = 1e-14 / oh_conc
        return -np.log10(h_conc)
    else:
        return 7.0


def generate_tone(frequency, duration=0.1, sample_rate=44100):
    """Generate a tone in WAV format for playback with Streamlit."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = np.sin(2 * np.pi * frequency * t)
    tone = (tone * 16000).astype(np.int16)

    # Convert to WAV format
    buffer = BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(tone.tobytes())

    buffer.seek(0)
    return buffer


def play_sound(frequency):
    """Play sound using Streamlit's st.audio."""
    tone = generate_tone(frequency)
    audio_data = tone.read()
    
    # Insert HTML with JavaScript to autoplay audio
    audio_html = f"""
    <audio id="audio" autoplay>
        <source src="data:audio/wav;base64,{audio_data}" type="audio/wav">
        Your browser does not support the audio element.
    </audio>
    """
    
    st.markdown(audio_html, unsafe_allow_html=True)


def main():
    st.title("가상 적정 실험 시뮬레이터")
    st.markdown("### 장애인을 위한 화학 실험 보조 시스템")

    if 'volume_naoh' not in st.session_state:
        st.session_state.volume_naoh = 0.0
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'data' not in st.session_state:
        st.session_state.data = []
    if 'has_reached_neutral' not in st.session_state:
        st.session_state.has_reached_neutral = False

    if 'initial_vinegar' not in st.session_state:
        st.session_state.initial_vinegar = 50.0

    st.sidebar.header("실험 설정")
    initial_vinegar = st.sidebar.number_input("식초의 초기 부피 (mL)",
                                              min_value=0.1,
                                              max_value=100.0,
                                              value=st.session_state.initial_vinegar)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 실시간 적정 그래프")
        chart_placeholder = st.empty()

    with col2:
        st.markdown("### 현재 상태")
        status_placeholder = st.empty()

        start_stop = st.button("뷰렛 코크 열기/닫기")
        reset = st.button("실험 초기화")

    if start_stop:
        st.session_state.is_running = not st.session_state.is_running

    if reset:
        st.session_state.volume_naoh = 0.0
        st.session_state.is_running = False
        st.session_state.data = []
        st.session_state.has_reached_neutral = False

    if st.session_state.is_running and not st.session_state.has_reached_neutral:
        while st.session_state.is_running:
            st.session_state.volume_naoh += 0.1

            current_ph = calculate_ph(st.session_state.volume_naoh, initial_vinegar)

            st.session_state.data.append({
                'Volume NaOH (mL)': st.session_state.volume_naoh,
                'pH': current_ph
            })

            df = pd.DataFrame(st.session_state.data)
            fig, ax = plt.subplots()
            ax.plot(df['Volume NaOH (mL)'], df['pH'], 'b-')
            ax.set_xlabel('NaOH 부피 (mL)')
            ax.set_ylabel('pH')
            ax.grid(True)
            chart_placeholder.pyplot(fig)
            plt.close()

            status_html = f"""
            <div style="padding: 20px; border-radius: 10px; background-color: {generate_color(current_ph)}">
                <h3>측정값</h3>
                <p>첨가된 NaOH: {st.session_state.volume_naoh:.1f} mL</p>
                <p>현재 pH: {current_ph:.2f}</p>
            </div>
            """
            status_placeholder.markdown(status_html, unsafe_allow_html=True)

            # pH가 7에 가까워지면 중화점에 도달했다고 판단
            if current_ph > 6.5:
                st.session_state.has_reached_neutral = True
                st.session_state.is_running = False  # 실험 종료
                play_sound(500)  # 삐비빅 소리 (500Hz)
                time.sleep(0.7)
                play_sound(500)  # 삐비빅 소리 (500Hz)
                st.write("중화점 근처에 도달했습니다! 코크가 자동으로 닫혔습니다.")

            # pH 상태에 따른 소리
            if current_ph < 7:
                play_sound(440)  # 낮은 음 (산성)
            elif current_ph > 7:
                play_sound(880)  # 높은 음 (염기성)
            else:
                play_sound(660)  # 중간 음 (중성)

            time.sleep(0.1)


if __name__ == "__main__":
    main()
