# NYU Public Test Corpus

This snapshot contains 16 English UTF-8 TXT documents for future upload, chunking, retrieval, citation, and grounded-answer tests. Retrieved on September 7, 2026 (UTC), September 6 in New York. These are extracted page texts, not generated summaries.

## Contents

- `policies/`: University Student Conduct Policy, effective August 13, 2026.
- `msds/`: curriculum, program overview, admissions requirements, admissions and general FAQs, admissions ambassadors, tracks, industry concentration, capstone, summer research, financial aid, student resources, career information, and the 2026–2027 degree bulletin.
- [manifest.json](manifest.json): source URLs, retrieval timestamps, file sizes, and SHA-256 hashes.
- [Test cases](../../nyu-test-cases.jsonl): 11 answerable questions with source anchors and line numbers, plus one insufficient-evidence case. Paths in these cases are relative to `evals/`.

## Using the Materials

1. Upload only the TXT files under `policies/` and `msds/`. Start with the conduct policy for a single-document test, then add the MSDS files for retrieval across documents.
2. Keep the README, manifest, and test cases outside the retrieval index to avoid answer leakage.
3. Ask the test questions and check retrieved evidence separately from answer correctness. Evidence entries identify sufficient source passages, not an exhaustive list of every valid duplicate source.
4. Use the insufficient-evidence case to check that the system does not invent a personal schedule.

No RAG runner or Python implementation is added here. The questions are prepared evaluation data; no live retrieval or model-quality evaluation has been run.

## Extraction and Scope

Main page content was read through a browser after direct downloads returned HTTP 403. Global navigation and footers were excluded. Paragraphs, headings, course codes, and table cell relationships are retained as plain text; tabs separate table cells. FAQ answers were expanded before extraction. The bulletin combines Overview, Curriculum (including the expanded concentration requirements), Sample Plan of Study, Outcomes, and Policies. Standalone accordion icons and excess whitespace were removed. Hidden duplicate FAQ markup was excluded.

Each TXT contains its title, source URL, retrieval timestamp, and a list of referenced links. A referenced URL does not mean that its target content is in this corpus. Only files in the manifest are included. Source page text may contain older cohorts, course names, or links; these are preserved instead of silently reconciled.

The scope covers the public MSDS program and admissions navigation, related CDS student-resource pages, and the linked degree bulletin. It is not a crawl of all NYU websites. External course sites, syllabi, forms, linked PDFs, videos, poster images, Google Drive files, and the pre-approved electives spreadsheet are not converted in this snapshot. Image-only and video-only content is not transcribed.

The [MS Student Handbook](https://docs.google.com/document/d/1pgDKSQeEEZq58kugHDaF_fhMsQ6Qm-myRLXKgwAB6vo/edit?usp=sharing) is not included: the curriculum page states that an NYU email address is required. Other linked resources were not tested for authentication requirements.

University policies, admissions cycles, contacts, and requirements can change. Evaluate against this dated snapshot and refresh the corpus before relying on it for current decisions. Original content belongs to NYU and the respective rights holders; this conversion does not grant a new license.

## Source Index

| TXT file | Official source |
| --- | --- |
| [msds/admissions-requirements.txt](msds/admissions-requirements.txt) | [Master’s in Data Science: Admissions Requirements](https://cds.nyu.edu/admissions/masters-in-data-science-admissions-req/admissions-requirements/) |
| [msds/curriculum.txt](msds/curriculum.txt) | [Master's in Data Science: Curriculum — NYU CDS](https://cds.nyu.edu/masters-in-data-science-curriculum/) |
| [msds/data-science-ms-bulletin.txt](msds/data-science-ms-bulletin.txt) | [Data Science (MS) — NYU Bulletins](https://bulletins.nyu.edu/graduate/arts-science/programs/data-science-ms/) |
| [msds/masters-in-data-science-admissions-ambassadors.txt](msds/masters-in-data-science-admissions-ambassadors.txt) | [Master’s in Data Science: Admissions Ambassadors — NYU CDS](https://cds.nyu.edu/masters-in-data-science-admissions-ambassadors/) |
| [msds/masters-in-data-science-capstone.txt](msds/masters-in-data-science-capstone.txt) | [Master’s in Data Science: Capstone Project — NYU CDS](https://cds.nyu.edu/masters-in-data-science-capstone/) |
| [msds/masters-in-data-science-faq-general.txt](msds/masters-in-data-science-faq-general.txt) | [Master’s in Data Science: FAQ (General) - NYU Center for Data Science](https://cds.nyu.edu/masters-in-data-science-faq-general/) |
| [msds/masters-in-data-science-faq.txt](msds/masters-in-data-science-faq.txt) | [Master’s in Data Science: FAQ (Admissions) — NYU CDS](https://cds.nyu.edu/masters-in-data-science-faq/) |
| [msds/masters-in-data-science-financial-aid-fellowships.txt](msds/masters-in-data-science-financial-aid-fellowships.txt) | [Master’s in Data Science: Financial Aid & Scholarships](https://cds.nyu.edu/masters-in-data-science-financial-aid-fellowships/) |
| [msds/masters-in-data-science-industry-concentration.txt](msds/masters-in-data-science-industry-concentration.txt) | [Master’s in Data Science: Industry Concentration](https://cds.nyu.edu/masters-in-data-science-industry-concentration/) |
| [msds/masters-in-data-science-overview.txt](msds/masters-in-data-science-overview.txt) | [Master's in Data Science: Program Overview — NYU CDS](https://cds.nyu.edu/masters-in-data-science-overview/) |
| [msds/masters-in-data-science-summer-research-initiative.txt](msds/masters-in-data-science-summer-research-initiative.txt) | [Summer Research Initiative for Master’s Students](https://cds.nyu.edu/masters-in-data-science-summer-research-initiative/) |
| [msds/masters-in-data-science-tracks.txt](msds/masters-in-data-science-tracks.txt) | [Master’s in Data Science: Tracks — NYU CDS](https://cds.nyu.edu/masters-in-data-science-tracks/) |
| [msds/student-career-development-professional-career-information.txt](msds/student-career-development-professional-career-information.txt) | [Data Science Salary: Career Information — NYU CDS](https://cds.nyu.edu/student-career-development-professional-career-information/) |
| [msds/student-career-development-professional-development-overview.txt](msds/student-career-development-professional-development-overview.txt) | [Student Career & Professional Development: Overview](https://cds.nyu.edu/student-career-development-professional-development-overview/) |
| [msds/student-resources-overview.txt](msds/student-resources-overview.txt) | [Student Resources Overview - NYU Center for Data Science](https://cds.nyu.edu/student-resources-overview/) |
| [policies/university-student-conduct-policy.txt](policies/university-student-conduct-policy.txt) | [University Student Conduct Policy](https://www.nyu.edu/about/policies-guidelines-compliance/policies-and-guidelines/university-student-conduct-policy.html) |
