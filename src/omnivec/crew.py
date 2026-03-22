from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class AssetLibrarianCrew:
    """CrewAI report generator for Omnivec."""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    llm_model = "openai/gpt-4o-mini"

    @agent
    def inventory_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["inventory_analyst"],  # type: ignore[index]
            llm=self.llm_model,
            reasoning=True,
            verbose=False,
        )

    @agent
    def librarian_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["librarian_writer"],  # type: ignore[index]
            llm=self.llm_model,
            verbose=False,
        )

    @task
    def inventory_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["inventory_analysis_task"],  # type: ignore[index]
        )

    @task
    def report_task(self) -> Task:
        return Task(
            config=self.tasks_config["report_task"],  # type: ignore[index]
            context=[self.inventory_analysis_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )
