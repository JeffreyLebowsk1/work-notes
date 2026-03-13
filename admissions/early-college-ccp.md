# Early College & Career and College Promise (CCP)

> Internal staff reference for Early College and CCP (Career & College Promise) admissions, enrollment, and Colleague procedures.

---

## Early College

### Graduation During an Active Semester — SPRO & XNC2 End Dates

- If a student graduates **after** the summer semester has already started, the NULL date on SPRO and the XNC2 end date must be set to the **day after the semester ends**.
- The XNC2 end date follows the same rule: if they graduate after the summer semester has already started, the XNC2 end date must be the **day after the semester ends**.

### Applications — Checklist

When processing Early College applications, make sure:

- [ ] County is correct
- [ ] Student has completed 8th grade
- [ ] XNC2 pathway is always **CIE** and **FR – Freshman**
- [ ] Student has **5 years** to complete — give 5 years in the attend dates

### Underage / Gifted Students

- **Dr. Short** must sign off on a student being gifted (underage).
- Enter the relevant info in **Datatel**.
- The application will **never show in SLATE**, but once the student gets registered, some info will pull back into SLATE.

### Colleague Quirk — IASU → HSA (Early College End Date)

When trying to add the End Date for Early College on the IASU → HSA screen, there is a known issue entering dates for **2030**:

- Enter the projected graduation date of **June 1, 2030** as **`6/1/2030`** exactly.
- Do **not** use `060130`, `06.01.30`, or any other format — only `6/1/2030` works correctly.

---

## Career and College Promise (CCP)

### What Is CCP?

The **Career and College Promise (CCP)** program offers structured dual enrollment opportunities for qualified NC high school students to enroll in community college courses that lead to a certificate, diploma, or degree, or provide entry-level job skills — **tuition-free**.

### Pathways

| Pathway | Abbreviation | Description |
|---|---|---|
| College Transfer | CT | For students planning to continue beyond high school toward an Associate's or Bachelor's degree |
| Career and Technical Education | CTE | For students beginning a certification or diploma program in a technical field or career area |
| Cooperative Innovative High School | CIHS | For students attending small public high schools on the campus of a higher education institution, working toward both a high school diploma and an associate degree, transferrable credit, or career certificate |

