# streamlit run ch03_voicebot.py

import streamlit as st
import os
from audiorecorder import audiorecorder

import openai
from datetime import datetime
import pytz

from gtts import gTTS
import base64

## 기능 구현 함수##
def STT(audio,apikey):
    #파일저장
    filename='input.mp3'
    audio.export(filename,format='mp3')
    
    #음원파일열기
    audio_file=open(filename,"rb")
    #Whisper 모델을 활용해 텍스트 얻기
    client=openai.OpenAI(api_key=apikey)
    responds=client.audio.transcriptions.create(model='whisper-1',file=audio_file)
    audio_file.close()
    #파일삭제
    os.remove(filename)
    return responds.text

def ask_gpt(prompt,model,apikey):
    client=openai.OpenAI(api_key=apikey)
    response=client.chat.completions.create(
        model = model,
        messages=prompt)
    gptResponse = response.choices[0].message.content
    return gptResponse


def TTS(response):
    #gTTS를 활용하여 음성 파일 생성
    filename="output.mp3"
    tts = gTTS(text=response, lang='ko')
    tts.save(filename)
    
    #음원파일 자동 재생
    with open(filename,'rb') as f:
        data = f.read()
        b64=base64.b64encode(data).decode()
        md=f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True,)
        
    #파일삭제
    os.remove(filename)

st.markdown("""
    <style>
    /* 메인 배경 */
    .stApp {
        background-color: #FFFFFF;
    }
    /* 사이드바 배경 */
    [data-testid="stSidebar"] {
        background-color: #C2E9F7;
    }
    /* 버튼 색 */
    .stButton > button {
        background-color: #29B5E8;
        color: white;
        border: none;
    }
    /* 글자색 */
    html, body, [class*="css"] {
        color: #1A3A4A;
    }
    </style>
""", unsafe_allow_html=True)

##메인함수##
def main():
    #기본설정
    st.set_page_config(
        page_title='🤖음성 비서 프로그램',
        layout='wide'
    )
    
    #제목
    st.header('🤖 주영 음성 비서 프로그램')
    st.caption('Whisper·GPT·gTTS 기반 한국어 음성 대화 비서')
    
    #구분선
    st.markdown('---')
    
    #기본설명
    with st.expander('음성 비서 프로그램에 관하여', expanded=True):
        st.write(
        """
        - 음성 비서 프로그램의 UI는 스트림릿을 활용했습니다.
        - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다.
        - 답변은 OpenAI의 GPT 모델을 활용했습니다.
        - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.
        """
        )
        
        st.markdown('')
        
    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state['chat'] = []
        
    if "OPENAI_API" not in st.session_state:
        st.session_state["OPENAI_API"] = ""
    
    if "messages" not in st.session_state:
        st.session_state['messages'] = [{'role':'system','content': '당신은 친절한 한국어 assistant입니다. 모든 질문에 반드시 한국어로만 대답하세요. 답변은 25단어 이내로 간결하게 합니다.'}]
    
    if "check_audio" not in st.session_state:
        st.session_state["check_audio"] = False

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False
    
    #사이드바 생성
    with st.sidebar:
        
        #Open AI API 키 입력받기
        st.session_state["OPENAI_API"]= st.text_input(label="OPENAI API 키", placeholder="Enter Your API Key",value='',type='password')
        
        st.markdown('---')
        
        #GPT 모델을 선택하기 위한 라디오 버튼 생성
        model = st.radio(label="GPT 모델", options = ['gpt-4o','gpt-4','gpt-3.5-turbo'])
        
        st.markdown('---')
        
        #리셋 버튼 생성
        if st.button(label='🔃 초기화'):
            #리셋코드
            st.session_state["chat"] = []
            st.session_state["messages"] = [{'role':'system','content': '당신은 친절한 한국어 assistant입니다. 모든 질문에 반드시 한국어로만 대답하세요. 답변은 25단어 이내로 간결하게 합니다.'}]
            st.session_state['last_audio_duration'] = 0
            st.rerun()

    if st.session_state['check_reset']:
        st.session_state['check_reset'] = False
    
    #기능 구현 공간    
    col1,col2 = st.columns(2)
    with col1:
        #왼쪽 영역 작성
        st.subheader('질문하기')
        #음성 녹음 아이콘 추가
        audio=audiorecorder(start_prompt="클릭하여 녹음하기🎙️", stop_prompt= "⏺️ 녹음중...",)
        if (audio.duration_seconds > 0) and (audio.duration_seconds != st.session_state.get('last_audio_duration',0)): #녹음을 실행하면?
            #음성재생
            st.session_state['last_audio_duration']=audio.duration_seconds
            #음원 파일에서 텍스트 추출
            question=STT(audio,st.session_state["OPENAI_API"])
            
            #채팅을 시각화 하기 위해 질문 내용 저장
            kst=pytz.timezone('Asia/Seoul')
            now = datetime.now(kst).strftime("%H:%M")
            st.session_state['chat'] = st.session_state['chat']+[('user',now,question)]
            #GPT 모델에 넣을 프롬프트를 위해 질문 내용 저장
            st.session_state['messages'] = st.session_state['messages']+[{'role':'user','content':question}]
    
    with col2:
        #오른쪽 영역 작성
        st.subheader('질문/답변')
        if (audio.duration_seconds > 0) and (st.session_state['check_reset']==False):
            #ChatGPT에게 답변 얻기
            response = ask_gpt(st.session_state['messages'],model,st.session_state["OPENAI_API"])
        
            #GPT모델에 넣을 프롬프트를 위해 답변 내용 저장
            st.session_state['messages']=st.session_state['messages']+[{'role':'assistant','content':response}]
            
            #채팅 시각화를 위한 답변 내용 저장
            kst=pytz.timezone('Asia/Seoul')
            now = datetime.now(kst).strftime("%H:%M")
            st.session_state['chat'] = st.session_state['chat']+[('bot',now,response)]
            
            #채팅 형식으로 시각화하기
            for sender,time,message in st.session_state['chat']:
                if sender=='user':
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write('')
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>',unsafe_allow_html=True)
                    st.write('')
            #gTTS를 활용하여 음성 파일 생성 및 재생
            TTS(response)
            
if __name__=="__main__":
    main()
