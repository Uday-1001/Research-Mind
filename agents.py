from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search , scrape_url 
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI

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

def create_gemini_model(model_name: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model = model_name,
        google_api_key = os.getenv("GOOGLE_API_KEY"),
        temperature = 0,
        max_retries = 0
    )

llm_gpt_20b = create_model("openai/gpt-oss-20b")
llm_gpt_120b = create_model("openai/gpt-oss-120b")
llm_first_gemini = create_gemini_model("gemini-2.5-flash")
llm_second_gemini = create_gemini_model("gemini-3.5-flash")

# Set up specific LLMs for their roles with fallbacks to ensure stability
llm_search = llm_gpt_20b.with_fallbacks([llm_first_gemini , llm_second_gemini])
llm_reader = llm_gpt_20b.with_fallbacks([llm_first_gemini , llm_second_gemini])
llm_writer = llm_gpt_120b.with_fallbacks([llm_gpt_20b])
llm_critic = llm_gpt_120b.with_fallbacks([llm_gpt_20b])


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

{feedback}

Structure the report as:
- Introduction
- Key Findings (minimum 4 well-explained points. Use tables ONLY when the data is strictly in a tabular format and would be distorted or hard to understand if presented without a table.)
- Conclusion
- Sources (MANDATORY: list all sources and URLs found in the research in bulleted format. Every source must be a clickable markdown link)

Be detailed, factual and professional.
IMPORTANT FORMATTING RULES - YOU MUST FOLLOW THESE STRICTLY:
1. CITATIONS AND LINKS: You MUST explicitly mention the source of your information to prevent false info. Convert any raw external citation markers, search snippets, brackets, or literals like 【1†source】 into proper inline clickable Markdown links. Clickable links and source mentions are MANDATORY.
2. MATH & SYMBOLS: You MUST format all mathematical formulas, equations, variables, and scientific symbols using proper LaTeX. 
   - INLINE: For math within a sentence, use a single `$` (e.g., $E=mc^2$). 
   - BLOCK: For standalone equations, use double `$$`. You MUST place `$$` block math on its own separate new line with empty lines above and below it. NEVER place `$$` in the middle of a text line. 
   - NO RAW MATH: Do not use raw text approximations like `r^{{-γ}}` or `ρ_DM`.
3. TABLES: Only use Markdown tables if the underlying data is strictly tabular (e.g., comparative stats, metrics). Never use a table just to format regular text.
4. SPACING: Always leave a blank line before and after headings, lists, tables, and block equations to ensure the Markdown renderer processes them correctly.
5. NO XML/HTML: Stick strictly to standard Markdown. Do not use raw HTML tags or XML blocks unless explicitly required."""),
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