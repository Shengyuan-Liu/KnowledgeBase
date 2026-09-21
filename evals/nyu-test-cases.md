# NYU Evaluation Cases and Evidence

This is a review copy of [nyu-test-cases.jsonl](nyu-test-cases.jsonl): **25 single-turn cases, 20 answerable and 5 unanswerable**. It evaluates the frozen `nyu-public-2026-09-07` corpus, not current NYU requirements. Original case IDs are preserved; answer points have been separated where useful for scoring.

All evidence below is copied verbatim from the local TXT snapshot. Corpus text is unchanged. Original sources and snapshot hashes are in the [manifest](materials/nyu/manifest.json).

## Revision 2: aligned question scope

This revision makes the requested scope explicit for policy coverage, off-campus
conditions, degree-plan caveats, and waiver materials. The CPT question no longer
supplies its expected timing facts. Tuition scoring no longer requires an unasked
external-link mention; summer scoring accepts a direct answer to the summer question.
Historical run snapshots remain unchanged. Results are not directly comparable to
revision 1 because the question/scoring input hash changed.

## Annotation format

- `id`: stable case identifier; `category`: the main evaluation behavior.
- `question`: the input question. `answerable` is relative to the saved corpus.
- `corpus_id`: the source snapshot used to establish the expected answer.
- `expected_answer_points`: a list of required semantic points; numbering starts at 1. Equivalent wording is acceptable.
- `evidence`: sufficient supporting passages for answerable cases. `file` is relative to `evals/`; `anchor` is a section label in that file.
- `line` / `end_line`: one-based, inclusive source lines containing the quoted span. `line` now points to the actual quote rather than only a section heading.
- `start_offset` / `end_offset`: zero-based Unicode character offsets into the complete UTF-8-decoded TXT file, with an exclusive end. They use the same coordinate system as stored chunk offsets, including the file's title and source metadata. These are not byte offsets.
- `quote`: exact source text. Thus `text[start_offset:end_offset] == quote`, including original whitespace and tabs.
- `supports_answer_points`: one-based indices into the case's expected answer points. Multiple passages can jointly support a point; a mapping alone does not mean that any one fragment is sufficient.
- `scoring_notes`: case-specific distinctions to retain when judging answers.
- `unanswerable_reason` / `context_evidence`: why a question cannot be answered and related passages that explain the limitation. These passages are **not positive retrieval targets**; unanswerable cases keep `evidence: []` and context passages have no answer-point mappings.

## Scoring guidance

1. For answerable cases, inspect whether retrieved chunks contain the evidence needed for each answer point. A matching filename or section heading alone is not a hit. Because passages may span several chunks, evaluate their combined coverage rather than requiring the whole quote inside one chunk. Overlapping chunks must not inflate the score.
2. The annotated passages are sufficient references, not an exhaustive list of all equivalent passages in duplicate sources. Valid alternative passages should be accepted after verification against the frozen corpus.
3. Score answer-point coverage semantically, and record unsupported claims and citation errors separately. Do not use whole-answer string equality or a keyword count as a correctness score. A valid citation number alone does not prove support.
4. For unanswerable cases, score explicit acknowledgment of missing information and absence of invented specifics. Do not apply positive-evidence Hit@k or Recall@k to these cases. Related retrieved chunks do not make the requested detail answerable.
5. These are development and regression cases, not held-out test evidence or proof of system quality. Follow-up resolution and deletion behavior need separate workflow tests. Record model, chunking settings, Top-k, and latency with future evaluation results.
6. Index only the corpus TXT documents. Keep this file, the JSONL, README, and manifest outside the retrieval index to avoid answer leakage.

## Case index

| # | ID | Category | Answerable |
| --- | --- | --- | --- |
| 1 | `policy-scope` | factual | Yes |
| 2 | `policy-fire` | factual | Yes |
| 3 | `policy-ai-impersonation` | factual | Yes |
| 4 | `policy-off-campus` | factual | Yes |
| 5 | `msds-credits` | multi_evidence | Yes |
| 6 | `msds-gpa` | multi_evidence | Yes |
| 7 | `msds-independent-study` | factual | Yes |
| 8 | `msds-waiver` | multi_evidence | Yes |
| 9 | `msds-industry` | multi_evidence | Yes |
| 10 | `msds-research` | factual | Yes |
| 11 | `msds-online` | factual | Yes |
| 12 | `missing-personal-schedule` | unanswerable | No |
| 13 | `msds-admissions-prerequisites` | multi_evidence | Yes |
| 14 | `msds-gre-submission` | multi_evidence | Yes |
| 15 | `msds-tracks-change` | multi_evidence | Yes |
| 16 | `msds-working-enrollment` | multi_document | Yes |
| 17 | `msds-pathbreaker-fall2027` | temporal | Yes |
| 18 | `msds-capstone-fall2026-deadline` | temporal | Yes |
| 19 | `policy-effective-date` | temporal | Yes |
| 20 | `msds-cpt-source-context` | source_comparison | Yes |
| 21 | `msds-career-advising` | multi_evidence | Yes |
| 22 | `missing-fall2027-application-deadline` | unanswerable | No |
| 23 | `missing-personal-scholarship-award` | unanswerable | No |
| 24 | `missing-personal-capstone-team` | unanswerable | No |
| 25 | `missing-exact-tuition-bill` | unanswerable | No |

