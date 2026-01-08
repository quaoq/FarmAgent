from rsare.agents.llm.openai_llm import OpenAILLM
from rsare.agents.agent.agent import Agent

from rsare.apps.gma.tools_list import SARTools

SYSTEM_PROMPT = """You are an expert assistant who solves tasks by reasoning step by step and calling tools via function calling.

You must always follow the cycle:
1. Thought: explain what you are thinking and why tools are needed.
2. Tool Call: use the available function calling feature to call ONE OR MORE tools in parallel when appropriate.
3. Observation: (will be provided by the system; you NEVER generate this).

=== THOUGHT RULES ===
- Always explain your reasoning in natural language before calling tools.
- Clearly state which tools you need and why.
- When multiple tools can be called in parallel (they don't depend on each other), explicitly mention this in your thought.
- Never include tool call details in the Thought - use function calling instead.


=== TOOL CALLING RULES ===
- Use the function calling feature to call tools - do NOT output JSON manually.
- **PREFER PARALLEL CALLS**: When you need to call multiple tools that are independent (don't depend on each other's results), call them ALL in a single function calling request. This is more efficient and faster.
- **WHEN TO CALL MULTIPLE TOOLS IN PARALLEL**:
  * When gathering information from multiple independent sources (e.g., checking weather in multiple cities, querying different databases)
  * When performing multiple independent operations (e.g., reading multiple files, checking multiple statuses)
  * When tools don't require the output of other tools as input
- **WHEN TO CALL ONE TOOL AT A TIME**:
  * When a tool's output is needed as input for another tool
  * When tools have dependencies on each other
- Provide real values for all required parameters, not placeholders.
- If a tool takes no input, the function calling will handle empty parameters automatically.
- The system will automatically format and execute your tool calls in parallel when possible.


=== OBSERVATION RULES ===
- Do NOT generate Observation; the system will insert it after tool calls complete.
- When multiple tools are called in parallel, you will receive observations for all of them.  """

TASK_INPUT = """Using Sentinel-1 GRD SAR imagery over Shanghai (121.0, 123.0, 30.0, 32.0)
from 2018-08-08 to 2018-08-10, load all available SAR scenes and apply
radiometric calibration, thermal noise removal, terrain correction, and
a 500-m border buffer to remove edge artefacts. Detect vessels using the
VH polarization band with a two-parameter CFAR configuration employing a
200 × 200 pixel inner window and a 600 × 600 pixel outer window, calibrated
with time-dependent thresholds to maintain a 60% detection rate for vessels
15–20 m in length. Exclude detections within 1 km of the global shoreline
and remove stationary objects from vessel detections to ensure that only
moving vessels are retained. For each CFAR detection, extract 80 × 80 pixel
dual-polarization (VH+VV) SAR tiles and apply the pre-trained neural network
to confirm vessel presence, filter out false detections, and estimate vessel
length. Finally, report the total number of detected vessel activities during
the study period and the number of vessels."""


def main(query="Hi there!"):
    llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)

    SARToolsCls = SARTools()
    agent = Agent(
        name="agent",
        llm=llm,
        system_message=SYSTEM_PROMPT,
        toolsets=[SARToolsCls]
    )
    # response = agent.run(input=TASK_INPUT)
    # print(response)
    args = {'date1': '2018-08-08', 'date2': '2018-08-10', 'region': [121.0, 30.0, 123.0, 32.0], 'satellite': 'S1AB', 'collection': 'COPERNICUS/S1_GRD'}
    agent.tools_map['load_SAR_scenes'](**args)

if __name__ == "__main__":
    main()
