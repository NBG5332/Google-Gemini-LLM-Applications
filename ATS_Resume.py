import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as PyPDF2

from dotenv import load_dotenv
load_dotenv() ## load all the environmnet variables

os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

##Gemini Pro Response
def get_gemini_response(input):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content(input)
    return response.text

def input_pdf_text(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += str(page.extract_text())
    return text

## Prompt Template for gemini pro to understand our requirments
input_prompt="""
Hey Act Like a skilled or very experience ATS(Application Tracking System)
with a deep understanding of tech field, software engineering, data science, data analyst and 
big data engineer. understand all the words in the resume properly like what are technologies/softwares, 
what are skills like technical, hardware and softwware skills.
give your answer in such a way that, that is final feedback on the resume.
 Your task is to evaluate the resume based on the given job description and the score should be accurate and good
 if the user uploads the same resume and job description score need to be same.
You must consider the job market is very competitive and you should provide
best assistance for improving thr resumes. Assign the percentage Matching based
on Jd and
the missing technologies/software and skiils keywords with high accuracy
resume: {text}
description:{jd}

I want the response in one signle string having the structure
{{"JD MAtch":"%", "MissingKeywords:[]", "Profile Summary of the candidate":""}}
Don't change response for the same query, maintain same level of complexicity. 
"""

## streamlit app
st.title("Smart ATS for resume")
st.text("Imporve Your Resume ATS")
jd=st.text_area("Paste the Job Description")
uploaded_file=st.file_uploader("Upload your Resume", type="pdf",help="Please upload the correct file")

submit=st.button("Submit")

if submit:
    if uploaded_file is not None:
        text=input_pdf_text(uploaded_file)
        response= get_gemini_response(input_prompt)
        st.subheader(response)