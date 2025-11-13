from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.core.memory import get_session_history

def build_stateful_agent(llm, tools):
    """
    LLM과 도구(Tools)를 결합하여 기억력을 가진 에이전트를 만듭니다.
    """
    
    # 1. 시스템 프롬프트
    # chat_history: 이전 대화 내용을 넣을 공간
    # agent_scratchpad: AI가 도구를 사용한 생각의 과정을 적는 공간
    prompt = ChatPromptTemplate.from_messages([
        (
            "system", 
            "당신은 NestJS 백엔드와 연동된 똑똑한 AI 비서입니다. "
            "사용자의 질문에 답변하되, 요청에 따라 주어진 도구를 적극적으로 사용하세요."
            "사용자의 요청이 당신의 도구로 처리할 수 있는 일이라고 판단되면, **반드시 해당 도구를 사용하세요.**"
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 2. 에이전트 생성 (LLM + 도구 + 프롬프트)
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 3. 실행기 생성
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        return_intermediate_steps=True
    )

    # 4. 대화 기록 관리 기능 추가 (RunnableWithMessageHistory)
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,               # .with_config({"return_intermediate_steps": True})
        get_session_history,          # session_id로 기록 찾는 함수
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return agent_with_chat_history