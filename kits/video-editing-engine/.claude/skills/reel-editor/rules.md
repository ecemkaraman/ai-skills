# Editing rules

Starting rules for a talking-head Reel. Add one line every time a note on a draft
turns out to be a rule, so the same note never has to be given twice.

## Cutting

- Cut between phrases at real silence, never inside a phrase.
- Keep natural beats, such as the pause after "First,". Remove dead air, not rhythm.
- Remove a filler word only when there is silence on both sides of it.
- When a sentence is said twice, keep the cleaner take and say which one you kept.
- Pad every cut edge by `pace.cut_padding_s` in `brand.json`.
- Keep the first sentence. It's usually the hook.

## Captions

- Two to four words at a time, current word highlighted.
- Never over the mouth. Check the first 2.5 seconds frame by frame.
- Inside the safe zone in `brand.json`, every frame.
- Captions never blink out; on busy shots move them, don't hide them.

## Graphics

- One title, at most two emphasized key terms. Restraint reads as quality.
- Every graphic must say something the speaker is saying at that moment.
- Animate position and scale, not layout properties.

## Audio

- A 30 ms fade at every cut.
- Loudness and true peak from `brand.json`, measured on the final file.

## Notes that became rules

<!-- Add new rules here, newest first, with the date. -->