## 1. policy-scope

**Question:** Which NYU student levels and organizations are covered by the conduct policy, and which schools and locations does it cover?

**Answerable:** Yes

**Expected answer points:**

1. The policy covers undergraduate and graduate students and Student Organizations at NYU.
2. It applies across all NYU schools and locations, including Study Away Sites and Portal Campuses.

### Supporting evidence 1

Source: [materials/nyu/policies/university-student-conduct-policy.txt, lines 26–26](materials/nyu/policies/university-student-conduct-policy.txt#L26-L26)

Section: I. STATEMENT OF POLICY  
Characters: `[1591, 1827)`

Supports answer points: 1, 2.

```text
The standards of non-academic misconduct set forth in this policy are applicable to all undergraduate and graduate students and Student Organizations at NYU, in all schools and locations, including Study Away Sites, and Portal Campuses.
```

## 2. policy-fire

**Question:** What should a student do when a fire alarm sounds?

**Answerable:** Yes

**Expected answer points:**

1. Immediately exit the facility or building when a fire alarm or other emergency notification sounds.

**Scoring notes:** The source states prohibited conduct negatively: failing to exit immediately. A correct answer expresses the corresponding required action.

### Supporting evidence 1

Source: [materials/nyu/policies/university-student-conduct-policy.txt, lines 106–106](materials/nyu/policies/university-student-conduct-policy.txt#L106-L106)

Section: G. FIRE SAFETY  
Characters: `[7937, 8060)`

Supports answer points: 1.

```text
4. Failing to immediately exit any facility or building when a fire alarm or other emergency notification has been sounded.
```

## 3. policy-ai-impersonation

**Question:** Does the conduct policy prohibit using generative AI to impersonate another NYU community member without consent?

**Answerable:** Yes

**Expected answer points:**

1. Yes. The policy explicitly includes using generative AI to impersonate another NYU community member without their consent.

### Supporting evidence 1

Source: [materials/nyu/policies/university-student-conduct-policy.txt, lines 132–134](materials/nyu/policies/university-student-conduct-policy.txt#L132-L134)

Section: L. MISREPRESENTATION  
Characters: `[9270, 9762)`

Supports answer points: 1.

```text
2. Assuming or facilitating the use of another person's identity, role, or access through deception or without proper authorization.

This includes, but is not limited to: communicating or acting under the guise, name, identification, access, email address, signature, or indicia of another; communicating under the rubric of an organization, entity, or unit without authorization; use of generative AI to impersonate the identity of another member of the NYU community without their consent.
```

## 4. policy-off-campus

**Question:** Can NYU take disciplinary action for conduct outside the University context, and under what conditions?

**Answerable:** Yes

**Expected answer points:**

1. Yes. NYU may take disciplinary action for conduct outside the University context that substantially disrupts regular University operations.
2. Threatening the health, safety, or security of one or more University community members is another stated basis for action.

**Scoring notes:** These are alternative conditions; do not require both conditions to be satisfied.

### Supporting evidence 1

Source: [materials/nyu/policies/university-student-conduct-policy.txt, lines 184–184](materials/nyu/policies/university-student-conduct-policy.txt#L184-L184)

Section: IV. CONDUCT OUTSIDE THE UNIVERSITY CONTEXT  
Characters: `[12837, 13125)`

Supports answer points: 1, 2.

```text
Notwithstanding, the University may take student disciplinary action for conduct occurring outside the University context, which substantially disrupts the regular operation of the University or threatens the health, safety, or security of one or more members of the University community.
```

## 5. msds-credits

**Question:** How many credits does the MSDS require, how are they distributed across the sample plan semesters, and can the actual plan vary with course availability?

**Answerable:** Yes

**Expected answer points:**

1. The MSDS requires 36 credits in total.
2. The sample plan has four semesters, with 9 credits in each semester.
3. The sample plan is a guide; the actual plan may vary with course availability.

### Supporting evidence 1

Source: [materials/nyu/msds/curriculum.txt, lines 12–12](materials/nyu/msds/curriculum.txt#L12-L12)

Section: Master’s in Data Science: Curriculum  
Characters: `[424, 494)`

Supports answer points: 1.

```text
The curriculum for the MS in Data Science (MSDS) degree is 36 credits.
```

### Supporting evidence 2

Source: [materials/nyu/msds/curriculum.txt, lines 77–100](materials/nyu/msds/curriculum.txt#L77-L100)

Section: 4 Semester Course Plan  
Characters: `[4557, 5227)`

Supports answer points: 2.

```text
YEAR 1 – FALL
Course Title	Credits
DS-GA-1001 Intro to Data Science	3
DS-GA 1002 Probability and Statistics for Data Science	3
General Elective or Track Course	3
TOTAL CREDITS	9
YEAR 1 – SPRING
Course Title	Credits
DS-GA-1003 Machine Learning	3
DS-GA-1004 Big Data	3
General Elective or Track Course	3
TOTAL CREDITS	9
YEAR 2 – FALL
Course Title	Credits
Data Science Elective (see list in required courses section)	3
DS-GA-1006 Capstone Project in Data Science	3
General Elective or Track Course	3
TOTAL CREDITS	9
YEAR 2 – SPRING
Course Title	Credits
General Elective or Track Course	3
General Elective or Track Course	3
General Elective or Track Course	3
TOTAL CREDITS	9
```

### Supporting evidence 3

Source: [materials/nyu/msds/curriculum.txt, lines 75–75](materials/nyu/msds/curriculum.txt#L75-L75)

Section: 4 Semester Course Plan  
Characters: `[4426, 4555)`

Supports answer points: 3.

```text
This is just a guide to help plan out courses for the degree. Your actual course plan may vary based on when courses are offered.
```

## 6. msds-gpa

**Question:** What academic progress requirements does the general FAQ specify?

**Answerable:** Yes

**Expected answer points:**

1. Maintain a minimum GPA of 3.0 each semester.
2. Successfully complete 66% of attempted credits.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-faq-general.txt, lines 43–43](materials/nyu/msds/masters-in-data-science-faq-general.txt#L43-L43)

Section: Is there a minimum GPA for the program?  
Characters: `[2417, 2537)`

Supports answer points: 1, 2.

```text
Yes, each semester, students must maintain a minimum GPA of 3.0 and must successfully complete 66% of credits attempted.
```

## 7. msds-independent-study

**Question:** How many independent study credits may count toward the MSDS?

**Answerable:** Yes

**Expected answer points:**

1. Up to 6 credits of independent study, DS-GA 1010, may count toward the MSDS degree.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-faq-general.txt, lines 85–85](materials/nyu/msds/masters-in-data-science-faq-general.txt#L85-L85)

Section: How many independent study (DS-GA 1010) credits can I apply to the MSDS degree?  
Characters: `[4683, 4776)`

Supports answer points: 1.

```text
MSDS students can apply up to 6 credits of independent study (DS-GA 1010) to the MSDS degree.
```

## 8. msds-waiver

**Question:** Which required Data Science course may be waived, and what materials must be submitted for review according to the general FAQ?

**Answerable:** Yes

**Expected answer points:**

1. Only DS-GA 1002 among the required Data Science courses may be waived.
2. Submit undergraduate or graduate transcripts, highlighting the relevant courses and grades, and the relevant course syllabi for review; transcripts and syllabi must be translated.

**Scoring notes:** A course website is optional if available; do not describe it as mandatory.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-faq-general.txt, lines 51–51](materials/nyu/msds/masters-in-data-science-faq-general.txt#L51-L51)

Section: What is the process for waiving required data science courses?  
Characters: `[2718, 2935)`

Supports answer points: 1.

```text
Of the required Data Science courses, only DS-GA 1002 may be waived. Incoming new students will receive information about the waiver process, but generally the following information needs to be submitted and reviewed:
```

### Supporting evidence 2

Source: [materials/nyu/msds/masters-in-data-science-faq-general.txt, lines 52–54](materials/nyu/msds/masters-in-data-science-faq-general.txt#L52-L54)

Section: What is the process for waiving required data science courses?  
Characters: `[2936, 3263)`

Supports answer points: 2.

```text
– Undergraduate or Graduate Transcripts (must be translated);
– The course(s) that you will be using to waive the required course should be highlighted. The grade(s) you received in the course(s) should be highlighted as well;
– Syllabi of the course(s) that you will be using to waive the required course (Must be translated);
```

## 9. msds-industry

**Question:** What additional coursework and practical experience does the Industry Concentration require?

**Answerable:** Yes

**Expected answer points:**

1. Take DS-GA 1009 Practical Training for Data Science within the first year, worth 3 credits.
2. Take two electives in Big Data or Natural Language Processing, totaling 6 credits.
3. Complete a mandatory internship within the first year of study.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-industry-concentration.txt, lines 16–16](materials/nyu/msds/masters-in-data-science-industry-concentration.txt#L16-L16)

Section: Required Courses  
Characters: `[1223, 1346)`

Supports answer points: 1.

```text
DS-GA 1009: Practical Training for Data Science within the first year of the program (3 credits in fall, spring, or summer)
```

### Supporting evidence 2

Source: [materials/nyu/msds/masters-in-data-science-industry-concentration.txt, lines 17–17](materials/nyu/msds/masters-in-data-science-industry-concentration.txt#L17-L17)

Section: Required Courses  
Characters: `[1347, 1463)`

Supports answer points: 2.

```text
2 electives within the Big Data or Natural Language Processing subject areas (6 credits, see below for more details)
```

### Supporting evidence 3

Source: [materials/nyu/msds/masters-in-data-science-industry-concentration.txt, lines 10–10](materials/nyu/msds/masters-in-data-science-industry-concentration.txt#L10-L10)

Section: Master’s in Data Science: Industry Concentration  
Characters: `[642, 789)`

Supports answer points: 3.

```text
It requires more industry-targeted coursework and a Practical Training experience, including a mandatory internship within the first year of study.
```

## 10. msds-research

**Question:** Can a student outside CDS MSDS participate in the Summer Research Initiative?

**Answerable:** Yes

**Expected answer points:**

1. No. The Summer Research Initiative is restricted to enrolled CDS MSDS students; students outside that program are not eligible.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-summer-research-initiative.txt, lines 12–12](materials/nyu/msds/masters-in-data-science-summer-research-initiative.txt#L12-L12)

Section: Summer Research Initiative for Master’s Students  
Characters: `[1086, 1236)`

Supports answer points: 1.

```text
This initiative is not open to students outside the CDS MS in Data Science program, and external student participation is not considered at this time.
```

## 11. msds-online

**Question:** Is the MSDS offered online?

**Answerable:** Yes

**Expected answer points:**

1. No. The admissions FAQ states that there is no online program.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-faq.txt, lines 21–23](materials/nyu/msds/masters-in-data-science-faq.txt#L21-L23)

Section: Is the degree offered online?  
Characters: `[777, 845)`

Supports answer points: 1.

```text
Is the degree offered online?

No, we do not have an online program.
```

## 12. missing-personal-schedule

**Question:** What room and exact start time is my first MSDS class next Monday?

**Answerable:** No

**Expected answer points:**

1. State that the supplied corpus does not establish the student-specific timetable, classroom, or exact meeting time.
2. Do not invent a classroom or start time, or infer a personal timetable from the sample semester plan.

**Scoring notes:** A generic curriculum plan does not establish an individual class schedule.

**Why no supported answer exists:** The snapshot contains public program information and a sample plan, not the user’s enrolled class schedule.

**Positive evidence:** None.

### Related context, not answer evidence 1

Source: [materials/nyu/msds/curriculum.txt, lines 75–75](materials/nyu/msds/curriculum.txt#L75-L75)

Section: 4 Semester Course Plan  
Characters: `[4426, 4555)`

```text
This is just a guide to help plan out courses for the degree. Your actual course plan may vary based on when courses are offered.
```

## 13. msds-admissions-prerequisites

**Question:** What prerequisite subjects are required for MSDS admission, and what programming background is generally expected?

**Answerable:** Yes

**Expected answer points:**

1. Calculus I and Linear Algebra are required, or their equivalents.
2. An introductory Computer Science or equivalent CS-101 programming course is required.
3. One of Calculus II, Probability, Statistics, or an advanced physics, engineering, or econometrics course with heavy mathematical content is required.
4. There is no fixed programming-language requirement, but serious academic or professional experience with Python and/or R is generally expected.

**Scoring notes:** Do not present every subject in the final prerequisite group as mandatory; it is a choice of one. Distinguish expected programming experience from a fixed language requirement.

### Supporting evidence 1

Source: [materials/nyu/msds/admissions-requirements.txt, lines 36–39](materials/nyu/msds/admissions-requirements.txt#L36-L39)

Section: Educational Prerequisites  
Characters: `[2266, 2472)`

Supports answer points: 1.

```text
To be considered for the program, you must have completed the following (or equivalents, e.g., MOOCs certification or course credit):

Calculus I: limits, derivatives, series, integrals, etc.
Linear Algebra
```

### Supporting evidence 2

Source: [materials/nyu/msds/admissions-requirements.txt, lines 40–40](materials/nyu/msds/admissions-requirements.txt#L40-L40)

Section: Educational Prerequisites  
Characters: `[2473, 2711)`

Supports answer points: 2, 4.

```text
Intro to Computer Science (or an equivalent “CS-101” programming course): We have no set requirements regarding specific languages, but we generally expect serious academic and/or professional experience with Python and/or R at a minimum.
```

### Supporting evidence 3

Source: [materials/nyu/msds/admissions-requirements.txt, lines 41–41](materials/nyu/msds/admissions-requirements.txt#L41-L41)

Section: Educational Prerequisites  
Characters: `[2712, 2848)`

Supports answer points: 3.

```text
One of Calculus II, Probability, Statistics, or an advanced physics, engineering, or econometrics course with heavy mathematical content
```

## 14. msds-gre-submission

**Question:** Is the GRE required for MSDS admission, and what does the admissions requirements page say to do if I submit GRE scores?

**Answerable:** Yes

**Expected answer points:**

1. The GRE General Test is optional.
2. If submitting scores, upload a PDF of the unofficial scores to the Additional Information Section of the application.
3. Also send the official scores to the Graduate School of Arts and Science.

### Supporting evidence 1

Source: [materials/nyu/msds/admissions-requirements.txt, lines 51–51](materials/nyu/msds/admissions-requirements.txt#L51-L51)

Section: Standardized Tests  
Characters: `[3563, 3773)`

Supports answer points: 1.

```text
The GRE General Test is optional. If submitting, please note: we do not accept “out of date” scores (see Graduate School of Arts and Science’s Test Scores FAQs); nor do we accept scores of other, similar tests.
```

### Supporting evidence 2

Source: [materials/nyu/msds/admissions-requirements.txt, lines 53–53](materials/nyu/msds/admissions-requirements.txt#L53-L53)

Section: Standardized Tests  
Characters: `[3775, 4101)`

Supports answer points: 2, 3.

```text
If submitting scores for the GRE General test with your application, please upload a PDF of the unofficial scores, which are made available upon completion of your test, to the “Additional Information Section” of your application. This is in addition to sending your official scores to the Graduate School of Arts and Science.
```

## 15. msds-tracks-change

**Question:** What are the two primary MSDS tracks, and until when can students change tracks?

**Answerable:** Yes

**Expected answer points:**

1. The two primary tracks are Data Science and Data Science – Biomedical Informatics (Medical School).
2. Students may change tracks until the end of their second semester.

**Scoring notes:** Big Data, Mathematics and Data, and NLP are areas of interest within the Data Science track, not the two primary tracks.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-tracks.txt, lines 10–12](materials/nyu/msds/masters-in-data-science-tracks.txt#L10-L12)

Section: Master’s in Data Science: Tracks  
Characters: `[415, 580)`

Supports answer points: 1.

```text
The CDS Master’s in Data Science (MSDS) offers two primary “tracks” of study:
The Data Science track
The Data Science – Biomedical Informatics (Medical School) track
```

### Supporting evidence 2

Source: [materials/nyu/msds/masters-in-data-science-tracks.txt, lines 14–14](materials/nyu/msds/masters-in-data-science-tracks.txt#L14-L14)

Section: Master’s in Data Science: Tracks  
Characters: `[891, 957)`

Supports answer points: 2.

```text
Students may change tracks until the end of their second semester.
```

## 16. msds-working-enrollment

**Question:** I work full-time. What semester workload does the admissions FAQ suggest, are evening classes guaranteed, and does continuous enrollment also apply in summer?

**Answerable:** Yes

**Expected answer points:**

1. The admissions FAQ suggests 6 or fewer credits per semester for students with a full-time job.
2. Evening scheduling is not guaranteed; working students need flexibility to take required daytime courses.
3. Continuous enrollment is required every fall and spring semester, but not in summer.

**Scoring notes:** The 6-credit suggestion is a recommendation, not a universal enrollment maximum. For the summer point, explicitly stating that continuous enrollment does not apply in summer is sufficient; naming both fall and spring is optional.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-faq.txt, lines 39–39](materials/nyu/msds/masters-in-data-science-faq.txt#L39-L39)

Section: Can I work full-time while taking classes?  
Characters: `[1713, 2243)`

Supports answer points: 1, 2.

```text
The suggested full-time program is 9 credits per semester. Because of the heavy workload, 9 credits will equal out to about 40 hours of work per week. Students should be able to work while taking classes, but due to the amount of work required for the program, we suggest taking 6 or fewer credits per semester if you have a full-time job. We try to schedule required courses in the evenings, but this is not guaranteed. Full-time working students should have the flexibility to take required courses during the daytime if needed.
```

### Supporting evidence 2

Source: [materials/nyu/msds/masters-in-data-science-faq-general.txt, lines 31–31](materials/nyu/msds/masters-in-data-science-faq-general.txt#L31-L31)

Section: Are students required to take courses every semester?  
Characters: `[1582, 1841)`

Supports answer points: 3.

```text
Students are required to be continuously enrolled every fall and spring semester. If there is a semester where you do not want to take courses, please reach out to CDS-masters@nyu.edu to discuss options. This requirement does not apply to the summer semester.
```

## 17. msds-pathbreaker-fall2027

**Question:** For Fall 2027, how many Pathbreaker scholarships are described, what do they cover, and is a separate application required?

**Answerable:** Yes

**Expected answer points:**

1. The page describes scholarships for two Fall 2027 MS students.
2. They cover full tuition for the MSDS, described as 36 points of tuition and fees support.
3. Applying to the CDS MS program automatically places applicants under consideration; a separate scholarship application is not required.

**Scoring notes:** Keep the Fall 2027 cohort explicit. Do not substitute the historical launch year or counts of past recipients, or promise that every applicant receives an award.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-financial-aid-fellowships.txt, lines 18–18](materials/nyu/msds/masters-in-data-science-financial-aid-fellowships.txt#L18-L18)

Section: The CDS Pathbreaker Scholarship  
Characters: `[761, 1078)`

Supports answer points: 1, 2.

```text
In our commitment to foster innovation in data science, we launched the CDS Pathbreaker Scholarship in 2024. To support this mission, we are offering scholarships for two Fall 2027 MS students, covering the full tuition for our Master’s of Science in Data Science degree. That’s 36 points of tuition and fees support.
```

### Supporting evidence 2

Source: [materials/nyu/msds/masters-in-data-science-financial-aid-fellowships.txt, lines 22–22](materials/nyu/msds/masters-in-data-science-financial-aid-fellowships.txt#L22-L22)

Section: The CDS Pathbreaker Scholarship  
Characters: `[1208, 1490)`

Supports answer points: 3.

```text
Students need only to apply for the CDS MS program to be automatically considered for the scholarship. While not mandatory, applicants who believe they qualify for the Pathbreaker are encouraged to highlight their experiences in the personal statement section of the MS application.
```

## 18. msds-capstone-fall2026-deadline

**Question:** According to the saved capstone page, when were Fall 2026 project proposals due, and were submissions still open in the snapshot?

**Answerable:** Yes

**Expected answer points:**

1. Fall 2026 capstone project proposals were due August 16, 2026.
2. The saved page states that Fall 2026 submissions are now closed.

**Scoring notes:** This is the project-proposal deadline, not a student admission deadline or a deadline inferred from the September 7 retrieval timestamp.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-capstone.txt, lines 7–9](materials/nyu/msds/masters-in-data-science-capstone.txt#L7-L9)

Section: Submissions for the Fall 2026 Capstone Project Now Closed  
Characters: `[229, 323)`

Supports answer points: 1, 2.

```text
Submissions for the Fall 2026 Capstone Project Now Closed

Proposals were due August 16, 2026.
```

## 19. policy-effective-date

**Question:** What is the effective date of the saved Student Conduct Policy, and which earlier policy does it supersede?

**Answerable:** Yes

**Expected answer points:**

1. The saved policy is effective August 13, 2026.
2. It supersedes the University Student Conduct Policy dated August 15, 2025.

**Scoring notes:** Do not use the corpus retrieval date as the policy effective date.

### Supporting evidence 1

Source: [materials/nyu/policies/university-student-conduct-policy.txt, lines 18–19](materials/nyu/policies/university-student-conduct-policy.txt#L18-L19)

Section: Effective Date  
Characters: `[535, 627)`

Supports answer points: 1, 2.

```text
Effective Date: Aug 13, 2026
Supersedes: University Student Conduct Policy (August 15, 2025)
```

## 20. msds-cpt-source-context

**Question:** How do the admissions FAQ and Industry Concentration page describe internship timing, and what advice does the concentration page give international students?

**Answerable:** Yes

**Expected answer points:**

1. The admissions FAQ describes CPT as paid internships for credit after the first year of the degree.
2. The Industry Concentration page specifies a mandatory internship within the first year.
3. For that concentration, international students are directed to NYU’s Office of Global Services about obtaining early CPT status within their first year.

**Scoring notes:** Attribute each timing statement to its page and context. Do not erase either statement, declare personal visa eligibility, or claim that one page supersedes the other.

### Supporting evidence 1

Source: [materials/nyu/msds/masters-in-data-science-faq.txt, lines 111–111](materials/nyu/msds/masters-in-data-science-faq.txt#L111-L111)

Section: Will CPT or OPT be offered?  
Characters: `[6479, 6694)`

Supports answer points: 1.

```text
Yes, CPT and OPT are options for Data Science students. CPT is “curricular practical training,” a program which allows international students to obtain paid internships for credit after the first year of the degree.
```

### Supporting evidence 2

Source: [materials/nyu/msds/masters-in-data-science-industry-concentration.txt, lines 10–10](materials/nyu/msds/masters-in-data-science-industry-concentration.txt#L10-L10)

Section: Master’s in Data Science: Industry Concentration  
Characters: `[325, 949)`

Supports answer points: 2, 3.

```text
CDS offers the Industry Concentration for the MS in Data Science. This concentration is specifically designed to respond to the needs and inputs from companies, allowing MS in Data Science students to apply the knowledge and skills obtained in their coursework to industry-related projects during the degree program. It requires more industry-targeted coursework and a Practical Training experience, including a mandatory internship within the first year of study. International students should consult NYU’s Office of Global Services on how to obtain early CPT status within their first year if pursuing this concentration.
```

## 21. msds-career-advising

**Question:** What can I discuss in an individual CDS career advising appointment, and which NYU center collaborates with CDS on career resources?

**Answerable:** Yes

**Expected answer points:**

1. Individual advising covers resumes and cover letters, interview preparation and job-search strategy, and career development or exploration questions.
2. CDS collaborates with the NYU Wasserman Center for Career Development.

### Supporting evidence 1

Source: [materials/nyu/msds/student-career-development-professional-development-overview.txt, lines 20–24](materials/nyu/msds/student-career-development-professional-development-overview.txt#L20-L24)

Section: Individual Career Advising Appointments  
Characters: `[1163, 1389)`

Supports answer points: 1.

```text
CDS offers students one-on-one career advising appointments where students can discuss:

Resumes & cover letters
Interview preparation and job search strategy
Any topic or question related to career development and exploration
```

### Supporting evidence 2

Source: [materials/nyu/msds/student-career-development-professional-development-overview.txt, lines 14–14](materials/nyu/msds/student-career-development-professional-development-overview.txt#L14-L14)

Section: Resources  
Characters: `[681, 1056)`

Supports answer points: 2.

```text
The Center for Data Science, in collaboration with the NYU Wasserman Center for Career Development, offers a wide range of career and professional development resources to assist CDS students with their internship/job search process. These initiatives help students develop professional skills and connect with companies and organizations offering data science opportunities.
```

## 22. missing-fall2027-application-deadline

**Question:** What is the exact MSDS Fall 2027 application deadline, including the time and time zone?

**Answerable:** No

**Expected answer points:**

1. State that the saved corpus does not provide the exact Fall 2027 application deadline, time, or time zone.
2. Do not substitute the Fall 2026 capstone deadline or invent a date from a previous admissions cycle.

**Why no supported answer exists:** The requirements page says Fall 2027 details are coming soon. The admissions FAQ points to an external GSAS page whose content is not included.

**Positive evidence:** None.

### Related context, not answer evidence 1

Source: [materials/nyu/msds/admissions-requirements.txt, lines 7–9](materials/nyu/msds/admissions-requirements.txt#L7-L9)

Section: The Fall 2027 Application Details Are Coming Soon  
Characters: `[274, 546)`

```text
The Fall 2027 Application Details Are Coming Soon

Please note that the Graduate School of Arts and Sciences and the Courant Institute will also update their websites soon regarding the application. Details about the CDS Fall 2027 Information Session are also coming soon.
```

### Related context, not answer evidence 2

Source: [materials/nyu/msds/masters-in-data-science-faq.txt, lines 139–141](materials/nyu/msds/masters-in-data-science-faq.txt#L139-L141)

Section: What is the application deadline?  
Characters: `[8282, 8361)`

```text
What is the application deadline?

Please visit the NYU GSAS Data Science page.
```

## 23. missing-personal-scholarship-award

**Question:** I submitted an MSDS application for Fall 2027. What exact dollar amount of scholarship funding has NYU awarded me?

**Answerable:** No

**Expected answer points:**

1. State that the corpus cannot determine whether this applicant received a scholarship or its dollar amount.
2. Do not equate automatic consideration or the existence of full-tuition scholarships with an individual award.

**Why no supported answer exists:** The corpus contains general scholarship descriptions, not the user’s admission or award letter.

**Positive evidence:** None.

### Related context, not answer evidence 1

Source: [materials/nyu/msds/masters-in-data-science-financial-aid-fellowships.txt, lines 12–12](materials/nyu/msds/masters-in-data-science-financial-aid-fellowships.txt#L12-L12)

Section: Scholarships for Fall 2027 Admissions  
Characters: `[390, 647)`

```text
CDS offers a limited number of tuition scholarships to select students admitted to the program. All applicants for admission are considered for these awards on a competitive basis. These scholarships cover a portion of the tuition costs for up to two years.
```

### Related context, not answer evidence 2

Source: [materials/nyu/msds/masters-in-data-science-faq.txt, lines 175–175](materials/nyu/msds/masters-in-data-science-faq.txt#L175-L175)

Section: How do I apply for CDS’s tuition scholarships?  
Characters: `[10282, 10553)`

```text
CDS offers a limited number of tuition scholarships for our students. All applicants for admission are considered for these awards on a competitive basis. There is no separate scholarship application process. Scholarship recipients will be notified in their admit letter.
```

## 24. missing-personal-capstone-team

**Question:** Which Fall 2026 capstone project have I been assigned to, and who are my teammates?

**Answerable:** No

**Expected answer points:**

1. State that the supplied corpus does not identify the user’s capstone assignment or teammates.
2. Do not infer an assignment from a listed project title, past cohort, or typical team size.

**Why no supported answer exists:** The capstone page provides a program overview and past project lists, not a personal assignment roster.

**Positive evidence:** None.

### Related context, not answer evidence 1

Source: [materials/nyu/msds/masters-in-data-science-capstone.txt, lines 15–17](materials/nyu/msds/masters-in-data-science-capstone.txt#L15-L17)

Section: Overview  
Characters: `[468, 940)`

```text
CDS master’s students have a unique opportunity to solve real-world problems through the capstone course in the final year of their program. The capstone course is designed to help students apply their knowledge to practical situations and develop critical skills such as problem-solving and collaboration.

Students are matched with research labs within the NYU community and industry partners to investigate pressing issues, applying data science to the following areas:
```

### Related context, not answer evidence 2

Source: [materials/nyu/msds/masters-in-data-science-capstone.txt, lines 33–36](materials/nyu/msds/masters-in-data-science-capstone.txt#L33-L36)

Section: Fall 2025 Capstone Project List  
Characters: `[2122, 2404)`

```text
Fall 2025 Capstone Project List
A Framework for Generative Music Models and Creator Tools with Ethical Licensing and Attribution
Agentic AI for Automating People Discovery, Outreach, and Dashboard Generation at Scale
Agentic AI Framework for Commercial Use Cases with MCP Compliance
```

## 25. missing-exact-tuition-bill

**Question:** What is the exact total tuition and mandatory fees in US dollars for all 36 MSDS credits for a Fall 2027 entrant?

**Answerable:** No

**Expected answer points:**

1. State that the saved corpus does not provide the tuition rates and mandatory fees needed to calculate that dollar total.
2. Do not fabricate a dollar total or per-credit rate, or infer universal tuition coverage from the existence of limited scholarships.

**Why no supported answer exists:** The FAQ gives the 36-credit requirement and a link, but the linked tuition-and-fees page is not part of this snapshot.

**Positive evidence:** None.

### Related context, not answer evidence 1

Source: [materials/nyu/msds/masters-in-data-science-faq.txt, lines 165–167](materials/nyu/msds/masters-in-data-science-faq.txt#L165-L167)

Section: How much does the program cost?  
Characters: `[9928, 10145)`

```text
How much does the program cost?

Tuition and fees for the current academic year can be found on the Graduate School of Arts and Science Tuition and Fees page. The MS in Data Science Program requires 36 course credits.
```
