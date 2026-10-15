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
        max_retries = 0,
        max_tokens = 4000
    )

def create_gemini_model(model_name: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model = model_name,
        google_api_key = os.getenv("GOOGLE_API_KEY"),
        temperature = 0,
        max_retries = 0,
        max_output_tokens = 4000
    )

llm_gpt_20b = create_model("openai/gpt-oss-20b")
llm_gpt_120b = create_model("openai/gpt-oss-120b")
llm_first_gemini = create_gemini_model("gemini-3.8-flash")
llm_second_gemini = create_gemini_model("gemini-flash-latest")

# Set up specific LLMs for their roles:
# GPT-120b is EXCLUSIVELY reserved for the Specialized Writer (best model)
llm_search = llm_gpt_20b.with_fallbacks([llm_first_gemini, llm_second_gemini])
llm_reader = llm_gpt_20b.with_fallbacks([llm_first_gemini, llm_second_gemini])
llm_writer = llm_gpt_120b.with_fallbacks([llm_first_gemini, llm_second_gemini, llm_gpt_20b])
llm_critic = llm_first_gemini.with_fallbacks([llm_second_gemini, llm_gpt_20b])


# ********************************** Creating the Agents Required ************************************

SEARCH_AGENT_PROMPT = """You are a rigorous Web Search Agent.
Your objective is to find recent, reliable, and high-quality information on the given topic.

CRITICAL INSTRUCTIONS:
1. ALWAYS call the `web_search` tool with a targeted, effective search query.
2. For EVERY relevant source discovered by the tool, you MUST explicitly extract and list:
   - Exact URL (http:// or https://)
   - Source / Article Title
   - Key factual findings, metrics, and quotes
3. Output format must strictly follow this structure:

## Search Findings Summary
<Synthesized overview of what was discovered>

## Discovered Sources & Links (MANDATORY)
For each result found by the search tool, list:
- URL: <exact http/https URL>
  Title: <page title>
  Summary: <concise summary>

4. NEVER omit, hide, or truncate the URLs. The downstream Reader Agent strictly depends on these exact URLs to scrape in-depth content."""

READER_AGENT_PROMPT = """You are an autonomous Web Reader & Extraction Agent.
Your objective is to identify the single most authoritative, informative URL from the search findings and extract its full content.

CRITICAL INSTRUCTIONS:
1. Scan the provided search results to identify all available URLs.
2. You MUST immediately invoke the `scrape_url` tool with the single best URL (prefer in-depth analysis, articles, or documentation over generic landing pages).
3. If no labeled URL field is obvious, extract any http:// or https:// link present in the text and scrape it immediately.
4. If scraping fails or returns an error, choose the next best URL from the search results and scrape that instead.
5. In your final response, provide:
   - Target URL Scraped: <the exact URL you scraped>
   - Extracted Deep Content: <detailed, structured synthesis of the scraped content, highlighting mechanisms, statistics, findings, and technical facts>
6. NEVER reply by saying you cannot find URLs or asking the user for links. You must autonomously choose and scrape from the provided search results."""

# 1st agent 
def build_search_agent():
    return create_agent(
        model = llm_search,
        tools = [web_search],
        system_prompt = SEARCH_AGENT_PROMPT
    )

# 2nd agent 
def build_reader_agent():
    return create_agent(
        model = llm_reader,
        tools = [scrape_url],
        system_prompt = READER_AGENT_PROMPT
    )

# ********************************** LCEL Chains for the Pipeline ************************************

parser = StrOutputParser()

