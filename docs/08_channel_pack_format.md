# Channel Pack format

A **Channel Pack** is a single-file bundle (zip) containing:

- `manifest.json`
- `pack.sqlite` (metadata + transcripts + summaries + mappings)
- `vectors/` (embeddings matrix or ANN index artifacts)

## Why a bundle?

- portable between macOS and iOS
- easy to export/import
- versioned and forward-compatible

## Versioning

`manifest.json` contains:
- `pack_version`
- `schema_version`
- `embedding_dim`
- `embedding_model_id` (string)
- `created_at`
- `channel_id`, `channel_title`
- `video_count`, `chunk_count`, `section_count`

## Encryption

Not implemented in code here, but recommended:
- encrypt the entire pack file with a user key
- store key in Keychain (iOS/macOS) or OS key manager
- or use OS-level file encryption (FileVault / iOS file protection)

Implementation reference:
- `src/yt_channel_expert/pack/pack_builder.py`
- `src/yt_channel_expert/pack/pack_reader.py`
