# Changelog

Dated notes for larger product changes. Day-to-day docs live in the other files under `docs/`.

## 31 October 2026

Work landed across several agent sessions on the same uncommitted branch. Summary below.

### Visitors (`apps.visitors`)

- New visitor log separate from children: name, gender, optional date of birth and address.
- Each Sabbath visit stores reason and who they came with (existing parent, existing child, or optional free-text name and phone).
- Home quick action **Add visitor**; More links for Visitors and Visitor follow-up (after Birthdays).
- Returning visitors are searched so visits stack on one person.
- After three visits since the last checkup, names appear under **Visitors to reach out to** on Home; marking checked up resets the counter.
- Convert to child creates an incomplete child record and keeps visit history.
- Visit counts add into Sabbath **Present** totals; visitors stay off the class roll.

### Attendance current vs past Sabbath

- **Current Sabbath** is the latest Saturday on or before today and stays open through Friday.
- Current Sabbath shows the live Present/Absent roll.
- Past Sabbaths show stats, children present, visitors, and CSV download.
- Only coordinators and admins see **Edit attendance** on a past Sabbath (teachers view only).
- Non-Saturday dates show a warning page; the next Saturday shows as not open yet.
- Home dashboard **Current Sabbath** card uses the same current date.

### Roles

- Teachers and coordinators share the same ministry model permissions (children, parents, guardians, attendance, age groups, visitors, academic year).
- Only Admin is staff/superuser; Django admin is Admin-only.
- Exception: past Sabbath edit/save remains coordinator and admin only (group check), even though teachers can change attendance for the current Sabbath.

### Children and parents

- Class ladder includes early years (Pre-school through KG) with matching migrations.
- Date of birth is optional; Incomplete labels call out missing birthday and/or parent.
- Unique child identity is case-insensitive first + last name with date of birth (unknown birthdays may share a name).
- Add child can link or create a parent; school and address suggest existing values while typing.
- Parent primary phone is unique; parents can link several children from the parent page.

### Other

- Optimized brand images in `static/images/`.
- CSS and small UX helpers (form submit loading, clear date, parent picker, field suggest).
- Seed data includes sample visitors and visits.
- Docs under `docs/` updated to match the above.