# writer prompt 
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a world-class Principal Research Scientist and Chief Technical Analyst. You author comprehensive, publishable research briefs that synthesize complex empirical and web intelligence with utmost clarity, technical rigor, and factual precision."),
    ("human", """Write an authoritative, rigorous, and fully completed research report on the topic below.

Topic: {topic}

Research Gathered from Web Search & Deep Reader:
{research}

{feedback}

CRITICAL LENGTH BUDGET & COMPLETION MANDATE:
- TOTAL TARGET LENGTH: 1,600 to 2,300 words (~2,200 to 3,100 tokens).
- You MUST strictly budget your tokens so that ALL SIX (6) MANDATORY SECTIONS are 100% written, fully fleshed out, and never cut off mid-sentence.
- You MUST finish the entire document cleanly, concluding with Section 6 (Verified Sources & Academic References).
- Avoid repetitive filler. Dense, rigorous technical analysis is far superior to verbose padding.

Structure your research report with the following mandatory sections:

# Comprehensive Research Report: {topic}

## 1. Executive Summary & Problem Context
Provide a focused, high-level synthesis of {topic} (~200 words). Explain the core problem, why it is critical today, current scientific baselines, and the report's overarching thesis.

## 2. Deep-Dive Key Findings & Breakthroughs
Provide exactly 3 to 4 tightly argued, deeply analyzed key findings (~700-900 words total).
For EACH finding:
- Give it a descriptive, bold conceptual heading.
- Provide a rigorous, substantive technical breakdown (1 to 2 detailed paragraphs).
- Integrate specific empirical metrics, percentages, dates, architectural components, or experimental benchmarks from the research.

## 3. Mathematical & Theoretical Formulations
Formulate the governing mathematical relationships, algorithmic complexity bounds, or scaling laws (~250 words):
- STRICT MARKDOWN / KATEX MATH SYNTAX:
  * For standalone display equations, you MUST enclose the formula inside double dollar signs `$$` on their own separate lines with empty blank lines above and below:
    $$
    \\pi_\\theta(a_t \\mid s_t) = \\text{{LLM}}_\\theta(\\text{{Prompt}}(s_t))
    $$
  * NEVER use LaTeX square brackets `\\[` or `\\]` or parentheses `\\(` or `\\)` or unclosed brackets `[` `]`.
  * For all inline variables, symbols, and mathematical terms in the explanatory text, enclose them in single dollar signs: `$\\theta$`, `$s_t$`, `$a_t$`, `$R$`, `$\\tau_t$`.
  * NEVER write naked LaTeX commands like `\\pi_\\theta` or `\\mathbb{{E}}` without dollar sign wrappers `$ ... $` or `$$ ... $$`.
  * Define all variables in a clean, professional bulleted list immediately following each equation.

## 4. Benchmark & Comparative Analysis
Synthesize key metrics, competing paradigms, or historical vs state-of-the-art performance in a clean Markdown comparison table with clear headers (~250 words including table and analytical commentary).

## 5. Strategic Implications & Future Trajectory
Discuss practical deployment challenges, bottleneck factors, engineering trade-offs, and 2-5 year projections (~250 words).

## 6. Verified Sources & Academic References (MANDATORY)
List all legitimate sources found in the gathered research in bulleted format (~150 words).
- Every source MUST be a clickable Markdown link: `[Source Title or Domain](exact_URL)`.
- Use the actual URLs discovered in the research. NEVER invent placeholders or claim links are missing.

CRITICAL FORMATTING GUARDRAILS:
1. CITATIONS: Link real URLs discovered in the research directly within the text and under Sources.
2. MATHEMATICAL RIGOR & KAETX FORMATTING:
   - Standalone display equations MUST be wrapped in `$$` on separate lines.
   - Inline variables MUST be wrapped in `$`.
   - NEVER use `\\[`, `\\]`, `\\(`, `\\)`, or plain brackets `[` `]` around formulas.
   - Never output unrendered pseudo-code or broken symbols.
3. 100% COMPLETION GUARANTEE: Never leave the report unfinished or cut off. Conclude cleanly with Section 6."""),
])

writer_chain = writer_prompt | llm_writer | parser

# Continuation chain for emergency completion if token ceiling is hit:
writer_continuation_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the Principal Research Scientist completing an in-progress research report that was cut off due to token limits. Complete all remaining sections seamlessly, maintaining high technical rigor, pristine LaTeX formulas ($$ for display, $ for inline, NEVER \\[ or \\]), and ending cleanly with ## 6. Verified Sources & Academic References with clickable markdown links."),
    ("human", """Topic: {topic}

Original Research & Sources:
{research}

The report draft was cut off mid-way. Here is the text generated so far:
---
{text_so_far}
---

Continue from the EXACT cut-off point above. Finish all remaining sections through ## 6. Verified Sources & Academic References completely:""")
])

writer_continuation_chain = writer_continuation_prompt | llm_writer | parser


# critic_chain 
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp, rigorous, and constructive research critic. Be honest, objective, and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Evaluation Criteria:
1. Depth & Accuracy: Does it contain 3 to 4 well-developed, insightful findings with empirical numbers and architectural depth?
2. Completeness: Does the report complete ALL sections (1 through 6) including equations, comparison table, trajectory, and sources without cutting off mid-sentence? If cut off or incomplete, score MUST be below 7.0.
3. Mathematics & Formatting: Are all equations and scientific symbols written in proper LaTeX syntax?
4. Sources & Citations: Are legitimate, clickable markdown source links ([Title](URL)) provided under Sources? If sources or URLs are missing or generic placeholders, the score MUST be below 8.0.

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