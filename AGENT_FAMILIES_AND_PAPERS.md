# FarmAgent Agent Families and Paper Mapping

This repo includes **10 controller families** for architecture-comparison experiments in farm scenarios.  
Goal: measure comparative behavior across long-horizon tasks, not claim one universal winner.

## Agent families

1. `farm_baseline_react`  
   Plain-language: direct reason-and-act baseline.  
   Technical: standard ReAct tool-use loop.  
   Paper: https://arxiv.org/abs/2210.03629

2. `farm_planner_executor`  
   Plain-language: plan first, execute in milestones.  
   Technical: planning context injection before step execution.  
   Grounding: planning-augmented ReAct workflow.

3. `farm_reflective_memory`  
   Plain-language: remembers short lessons from prior turns.  
   Technical: reflection-memory snippets added to prompt context.  
   Paper: https://arxiv.org/abs/2303.11366

4. `farm_skill_rag`  
   Plain-language: consults local skill playbooks.  
   Technical: retrieval over local skills and top-k insertion.  
   Paper: https://arxiv.org/abs/2005.11401

5. `farm_multi_specialist`  
   Plain-language: combines recommendations from specialist roles.  
   Technical: role-decomposition prompting plus merged action synthesis.  
   Reference: https://arxiv.org/abs/2308.08155

6. `farm_adaptive_verifier`  
   Plain-language: verifies high-risk actions before executing.  
   Technical: uncertainty-triggered verification guidance.  
   Reference: https://arxiv.org/abs/2305.11738

7. `farm_rewoo_modular`  
   Plain-language: breaks tasks into plan/work/solve stages.  
   Technical: ReWOO-like modular decomposition.  
   Paper: https://arxiv.org/abs/2305.18323

8. `farm_tree_search`  
   Plain-language: explores and scores multiple action branches.  
   Technical: candidate branching with limited backtracking.  
   Paper: https://arxiv.org/abs/2310.04406

9. `farm_critic_refiner`  
   Plain-language: action proposal followed by critique and revision.  
   Technical: actor-critic refinement loop with precondition checks.  
   Reference: https://arxiv.org/abs/2305.11738

10. `farm_graph_memory`  
    Plain-language: tracks structured task facts and dependencies.  
    Technical: graph-style memory retrieval and contradiction checks.  
    Paper: https://arxiv.org/abs/2308.09687

## Agent2Agent (A2A)

- Supported as A2A OFF and A2A ON packs.
- Typed routing policy:
  - `WeatherApp` -> `weather_expert_app_agent`
  - `SensorApp` -> `sensor_expert_app_agent`
  - `TractorApp`, `FieldOpsApp` -> `machinery_expert_app_agent`
  - `FarmWorldApp`, `DroneApp`, `RobotApp` -> `operations_expert_app_agent`
- A2A framing: https://developers.googleblog.com/es/a2a-a-new-era-of-agent-interoperability/

## Paper framing (safe)

- Report architecture tradeoffs and ablations, not absolute superiority claims.
- Treat long-horizon failures as informative for analysis.
- Keep results reproducible via shared suite configs and fixed execution interfaces.
