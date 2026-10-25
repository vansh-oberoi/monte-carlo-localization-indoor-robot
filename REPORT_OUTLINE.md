# Report Outline — AISR Project

**Project:** Monte Carlo Localization of an Indoor Robot Using a 2D Map and Simulated LiDAR  
**Course:** CSAI4014 Algorithms for Intelligent Systems and Robotics

This outline is a drafting aid, not a substitute for the instructor's sample report. Before submission, transfer content into the supplied Word/Overleaf template and preserve the required page layout and common title page.

## Mandatory front matter (use the prescribed order)
1. Common title page from the sample; fill the actual project number, group number, batch, all member names and SAP IDs, course/faculty details.
2. Declaration signed by all members.
3. Index / Table of Contents with page numbers.
4. List of Figures and List of Tables.
5. Writing Allocation table.
6. Abstract (150–200 words).

## 1. Introduction
Explain indoor mobile-robot localization, odometry drift, range sensing, and why localization matters. Cite sources for factual claims.

## 2. Problem Statement and Objectives
Define the known-map pose-estimation problem. Give 3–5 measurable objectives, assumptions, and limitations.

## 3. Literature and Industry Review
Review at least five relevant papers, books, standards, or industry systems. Compare their approaches and identify a supported gap. Verify sources and cite them in the text.

## 4. NOVELTY (mandatory; 1–2 pages)
State 3–5 precise claims about what this implementation adds beyond the standard example. Possible candidates to investigate—not pre-approved claims—include repeatable multi-seed evaluation, particle-count/compute trade-offs, and systematic error analysis. Retain only claims supported by comparisons and actual results.

## 5. Syllabus Mapping and Theory
Map relevant AISR topics to implementation modules. Explain Bayesian filtering, the motion model, measurement likelihood, weight normalization, pose estimate, and resampling with equations.

## 6. System Design
Include a block diagram and describe map, robot pose, movement/odometry, simulated LiDAR, particle filter, and visualization/logging components.

## 7. Methodology and Algorithms
Describe the simulation loop, particle initialization, prediction, sensor update, normalization, pose estimation, and resampling. Include a flowchart and pseudocode.

## 8. Simulation Setup
State Python and package versions, operating environment, map dimensions and obstacles, beam count, sensor range/noise, motion-noise settings, particle counts, seeds, and exact commands used.

## 9. Results and Analysis
Include numbered plots/tables for paths, position error, and the experiment comparisons. Report trial counts, summary statistics, and runtime. Discuss failures and limitations. Only include values from actual runs; keep raw CSV outputs with the project.

## 10. CONTRIBUTION (mandatory)
Complete the supplied contribution table for every actual group member. Describe specific code modules, algorithms, tests, and experiments. Each member signs their row in the printed copy. Claims must be traceable to authentic commits, report sections, and the video.

## 11. Co-learning Reflection
Each member writes 5–8 lines describing what they learned independently, learned from teammates, and taught others.

## 12. Conclusion and Future Scope
Summarize findings supported by the results. Discuss realistic next steps such as better motion/sensor models, adaptive particle counts, or integration with a robotics simulator.

## 13. References
Include at least eight real, verified references in IEEE style, numbered in order of first citation. Every reference must be cited in the report body. Verify publication metadata; do not use invented citations.

## Appendix: Links and Logs
Include the GitHub URL, the unlisted YouTube video URL, dated team meeting log (duration, attendees, decisions), and completed peer-assessment sheets.

## Formatting checklist from the instructions
- A4 portrait; left margin 3.0 cm; other margins 2.5 cm.
- Single-line border on every page, including title page.
- Times New Roman; body 12 pt, 1.5 line spacing, justified; section headings 14 pt bold; subsection headings 12 pt bold; title 18–20 pt bold.
- Page numbers centered at bottom except title page. Roman numerals for front matter; Arabic numerals from Section 1 onward.
- Number and caption every figure/table and refer to each in the text.
- Total length 25–35 pages including front matter; print single-sided and submit the mandatory bound hard copy.
- Divide writing equally and complete the Writing Allocation table.

**Important:** The instructions say the report must follow the provided sample exactly. This Markdown file does not implement the required Word/PDF page design.