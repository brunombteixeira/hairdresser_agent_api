import os
from datetime import datetime
from dotenv import load_dotenv
from db_functions import supa_insert_data, supa_fetch_data

load_dotenv()

# LANGSMITH SETUP
os.environ["LANGCHAIN_API_KEY"] = os.environ.get("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Hairdresser Agent"

def create_agent():
    # -------- CREATE THE AGENT ---------#

    from langchain import hub
    from langchain.agents import create_openai_functions_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai.chat_models import ChatOpenAI
    from tools import get_company_general_info, get_services_information, get_availability_for_service

    tools = [get_company_general_info, get_services_information, get_availability_for_service]

    # prompt = hub.pull("hwchase17/openai-functions-agent")
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"You are very powerful assistant who will answer questions related to a barbershop. If you have access to customer's name, please use it when aswering. Your answers should be written in PT-PT and the only currency you know is Euros. Today is {datetime.today().strftime('%Y-%m-%d')}"
            ),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
                MessagesPlaceholder(variable_name="chat_history"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4o", streaming=True)

    agent_runnable = create_openai_functions_agent(llm, tools, prompt)


    # -------- DEFINE THE GRAPH STATE ---------#

    import operator
    from typing import Annotated, TypedDict, Union

    from langchain_core.agents import AgentAction, AgentFinish
    from langchain_core.messages import BaseMessage

    class AgentState(TypedDict):
        input: str
        chat_history: list[BaseMessage]
        agent_outcome: Union[AgentAction, AgentFinish, None]
        intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
        user_waid: str

    # -------- DEFINE THE GRAPH NODES ---------#

    from langchain_core.agents import AgentFinish
    from langgraph.prebuilt.tool_executor import ToolExecutor

    tool_executor = ToolExecutor(tools)

    def run_agent(data):
        agent_outcome = agent_runnable.invoke(data)

        # Get the agent's output
        agent_output = agent_outcome.log

        # Update the chat_history in the state dictionary
        # updated_chat_history = data['chat_history'] + [agent_output]
        # supa_insert_data(message=data["input"], user_waid=data["user_waid"], created_by="user")

        return {"agent_outcome": agent_outcome, "chat_history": data["chat_history"]}

    def execute_tools(data):
        agent_action = data["agent_outcome"]
        output = tool_executor.invoke(agent_action)

        # updated_chat_history = data["chat_history"] + [str(output)]
        # supa_insert_data(message=str(output), user_waid=data["user_waid"], created_by="system")

        return {"intermediate_steps": [(agent_action, str(output))], "chat_history": data["chat_history"]}

    def should_continue(data):
        if isinstance(data["agent_outcome"], AgentFinish):
            return "end"
        else:
            return "continue"

    # -------- DEFINE THE GRAPH ---------#

    from langgraph.graph import END, StateGraph
    from langgraph.checkpoint import MemorySaver

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", run_agent)
    workflow.add_node("action", execute_tools)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "action",
            "end": END,
        },
    )

    workflow.add_edge("action", "agent")


    checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer)

    # output = {"chat_history": []}
    # while True:
    #     user_input = input("User: ")
    #     if user_input.lower() in ["quit", "exit", "q"]:
    #         print("Goodbye!")
    #         break
    #     output["chat_history"] = output["chat_history"] + [user_input]
    #     print(f"Chat history: {output['chat_history']}")
    #     output = app.invoke({"input":user_input, "chat_history": output["chat_history"]}, config={"configurable": {"thread_id": 1}})
    #     print(f"Final answer: {output.get('agent_outcome').return_values['output']}")

    return app

# create_agent()