- More info: [NCDPI CCP website](https://www.dpi.nc.gov/students-families/enhancing-student-learning/career-and-college-promise) and [NCCCS CCP website](https://www.nccommunitycolleges.edu/academic-programs/college-and-career-readiness/career-college-promise-ccp/)

### Eligibility

- **CT and CTE pathways:** Juniors and Seniors must meet specific eligibility requirements. Select Freshmen and Sophomores may access select pathways with additional eligibility requirements.
- **CIHS:** Eligibility criteria are locally determined.
- Full criteria: [NC Community College System CCP Operating Procedures](https://www.nccommunitycolleges.edu/academic-programs/college-and-career-readiness/career-college-promise-ccp/)

### Key Facts for All CCP Students

- Courses are **tuition-free** (some colleges may have additional local fees).
- Students **must** enroll through their high school — school approval is required before enrolling in any college course.
- CCP begins a **permanent college transcript**; grades earned carry forward beyond high school.
- Students are held to the same attendance, academic requirements, and honor code as traditional college students.
- CCP courses may require travel to the college campus and time outside normal school hours.
- A minimum **2.0 college GPA** (after completing two courses) is required to remain eligible (non-CIHS students).
- Failing courses can lead to academic probation, affect financial aid eligibility, and remain permanently on the college transcript.

### College Transfer (CT) Pathway — Course Guidance

- Work with both the high school counselor and the college advisor — advisors have access to the **UNC System Transfer Toolbox**.
- Use **Baccalaureate Degree Plans (BDP)** for the intended major and institution to determine the right courses.
- **Universal General Education Transfer Courses (UGETC)** provide guaranteed transfer to all UNC System institutions — focus on UGETCs when the student's major or intended institution is undecided.
- See: [Dual Credit Allowances Chart](https://www.dpi.nc.gov/students-families/enhancing-student-learning/career-and-college-promise), [CAA Transfer Course List](https://www.nccommunitycolleges.edu/academic-programs/college-transfer/transfer-articulation-agreements/), and the [NCCCS CCP website](https://www.nccommunitycolleges.edu/academic-programs/college-and-career-readiness/career-college-promise-ccp/).
- Being on the CAA Transfer Course List does **not** guarantee courses will apply to a specific major — verify with the target institution.
- To earn an Associate of Arts (AA) or Associate of Science (AS), students must earn **C's or better** in at least **60 credit hours**.

### CTE Pathway — Course Guidance

- CTE opportunities vary by community college — work with the high school counselor and Career Development Coordinator.
- Students may be able to receive college credit for high school CTE courses — see: [NC High School to Community College Articulation Agreement](https://www.nccommunitycolleges.edu).
- To learn more about career opportunities in NC: [NCCareers.org](https://www.nccareers.org)

### Cooperative Innovative High Schools (CIHS)

- Not all school districts have a CIHS — check locally.
- CIHS students may enroll in the CT program, CTE program, or both.
- More info: [NCDPI CIHS website](https://www.dpi.nc.gov/students-families/enhancing-student-learning/cooperative-innovative-high-schools)

### PSAT or PreACT Scores

Per CCP guidelines, CCP students can use **PSAT or PreACT scores** to qualify for direct placement into gateway math or English. However:

- We do **not** use a test code that awards non-course credit — we would have to remove the credit once the student graduated.
- Instead: the CCP advisor files a copy of the scores with **SRR**. SRR overrides the prereq, makes an advising note, and notifies the instructor and department chair who are checking the prereqs.

---

## CCP Applications

### Application Materials

- CCP Application Process.pdf
- CCP Student App to Traditional App.pdf

### Key Application Rules

| Situation | Action |
|---|---|
| Current CCP student finishing a CCP program and starting as a regular student **in the same semester** | Keep the CCP program open and primary; add the regular college program as secondary — do **not** null or close the CCP program |
| Current CCP student applying as a regular student for the **next semester** | Null the CCP programs and process the regular program normally |
| High schools that graduate early (e.g., Central Carolina Academy, Chatham Charter — end for Spring; Ascend — just after classes begin) | Null accordingly based on graduation date |

- **Ken Hoyle** must sign off on a CCP application only if the student's GPA is **below 2.8** or the student is in **2 pathways**.

---

## RGO1 HUSK CCPP — Student Rule Error

### What Is This Rule?

The **RGO1 HUSK CCPP** rule is an internal Colleague registration rule used to restrict enrollment in specific class sections to CCP students.

- **RGO1** — A "Registration Group" rule checked during enrollment.
- **HUSK** — Refers to the legacy Huskins program (predecessor to CCP); the name remains in Colleague even though the program has changed.
- **CCPP** — The current student type code for Career & College Promise students.

### Why Does This Error Trigger?

The error message "Must be CCPP student to enroll in this section" means the student's **SPRO screen** does not have the CCPP student type listed for the current term.

### Internal Staff Action Steps

1. **Check SPRO** — Ensure the student is coded as CCPP for the specific term they are trying to register for.
2. **Verify XNC2** — Confirm the student has an active pathway (e.g., College Transfer or CTE) on the XNC2 screen.
3. **Leon's Law Check** — If the student is under 18, verify the Leon's Law acknowledgement form is on file in Slate or Etrieve. The system may block registration for minors who have not completed this mandatory step.
4. **HS Graduation Date** — Check **XNCA** to ensure the student has not been assigned a graduation date in the past, which would automatically invalidate their CCPP status.

> **From Haley:** These rules are added to CCP courses to prevent traditional students from being added to them. If the student's program is a CCP program, they are OK to register — but CCP advisors do **not** have override rights. CCP advisors can chat their lead CCP advisor or Haley can add them.

---

## CCP — NULL Date Rules for Graduating Students

Use the following rules to determine when to NULL a student's CCP status when they submit a traditional application:

| Scenario | NULL Date |
|---|---|
| CCP student graduates **before** their traditional semester starts (e.g., graduates 01/09/2026, 3 days before Spring 2026 starts) | NULL for the **previous semester** they were a CCP student (e.g., Fall 2025 in that example — the semester before Spring 2026) |
| CCP student graduates **during** the semester they submitted a traditional application for (e.g., graduates 01/18/2026 during Spring 2026) | NULL for the **end of the current semester** (e.g., end of Spring 2026) |

### Class Enrollment Restrictions for Mid-Semester Graduates

If a CCP student graduates from high school **during** the semester they submitted a traditional application for, they can only sign up for classes that **start after** the day they graduated.

> **Example:** A CCP student graduates on January 25, 2026 during the Spring 2026 semester. The 16-week and 1st 8-week classes already started on January 12, 2026. This student **cannot** sign up for 16-week or 1st 8-week classes. They **can** sign up for 12-week and 2nd 8-week classes for Spring 2026.

---

*Source: NCDPI Feb 2021; internal staff notes and communications*
*Last updated: 2026-03-13*
