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

TASK_INPUT_1_1 = """Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites, covering the Shanghai region (121.0–123.0°E, 30.0–32.0°N) and the period from 2018-08-08 to 2018-08-10, load all available SAR scenes and clip a 500-m border buffer to remove edge artefacts.

Load global shoreline data and apply a 1-km shoreline buffer as a spatial mask to restrict each SAR scene to valid offshore analysis areas .

Detect vessels using the VH polarization band with a two-parameter CFAR configuration, applying a 200 × 200-pixel inner window and a 600 × 600-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

For each CFAR detection, extract an 80 × 80-pixel dual-polarization (VH + VV) SAR tile. Apply a pre-trained neural network to confirm vessel presence, filter out false detections, and estimate vessel length.

Finally, report the total number of detected vessel activities during the study period and the total number of vessels."""

TASK_INPUT_1_2 = """Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites, covering the Shanghai region (121.0–123.0°E, 30.0–32.0°N) and the period from 2018-08-08 to 2018-08-10, load all available SAR scenes and clip a 500-m border buffer to remove edge artefacts.

Load global shoreline data and apply a 1-km shoreline buffer as a spatial mask to restrict each SAR scene to valid offshore analysis areas .

Detect vessels using the VH polarization band with a two-parameter CFAR configuration, applying a 200 × 200-pixel inner window and a 600 × 600-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

For each CFAR detection, extract an 80 × 80-pixel dual-polarization (VH + VV) SAR tile. Apply a pre-trained neural network to confirm vessel presence, filter out false detections, and estimate vessel length.

Load AIS data and match SAR detections to AIS tracks to identify bright vessels (with AIS) and dark vessels (without AIS). 

Finally, report the total number of detected vessel activities during the study period and the total number of vessels."""

TASK_INPUT_1_3 = """Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites, covering the Shanghai region (121.0–123.0°E, 30.0–32.0°N) and the period from 2018-08-08 to 2018-08-10, load all available SAR scenes and clip a 500-m border buffer to remove edge artefacts.

Load global shoreline data and apply a 1-km shoreline buffer as a spatial mask to restrict each SAR scene to valid offshore analysis areas .

Detect vessels using the VH polarization band with a two-parameter CFAR configuration, applying a 200 × 200-pixel inner window and a 600 × 600-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

For each CFAR detection, extract an 80 × 80-pixel dual-polarization (VH + VV) SAR tile. Apply a pre-trained neural network to confirm vessel presence, filter out false detections, and estimate vessel length.

Load environmental data (bathymetry, port distance, sea surface temperature, current speed, chlorophyll) and generate multiband raster stacks for fishing classification. Apply the fishing/non-fishing classifier to high-confidence vessel detections.

Finally, report the total number of detected vessel activities during the study period and the total number of vessels."""

TASK_INPUT_2 = """Using Sentinel-1 GRD SAR imagery from the S1A and S1B satellites over the Gulf of Mexico (-95.0, -94.0, 29.0, 30.0) for the period from 2019-01-01 to 2019-12-31, load all available SAR scenes.

Generate monthly SAR composites using a rolling 6-month median to suppress moving vessels and enhance stationary offshore objects.

Load global shoreline data and apply a 1-km shoreline buffer as a spatial mask to restrict each SAR scene to valid offshore analysis areas .

Detect stationary offshore infrastructure on the monthly median composites using a two-parameter CFAR configuration with a 140 × 140-pixel inner window and a 200 × 200-pixel outer window. Set the detection threshold to 16 for S1A scenes and 19 for S1B scenes.

Load Sentinel-2 optical scenes (RGB + NIR) from the S2A and S2B satellites .For each detected infrastructure candidate, generate 6-month SAR (VH + VV) composites and 6-month Sentinel-2 optical (RGB + NIR) composites . Extract 100 × 100-pixel multimodal tiles centred on each detected structure, and apply a pre-trained multimodal neural network to classify each structure as wind, oil, other, or noise.

Finally, report the total number of detected offshore structures and their spatial distribution."""
def main(query="Hi there!"):
    llm = OpenAILLM(model="gpt-4o-mini", temperature=0.1)
    tools = SARTools()
    agent = Agent(
        name="agent",
        llm=llm,
        system_message=SYSTEM_PROMPT,
        toolsets=[tools]
    )
    # response = agent.run(input=TASK_INPUT_1_1)
    response = agent.run(input=TASK_INPUT_1_3)

    # tools.state.load_infra =  True
    # response = agent.run(input=TASK_INPUT_2)

    print(response)
    # args = {'date1': '2018-08-08', 'date2': '2018-08-10', 'region': [121.0, 30.0, 123.0, 32.0], 'satellite': 'S1AB', 'collection': 'COPERNICUS/S1_GRD'}
    # agent.tools_map['load_SAR_scenes'](**args)

if __name__ == "__main__":
    main()
