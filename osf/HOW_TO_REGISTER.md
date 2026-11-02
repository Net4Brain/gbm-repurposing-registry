# How to submit the OSF registration (private, embargoed)

Time: about 45–60 minutes. Everything happens in your browser, under your own OSF account.

## 1. Create the OSF project (private)
1. Sign in at osf.io (create a free account if needed; ORCID sign-in works).
2. **Create new project** → title: *Repurposed drugs in the contemporary glioblastoma clinical trial landscape* → storage location: **United Kingdom** or **Germany (EU)** → leave it **Private**.
3. In the project, open **Files → OSF Storage → Upload** and upload:
   - `osf/gbm-repurposing-registry_903dc98.zip` (12 MB: the full frozen pipeline at GitHub commit 903dc98, manual v1.4; no ReDO file)
   - `osf/OSF_preregistration_draft_v2.md` (optional, for the record)

## 2. Start the registration
1. In the project, open **Registrations** → **New registration**.
2. Choose the template **"Preregistration Template for Secondary Data Analysis"**. (If it is not listed, use **"OSF Preregistration"**; the draft answers its questions too.)
3. Fill in each field by copying the matching section from `OSF_preregistration_draft_v2.md` (version 2 supersedes the first draft). Where a field allows attaching files, attach the zip from OSF Storage.
4. Contributors: add only people who have agreed. Co-authors can be added later.

## 3. Submit with an embargo
1. On the final page choose **"Enter registration into embargo"** and set the end date (up to 4 years; e.g. 2030-11-01). You can end the embargo early at any time, for example when the paper is accepted.
2. Submit. OSF sends a confirmation email to every admin contributor; the registration is only created after **all** admins approve (if you are the only admin, approve it yourself from the email).
3. Note the registration DOI / identifier (form `10.17605/OSF.IO/XXXXX`). It is fixed even while embargoed.

## 4. Afterwards (tell Claude)
- Send me the registration identifier. I will add it to `protocol_decisions.md` (as D20), the README, and the next manuscript revision (replacing "[Insert OSF registration identifier…]").
- Then the main coding pass on the 870 records can start.

## Notes
- The embargoed registration is invisible to the public but carries the registration date, which is what reviewers check.
- Do not change the frozen files in GitHub after registering; any change goes in as a dated amendment.
- The zips are not committed to GitHub (each is a copy of a commit that is already there). Upload only `gbm-repurposing-registry_903dc98.zip`; the older e2e6083 zip (manual v1.2) is superseded.
