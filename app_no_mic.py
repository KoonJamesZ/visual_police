# from openai import OpenAI
import os
from typing import Any, Dict
import ast
import json
import gradio as gr
from openai import AzureOpenAI


os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test-gpt4-0-bt.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "55c2cab8e0bd45078d5c7fba1d1b137e"


client = AzureOpenAI(
    api_version="2023-05-15",
    azure_deployment="bt-rd-gpt4o",
)



information_extrac_prompt = """ Your job is to extract important information from USER text input
                                The important information you need to pull is:

                                INFORMATION_JSON:
                                {INFROMATION_JSON}

                                This is the previous question you asked:
                                {QUESTION}

                                USER: {USER_INPUT_DATA}

                                If in the USER message is available in INFORMATION.
                                Please reply this information in json format.

                                Do not delete existing data. Please return the original data as well. But if the information is on the same topic Please combine the information.

                                Please write information with USET input language."""


conversatoin_prompt = """ You are an investigative expert. Your job is to try and answer questions.
                          with the user in order to collect information that is useful in further investigating complete.

                          INFORMATION_JSON:
                          {INFORMATION_JSON}

                          This is the previous question you asked:
                          {QUESTION}

                          Don't ask the same question again.

                          If some any part has INFORMATION_JSON but is not complete. Please ask questoin more for gave the information from user, but if the INFORMATION_JSON is complete Please ask more the new next question.
                          
                          Try to ask one question at a time.

                          If there is no information at all Start by asking your name first.

                          Remember asking as if He was talking to a police officer. who is really a female person.
                          
                          Please note the new question and avoid repeating the format of the previous question, which was -> {QUESTION}.

                          Response with Thai language.
                                    """

data_from_user = {
                  "ชื่อ" : "",
                  "เหตุการณ์ที่เกิดขึ้น": "",
                  "ชื่อคนร้าย": "",
                  "วัน/เวลาที่เกิดเหตุ": "",
                  "ประเภททรัพย์สินที่เสียไป": "",
                  "มูลค่าความเสียหายที่เกิดขึ้น": "",
                  "หมายเลขบัญชีของคนร้าย": "",
                  "ช่องทางที่คนร้ายติดต่อเข้ามา": "",
                  "คนร้ายติดต่อมาด้วยข้อความแบบใหน/ตัวอย่าง": "",
                  "มีช่องทางในการติดต่อคนร้ายใหม": "",
}

def information_extract(user_input: str, question: str, data_from_user: Dict )-> Dict:
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": information_extrac_prompt.replace("{USER_INPUT_DATA}",user_input).replace('{QUESTION}',question).replace('{INFROMATION_JSON}',str(data_from_user)) }
    ],
    temperature=0,
    response_format={ "type": "json_object" }
    )

    result_dict = ast.literal_eval(completion.choices[0].message.content)
    return result_dict

def generate_question(question: str) -> str:
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": conversatoin_prompt.replace('{INFORMATION_JSON}',str(data_from_user)).replace('{QUESTION}',question)}],
    temperature=0.7,
    )
    return completion.choices[0].message.content

def check_information(data_dict: Dict) -> bool:
    check = True
    for valuse in data_dict.values():
        if valuse == "" :
            check = False
    return check


# Function to reset data and question
def reset_data():
    global data_from_user, question
    data_from_user = {
        "ชื่อ": "",
        "เหตุการณ์ที่เกิดขึ้น": "",
        "ชื่อคนร้าย": "",
        "วัน/เวลาที่เกิดเหตุ": "",
        "ประเภททรัพย์สินที่เสียไป": "",
        "มูลค่าความเสียหายที่เกิดขึ้น": "",
        "หมายเลขบัญชีของคนร้าย": "",
        "ช่องทางที่คนร้ายติดต่อเข้ามา": "",
        "คนร้ายติดต่อมาด้วยข้อความแบบใหน/ตัวอย่าง": "",
        "มีช่องทางในการติดต่อคนร้ายใหม": "",
    }
    question = generate_question("")
    chat_history = [[None, question]]
    
    return chat_history # Reset chat history with initial question


# Function to update the data display
def update_data_display():
    pretty_json = json.dumps(data_from_user, indent=4, ensure_ascii=False)
    return pretty_json

# Main respond function
def respond(message, chat_history):
    global data_from_user, question
    data_from_user = information_extract(message, question, data_from_user)
    verify = check_information(data_from_user)
    if verify:
        response = "ข้อมูลครบถ้วนแล้ว ขอบคุณค่ะ"
        msg_interactive = False
    else:
        question = generate_question(question)
        response = question
        msg_interactive = True
    chat_history.append([message, response])
    if len(chat_history) >= 12:
        msg_interactive = False
    return "", chat_history, gr.update(interactive=msg_interactive)


# Initialize the first question
reset_data()

# Create the Gradio interface
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(value=[[None, question]], bubble_full_width=False, height=1000)
    msg = gr.Textbox(placeholder="Type your message here...", label="Message")
    data_display = gr.Textbox(value=update_data_display(), label="Data from User", interactive=False)

    with gr.Row():
        reset_button = gr.Button("Reset")
        submit_button = gr.Button("Submit")

    msg.submit(respond, [msg, chatbot], [msg, chatbot, msg]).then(fn=update_data_display, outputs=data_display)
    submit_button.click(respond, [msg, chatbot], [msg, chatbot, msg]).then(fn=update_data_display, outputs=data_display)
    reset_button.click(fn=reset_data, outputs=[chatbot]).then(fn=update_data_display, outputs=data_display).then(lambda: gr.update(interactive=True), outputs=msg)  # reset button functionality


if __name__ == "__main__":
    demo.launch(share=True)
