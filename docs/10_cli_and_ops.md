# CLI and operations

The CLI entrypoint is `ytce`.

## Commands

- `ytce pack build --input <folder> --out <file.pack>`
- `ytce pack info --pack <file.pack>`
- `ytce pack ask --pack <file.pack> --question "<q>"`

## Input folder format

```
input/
  channel.json
  videos.json
  transcripts/
    VIDEO_ID_1.srt
    VIDEO_ID_2.vtt
    ...
```

See `examples/demo_channel/`.

## Pack portability

The resulting `.pack` file is just a zip bundle.
You can inspect it:

```bash
unzip -l packs/demo_channel.pack
```
