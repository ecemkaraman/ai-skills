# Quality checks

Run `scripts/qa.py`, then check every item. A render that finishes isn't an edit
that works.

## From the report

- [ ] No black or frozen frames
- [ ] Audio and video are the same length
- [ ] Loudness and true peak match `brand.json`

## Look at the images

- [ ] **Contact sheet:** framing holds, no empty or wrong shots
- [ ] **Every cut strip:** no one-frame flashes, no caption left over from the previous shot
- [ ] **First 2.5 s:** nothing covers the mouth
- [ ] **Safe zone:** no text in the top, bottom or side margins from `brand.json`

## Listen and compare

- [ ] Re-transcribe the render and compare the words at every cut with the source.
      A clipped word can still transcribe correctly, so listen at each cut too.
- [ ] Captions match the audio from the first word to the last

## Before showing me

- [ ] List what you checked, what failed and what you changed
- [ ] Stop after three fix passes and tell me what's left
