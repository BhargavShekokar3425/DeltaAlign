# After E16: bounded real-topology ingestion and initial-quality gate

Status: selected after E16; source descriptions checked on 2026-10-03. This is a follow-up design, not a completed ingestion or dataset experiment. E13–E16 use synthetic topology; timing repetition does not establish relevance to real graph structure. Before longer or larger runs, ingest one bounded real topology reproducibly and measure initial objective fitness and exact maintenance.

The candidate is [SNAP email-Eu-core](https://snap.stanford.edu/data/email-Eu-core.html): the source describes anonymized directed institution-internal communication, reports 1,005 nodes and 25,571 links, and supplies department labels. Those labels are communities, not cross-network correspondence, and must not enter this topology-only descriptor. The page cites Yin et al. (2017) and Leskovec et al. (2007).

Do not silently substitute the [temporal variant](https://snap.stanford.edu/data/email-Eu-core-temporal.html): it reports 986 nodes, 332,334 events and 24,929 static directed edges over 803 days; its IDs differ from the static core. Source descriptions of WCC equivalence and numerical edge totals need reconciliation from actual files, not assumed identity. Temporal repeated messages are not all effective edge changes.

## First deliverable: provenance and preprocessing

Fetch the static core edge file from its source link, record retrieval date, original URL/redirects and compressed/uncompressed SHA256. Inspect any supplied reuse terms and citation instructions; record what is present or unresolved without inventing a license. Keep the raw artifact immutable and avoid assuming a code-package license applies to data.

Parse node IDs and directed links, count comments/records/duplicates/self-loops/reciprocal pairs, and compare raw node/edge counts to the source. Preserve every observed node even if removing a self-loop isolates it. Project to a simple undirected graph by removing self-loops and collapsing duplicate/reciprocal links, then remap sorted original IDs to contiguous fixed vertices. Record every count change, components, isolates, degree summaries and clustering. No largest-component filtering or favorable subgraph selection. Test parser/projection on small fixtures before using downloaded data. Preserve the ID map only for provenance; matching features never consume identifiers or department labels.

## Then freeze the first benchmark

After inspecting effective graph size/density and headroom, preregister a bounded full-versus-refined/control test without editing historical kernels. Use fixed hidden permutation and observation noise to construct a graph pair. Explicitly label truth as **constructed correspondence on real topology**, not a naturally observed mapping. No original temporal-dynamics claim from synthetic edits on a static graph.

Start with no-update and initial-quality controls before stream timings. Retain NC/EC/S3 and descriptor collisions/ties, frozen normalization, method-specific setup, exact feature/cost/mapping checks, support and computed-entry counts, worker RSS and stage/total latency. Seed repetition of permutation/noise/edit construction on this one graph is not independent real-dataset replication. Define the eventual noise/budget/stream length before measurements and retain failure conditions. Select longer streams only after this bounded correctness/resource gate; do not tune descriptors on reported evaluation seeds.

A real topology can improve external relevance even if initial accuracy is poor or locality covers most nodes. Such failures constrain the objective and applicability; component efficiency still counts positively where measured. This gate establishes neither novelty nor parallel decomposition. The next artifact is `docs/real_topology_provenance.md` plus an ingestion module/tests and a preregistered experiment, not a promised accuracy/speedup number.
