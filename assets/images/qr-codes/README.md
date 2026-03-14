# QR Codes

CCCC-branded QR codes for student-facing links. Navy (#1d3557) foreground on white, circle modules, rounded eyes.

Generated with [qoder](https://qoder.ngrok.app) — a self-hosted QR code generator running on the Jetson.

---

## Codes

| File | Destination | URL |
|---|---|---|
| `registrar-office.png` | Student Records & Registrar's Office | https://www.cccc.edu/support-success/all-offices-services/student-records-and-registrars-office |
| `transcript-request.png` | CCCC Transcript Request | https://www.cccc.edu/support-success/all-offices-services/student-records-and-registrars-office/cccc-transcript-request |
| `fafsa.png` | FAFSA Application | https://studentaid.gov |
| `advising-hub.png` | Advisor Degree Audit Portal | https://apply.cccc.edu/portal/advisor?tab=Home |
| `nc-residency.png` | NC Residency Determination Service | https://www.ncresidency.org |
| `ce-scholarship.png` | CE Workforce Access Scholarships | https://www.cccc.edu/continuingeducation/workforceaccess/ |
| `ccr-registration.png` | College & Career Readiness Registration | https://www.cccc.edu/support-success/all-offices-services/college-career-readiness/registration |
| `cfnc.png` | CFNC Application Portal | https://www.cfnc.org |
| `diplomasender.png` | DiplomaSender (GED/HiSET Records) | https://www.diplomasender.com |
| `cccc-scholarships.png` | CCCC Foundation Scholarships | https://www.cccc.edu/scholarships |
| `cccc-financial-aid.png` | CCCC Financial Aid | https://www.cccc.edu/paying-college |
| `civic-center.png` | Dennis A. Wicker Civic & Conference Center | https://www.cccc.edu/about/locations/civic-center/ |
| `ce-schedule.png` | CE Course Schedule | https://www.cccc.edu/ecd/schedule/ |
| `academic-calendar.png` | Academic Calendar | https://calendar.cccc.edu/ |

---

## Regenerating

To regenerate or add codes, POST to the [qoder API](https://qoder.ngrok.app) (`/api/qr/text`):

```json
{
  "data": "https://example.com",
  "fg_color": "#1d3557",
  "bg_color": "#FFFFFF",
  "module_style": "circle",
  "eye_style": "rounded",
  "error_correction": "H",
  "box_size": 20,
  "border": 3
}
```
