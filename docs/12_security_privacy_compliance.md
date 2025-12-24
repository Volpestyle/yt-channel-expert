# Security, privacy, compliance

## Local-first storage
- Store packs locally.
- Provide deletion primitives that wipe pack + derived caches.

## Data minimization
- Do not ingest more than needed (comments optional).
- Consider omitting viewer usernames if you ingest comments.

## Compliance
- Use transcripts/audio that you are authorized to process.
- For channels you do not own, prefer:
  - manual transcript import, or
  - local transcription from audio you have rights to use.

## Threat model considerations
- Packs may contain sensitive info (private videos, unlisted links).
- Support encryption at rest if distributing packs.
