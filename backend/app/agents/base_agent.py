"""
Base AI Agent implementation using LangChain and Azure OpenAI
Provides foundation for specialized agents with tool calling capabilities
"""
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import AzureChatOpenAI
from langchain.tools import BaseTool
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Dict, Any, Optional
import structlog
from abc import ABC, abstractmethod
from app.config import settings

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for AI agents with Azure OpenAI integration
    Implements common functionality and tool calling framework
    """
    
    def __init__(self, tools: Optional[List[BaseTool]] = None, **kwargs):
        self.tools = tools or []
        self.llm = self._initialize_llm()
        self.agent = None
        self.agent_executor = None
        
        # Allow subclasses to handle additional initialization
        self._initialize_subclass(**kwargs)
        
        # Setup agent after subclass initialization
        if self.tools:
            self._setup_agent()
    
    def _initialize_subclass(self, **kwargs):
        """Hook for subclass-specific initialization. Override in subclasses."""
        pass
    
    def _initialize_llm(self) -> AzureChatOpenAI:
        """Initialize Azure OpenAI LLM with proper configuration"""
        try:
            llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                openai_api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_deployment=settings.azure_openai_deployment_name,
                temperature=0.1,  # Low temperature for consistent SQL generation
                max_tokens=1000,
                timeout=settings.max_query_timeout,
                max_retries=2
            )
            logger.info("Azure OpenAI LLM initialized successfully")
            return llm
        except Exception as e:
            logger.error("Failed to initialize Azure OpenAI LLM", error=str(e))
            raise
    
    def _setup_agent(self):
        """Setup agent with tools and prompt template"""
        if not self.tools:
            logger.warning("No tools provided to agent")
            return
        
        try:
            prompt = self._get_prompt_template()
            self.agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=settings.debug,
                max_iterations=5,
                early_stopping_method="force",
                handle_parsing_errors=True
            )
            logger.info(f"Agent setup completed with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error("Failed to setup agent", error=str(e))
            raise
    
    @abstractmethod
    def _get_prompt_template(self) -> ChatPromptTemplate:
        """Get the prompt template for this agent type"""
        pass
    
    @abstractmethod
    def _get_system_message(self) -> str:
        """Get the system message for this agent type"""
        pass
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent with input data and return results
        Implements error handling and logging
        """
        try:
            if not self.agent_executor:
                raise ValueError("Agent not properly initialized")
            
            # Prepare input for agent
            agent_input = self._prepare_agent_input(input_data)
            
            # Execute agent with timeout and error handling
            result = self.agent_executor.invoke(agent_input)
            
            # Process and format results
            formatted_result = self._process_agent_output(result)
            
            logger.info("Agent execution completed successfully")
            return {
                'success': True,
                'result': formatted_result,
                'input': input_data
            }
            
        except Exception as e:
            logger.error("Agent execution failed", error=str(e), input=input_data)
            return {
                'success': False,
                'error': str(e),
                'input': input_data
            }
    
    def _prepare_agent_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input data for agent execution"""
        return {
            'input': input_data.get('question', ''),
            'context': input_data.get('context', {}),
            'user_id': input_data.get('user_id'),
            'session_id': input_data.get('session_id')
        }
    
    def _process_agent_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and format agent output"""
        return {
            'output': result.get('output', ''),
            'intermediate_steps': result.get('intermediate_steps', []),
            'tool_calls': self._extract_tool_calls(result)
        }
    
    def _extract_tool_calls(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tool call information from agent result"""
        tool_calls = []
        for step in result.get('intermediate_steps', []):
            if len(step) >= 2:
                action, observation = step[0], step[1]
                tool_calls.append({
                    'tool': action.tool,
                    'input': action.tool_input,
                    'output': observation
                })
        return tool_calls
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the agent"""
        if tool not in self.tools:
            self.tools.append(tool)
            self._setup_agent()  # Reinitialize agent with new tools
            logger.info(f"Added tool: {tool.name}")
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent"""
        self.tools = [tool for tool in self.tools if tool.name != tool_name]
        self._setup_agent()  # Reinitialize agent without the tool
        logger.info(f"Removed tool: {tool_name}")
    
    async def aexecute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of execute method"""
        try:
            if not self.agent_executor:
                raise ValueError("Agent not properly initialized")
            
            agent_input = self._prepare_agent_input(input_data)
            result = await self.agent_executor.ainvoke(agent_input)
            formatted_result = self._process_agent_output(result)
            
            logger.info("Async agent execution completed successfully")
            return {
                'success': True,
                'result': formatted_result,
                'input': input_data
            }
            
        except Exception as e:
            logger.error("Async agent execution failed", error=str(e), input=input_data)
            return {
                'success': False,
                'error': str(e),
                'input': input_data
            }


class AgentRegistry:
    """Registry for managing multiple agent instances"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, name: str, agent: BaseAgent):
        """Register an agent with a name"""
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return list(self.agents.keys())
    
    def remove_agent(self, name: str):
        """Remove an agent from registry"""
        if name in self.agents:
            del self.agents[name]
            logger.info(f"Removed agent: {name}")


# Global agent registry
agent_registry = AgentRegistry()
