"""
Concrete implementation of a SQL Agent for Text-to-SQL tasks.
Inherits from BaseAgent and uses specialized SQL tools.
"""

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from typing import List

from ..agents.base_agent import BaseAgent
from ..tools.schema_analyzer_tool import SchemaAnalyzerTool
from ..tools.sql_execution_tool import SQLExecutionTool
from ..database.connection_manager import DatabaseManager
import structlog

logger = structlog.get_logger(__name__)

class SQLAgent(BaseAgent):
    """
    An AI Agent specialized in converting natural language questions to SQL queries
    and executing them to get answers from a database.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the SQLAgent.

        Args:
            db_manager: An instance of DatabaseManager to interact with the database.
        """
        self.db_manager = db_manager
        # The super().__init__() call is placed in _initialize_subclass
        # to ensure tools are ready before the base agent setup runs.
        super().__init__()
        logger.info("SQLAgent initialized with database manager.")

    def _initialize_subclass(self, **kwargs):
        """
        Initializes tools specific to the SQLAgent and then calls the parent
        initializer to set up the agent with these tools.
        """
        tools = self._get_tools()
        # This was intentionally left blank in the base class. 
        # We are now using it to set up the agent with its specific tools.
        self.tools = tools
        logger.info(f"SQLAgent tools initialized: {[tool.name for tool in tools]}")


    def _get_tools(self) -> List[BaseTool]:
        """
        Instantiates and returns the list of tools available to the SQL agent.
        """
        return [
            SchemaAnalyzerTool(db_manager=self.db_manager),
            SQLExecutionTool(),
        ]

    def _get_system_message(self) -> str:
        """
        Returns the system message that defines the agent's role, capabilities,
        and constraints.
        """
        return """
        You are a powerful and intelligent Business Analytics Assistant.
        Your goal is to answer user questions by converting them into SQL queries
        and executing them against a PostgreSQL database.

        You have access to the following tools:
        - `schema_analyzer`: Use this to understand the database schema, including tables, columns, and relationships. Always look at the schema before writing a query.
        - `sql_execution`: Use this to execute SELECT queries. You cannot use any other type of query (no UPDATE, DELETE, INSERT, etc.).

        Your workflow should be:
        1.  When you receive a question, first decide if you need to understand the database structure. If you are not 100% certain about the table and column names, use the `schema_analyzer` tool.
        2.  Based on the schema and the user's question, construct a valid PostgreSQL SELECT query.
        3.  Execute the query using the `sql_execution` tool.
        4.  Analyze the results from the `sql_execution` tool. If the result is an error or not what you expected, try to correct your query and execute it again.
        5.  Based on the final query result, formulate a clear, concise, and helpful answer to the user's original question in natural language.
        6.  Your final answer should be just the natural language response. Do not include the SQL query in your final output.

        Important rules:
        - Always use the `schema_analyzer` if you have any doubt about the database structure.
        - NEVER execute a query that is not a SELECT query.
        - Provide your final answer in the same language as the user's question.
        """

    def _get_prompt_template(self) -> ChatPromptTemplate:
        """
        Creates and returns the chat prompt template for the agent.
        This template includes the system message, placeholders for memory (chat history),
        and the user's input.
        """
        return ChatPromptTemplate.from_messages([
            ("system", self._get_system_message()),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
