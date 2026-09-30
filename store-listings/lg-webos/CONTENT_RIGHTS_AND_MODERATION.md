# LG Content Rights and Moderation Readiness

## Decision

**Do not submit as a global app until Seller Lounge account review, physical or
Cloud Test Lab validation, and content-rights evidence are complete.**

TV Viewer is a player and does not host video. However, the LG application
provides an integrated discovery catalog, so LG content QA can reasonably treat
the discoverable streams as app content.

## Controls implemented for the LG edition

- Catalog discovery is restricted to public-interest categories: Business,
  Culture, Documentary, Education, Legislative, News, Science, and Weather.
- Explicit channel-name patterns are blocked before rendering.
- Movies, entertainment, sports, music, radio, general, and uncategorized
  discovery are excluded from the LG edition.
- Only HTTP and HTTPS media URLs are accepted.
- The first-run notice states that availability and rights vary by source and
  location and that users must access only permitted content.
- Store screenshots use legislative/public-interest results and contain no
  sexual, violent, gambling, or mature imagery.

## Remaining evidence needed

1. Confirm whether LG accepts an app that indexes community-discovered public
   stream URLs without individual broadcaster agreements.
2. Obtain written confirmation or documented source terms for channels chosen
   for initial certification testing.
3. Select initial territories only after validating geo-blocking and content
   availability for those territories.
4. Run a manual review sample across every enabled category before submission.
5. Establish a removal/escalation process for rights-holder complaints.

## Recommended submission position

- Describe TV Viewer as an open-source live-stream player and discovery client,
  not as a broadcaster or content owner.
- State that streams are opened from third-party endpoints and may be
  unavailable by region.
- Avoid claiming that all catalog content is licensed by TV Viewer.
- Use LG Seller Lounge 1:1 Q&A before formal submission to ask whether the
  curated community catalog model is acceptable.
- If LG requires direct distribution rights, switch the store build to a
  user-supplied-playlist model or a small allowlist backed by broadcaster
  permission.
