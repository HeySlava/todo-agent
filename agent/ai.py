import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from openai import OpenAI

from agent import tools as t

api_key = os.environ['OPENAI_TOKEN']


llm = ChatOpenAI(
        model='gpt-4o-mini',
        temperature=0,
        api_key=api_key,
    )


def convert_audio_to_text(audio_path: str) -> str:
    audio_file = open(audio_path, 'rb')

    client = OpenAI(api_key=api_key)
    transcription = client.audio.transcriptions.create(
        model='gpt-4o-mini-transcribe',
        file=audio_file
    )

    return transcription.text


tools = [t.do_it, t.remember]
agent = create_react_agent(model=llm, tools=tools)
