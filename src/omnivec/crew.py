"""CrewAI wiring used only for the final report-writing step."""

from collections.abc import Callable
from typing import cast

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task


@CrewBase
class AssetLibrarianCrew:
    """CrewAI configuration that turns saved analysis into a markdown report."""

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
        inventory_analysis_task = cast(Callable[[], Task], self.inventory_analysis_task)
        return Task(
            config=self.tasks_config["report_task"],  # type: ignore[index]
            context=[inventory_analysis_task()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )


def create_asset_librarian_crew(llm_model: str) -> Crew:
    """Build a CrewAI crew with the configured model."""

    crew_builder = AssetLibrarianCrew()
    setattr(crew_builder, "llm_model", llm_model)
    return crew_builder.crew()
