# Validation Hooks — S-ASM-CC v5.3

Dedicated to Ali Sayed Muhammad Osman (1957-2022)

These scripts cross-check that the physics engine, the cancer
database, the S-ASM-CC simulation, and the hardware blueprint
all agree with each other. Run them whenever ANY of these change:

  - ~/sonoluminescence/02_simulations/**/*.py
  - ~/oncotripsy_full_system/src/cancer_database.py
  - ~/oncotripsy_full_system/src/sasmcc_v53.py
  - ~/oncotripsy_full_system/hardware/blueprint_v2/*

## Scripts

  check_blueprint_vs_database.py
      Verifies every frequency/transducer in cancer_database.py
      has a matching transducer in the hardware PARTS.csv,
      and that the PNP/frequency ranges in the CONFIG.json
      "Physics Constraints" table match cancer_database.py exactly.

  check_engine_consistency.py
      Re-runs sasmcc_v53.py and confirms threshold agreement
      stays under 5% and selectivity direction stays correct
      for all 9 cancer types — same checks as PhysicsEngineValidator,
      run standalone so it can be scripted/automated (cron, CI, etc).

  check_knowledge_graph_sync.py
      Confirms knowledge_graph_data.json version/completed-files
      list matches what's actually on disk in both project dirs.

## Usage
  cd ~/oncotripsy_full_system/hooks
  python3 check_blueprint_vs_database.py
  python3 check_engine_consistency.py
  python3 check_knowledge_graph_sync.py
