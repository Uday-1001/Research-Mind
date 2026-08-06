# pyrefly: ignore [missing-import]
from langchain.agents import create_agent
# pyrefly: ignore [missing-import]
from langchain_openai import ChatOpenAI
# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
# pyrefly: ignore [missing-import]
from langchain_core.output_parsers import StrOutputParser
# pyrefly: ignore [missing-import]
from tools import web_search , scrape_url 
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os

load_dotenv()

# ************************************** Model - GPT OSS 120B ****************************************

# model setup using the groq api via endpoint 
llm_primary = ChatOpenAI(
    model = "openai/gpt-oss-120b",
    api_key = os.getenv("GROQ_API_KEY"),
    base_url = "https://api.groq.com/openai/v1",
    temperature = 0
)

llm_fallback = ChatOpenAI(
    model = "llama-3.3-70b-versatile",
    api_key = os.getenv("GROQ_API_KEY"),
    base_url = "https://api.groq.com/openai/v1",
    temperature = 0
)

llm = llm_primary.with_fallbacks([llm_fallback])


# ********************************** Creating the Agents Required ************************************

# 1st agent 
def build_search_agent():
    return create_agent(
        model = llm,
        tools= [web_search]
    )

# 2nd agent 
def build_reader_agent():
    return create_agent(
        model = llm,
        tools = [scrape_url]
    )

# ********************************** LCEL Chains for the Pipeline ************************************

parser = StrOutputParser()

# writer prompt 
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional.
IMPORTANT: Do NOT include any external citation markers, brackets, or literals like 【1†source】 in your output. Clean all such artifacts from the text."""),
])

writer_chain = writer_prompt | llm | parser


# critic_chain 
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X out of 10 stars

Strengths:
-> ...
-> ...

Areas to Improve:
-> ...
-> ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | parser