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

# ********************************** Initiate the Models Required ************************************

def create_model(model_name: str) -> ChatOpenAI:
    return ChatOpenAI(
        model = model_name,
        api_key = os.getenv("GROQ_API_KEY"),
        base_url = "https://api.groq.com/openai/v1",
        temperature = 0,
        max_retries = 0
    )

llm_llama_70b = create_model("llama-3.3-70b-versatile")
llm_gpt_20b = create_model("openai/gpt-oss-20b")
llm_gpt_120b = create_model("openai/gpt-oss-120b")

# Set up specific LLMs for their roles with fallbacks to ensure stability
llm_search = llm_llama_70b.with_fallbacks([llm_gpt_20b])
llm_reader = llm_gpt_20b.with_fallbacks([llm_llama_70b])
llm_writer = llm_gpt_120b.with_fallbacks([llm_llama_70b])
llm_critic = llm_llama_70b.with_fallbacks([llm_gpt_120b])


# ********************************** Creating the Agents Required ************************************

# 1st agent 
def build_search_agent():
    return create_agent(
        model = llm_search,
        tools= [web_search]
    )

# 2nd agent 
def build_reader_agent():
    return create_agent(
        model = llm_reader,
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
- Key Findings (minimum 4 well-explained points and include tabular data if needed.)
- Conclusion
- Sources (list all URLs found in the research in bulleted format and must be clickable)

Be detailed, factual and professional.
IMPORTANT: Do NOT include any external citation markers, brackets, or literals like 【1†source】 in your output. Clean all such artifacts from the text."""),
])

writer_chain = writer_prompt | llm_writer | parser


# critic_chain 
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X out of 10 stars

Strengths:
-> &nbsp;&nbsp;&nbsp;...
-> &nbsp;&nbsp;&nbsp;...

Areas to Improve:
-> &nbsp;&nbsp;&nbsp;...
-> &nbsp;&nbsp;&nbsp;...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm_critic | parser