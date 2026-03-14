# Transcript Processes

## Official Transcript Request Flow

<div class="mermaid">
flowchart TD
    A[Student submits request] --> B{Hold on account?}
    B -- Yes --> C[Notify student — do not release]
    B -- No --> D[Verify identity & request details]
    D --> E[Process in SIS]
    E --> F{Delivery method?}
    F -- Electronic --> G[Upload to Parchment / NSC]
    F -- Mail --> H[Print, seal, and mail]
    G --> I[Log request & notify student]
    H --> I
</div>

## Official Transcript Requests

1. Student submits request via the [Transcript Request Portal](_links.md) (online) or completes a paper request form in person.
2. Verify student identity — confirm name, student ID, and date of birth match records.
3. Confirm the request is complete: recipient address/institution, number of copies, delivery method (electronic vs. mail), and purpose.
4. Check for any holds on the student's account (financial, academic, administrative) — **do not release transcripts if a hold is present; notify the student.**
5. Process the request in the Student Information System (SIS):
   - Locate the student record.
   - Generate/export the official transcript.
   - Apply the official seal / registrar signature as required.
6. Send via the requested delivery method:
   - **Electronic:** Upload to third-party service (e.g., [Parchment](https://www.parchment.com)/[National Student Clearinghouse](https://www.studentclearinghouse.org)) or send securely to the recipient.
   - **Mail:** Print, seal in an official envelope with the registrar's stamp across the seal, and mail.
7. Log the request and mark as completed. See [`templates/request-log.md`](./templates/request-log.md).
8. Notify the student when the transcript has been sent (if electronic, the platform may do this automatically).

## Unofficial Transcript Requests

1. Student requests via the student portal (self-service) or in person at the office.
2. Verify student identity.
3. **Unofficial transcripts are for student use only** — do not release directly to third parties.
4. Generate an unofficial transcript from SIS (no seal required).
5. Provide to the student (print, PDF, or portal download).
6. No logging required unless your office tracks all transcript activity.

## Third-Party Requests

Third parties (employers, other institutions, licensing boards) must receive **official** transcripts only — **never release to a third party upon their request alone.**

1. Direct the third party to the student to initiate the request.
2. If a signed student release/consent form is provided:
   - Verify the signature and that consent is current and specific.
   - Follow the Official Transcript Request steps above with the third party as the recipient.
3. If a **subpoena or court order** is received — see [Data Requests — Subpoenas](../personal-data/data-requests.md).
4. For **[National Student Clearinghouse](https://www.studentclearinghouse.org)** or similar verification services — follow the enrollment verification procedure (not a transcript release).

## Rush / Expedited Requests

- Verify whether your office offers rush processing and any associated fee.
- Prioritize in the queue and note the rush status in the SIS.
- Confirm delivery timeline with the student at the time of request.

## Common Issues & Resolutions

| Issue | Resolution |
|---|---|
| Student has a hold | Notify student, do not release; direct them to the office that placed the hold |
| Student name doesn't match ID | Verify with government-issued ID; check for name changes in records |
| Transcript not generating in SIS | Contact IT/SIS support; process manually if urgent |
| Recipient claims they never received | Confirm delivery method; re-send if needed; check spam/junk for electronic |
| Student wants grades from transfer credits | Explain that transfer credits are not on the institutional transcript; refer to originating school |
| Request for a student who hasn't attended recently | Locate archived records; may need to pull from older system or paper files |

---

## Continuing Education (Non-Credit) Transcript Requests

Non-credit/CE transcript handling is split by record date. **Always ask the student whether their CE courses were before or after 2007** before routing.

| Record Date | Who Handles It |
|---|---|
| **2007 to present** | Student Records and Registrar's Office — (919) 718-7201 / admissions@cccc.edu |
| **Prior to 2007** | Nutan Varma, Harnett Main Campus (CE Building) — (910) 814-8975 / nvarma@cccc.edu |

### Personal Enrichment & Short-Term Training

- Students must use the specific **"Personal Enrichment & Short-Term Training Transcript Request"** form.
- CE transcripts are provided **free of charge**.
- Pre-2007 requests: processing time up to **five business days** (Nutan Varma).
- AHS backup printing (urgent situations): Chesure Tate — Bell Welcome Center, (919) 718-7716; or Anita Green — Lee Main Campus, (919) 545-8669.

### GED / HiSET Records

CCCC does not maintain official NC High School Equivalency records. Direct students to:

- **[DiplomaSender](https://www.diplomasender.com)** — (855) 313-5799
- Standard fee: **$20.00 per document** *(see [Conflicts Pending — CONFLICT 4](../updates/conflicts-pending.md) for a noted fee discrepancy)*
- Records must be sent directly to CCCC at **admissions@cccc.edu** to be considered official.

See also: [Continuing Education — Programs, Policies & Records](../continuing-education/programs-and-policies.md)