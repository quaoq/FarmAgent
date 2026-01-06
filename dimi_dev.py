
from rsare.agents.llm.openai_llm import OpenAILLM
from rsare.agents.agent.agent import Agent

from rsare.apps.gma.database import Database


def main(query="Hi there!"):

    llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)
    
    agent = Agent(
        name="agent",
        llm=llm,
        system_message="You are a geospatial agent helping with fetching images from a database!",
        toolsets=[Database]
    )    
    response = agent.run(input="Get Sentinel-1 SAR scenes from 2018-08-01 to 2018-08-10 over Shanghai (i.e., 121.0, 30.0, 123.0, 32.0)!")
    print(response)

if __name__ == "__main__":
    main()
