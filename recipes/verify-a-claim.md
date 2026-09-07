# Verify a claim before you write it down

This reference is only worth what its claims are worth. A pattern that looks certain after one observation is how a
wrong rule gets published — and once published, later readers treat it as settled.

`tools/cr-probe` exists to make checking cheaper than guessing.

## Before adding a rule

Run it against every week the API still remembers, not the week you noticed:

```sh
cd tools/cr-probe
uv run crprobe survey finish-time --clan '#YOURCLAN' --human
```

A survey prints a verdict plus the rows behind it, so the evidence table in the doc and the sentence above it come from
the same command. If a survey says `DOES NOT HOLD`, the interesting thing is the counterexample, not the rule.

Absence of evidence is reported as not-holding rather than holding. A rule with no Colosseum week in range is unproven,
not confirmed.

## When the API surprises you

Check what it actually returns, rather than what you remember:

```sh
uv run crprobe get '/clans/#YOURCLAN/currentriverrace' | jq '{state, sectionIndex, periodIndex, periodType}'
```

If a key fails, find out whether it is the key or the network before debugging the wrong thing:

```sh
uv run crprobe keys --human
```

A `403` naming an IP means the key is fine and allowlisted elsewhere. Point `--key-file` at the `.env` of the service
that owns it and you are probing with exactly what it uses.

## When something changes on a schedule

Season rolls, week closes and daily resets are only observable while they happen, and they happen once a month, once a
week and once a day. Record them unattended rather than trying to be awake:

```sh
uv run crprobe record --preset season-roll \
  --clan '#YOURCLAN' --player '#YOURTAG' --session s137-roll --for 4h
uv run crprobe timeline s137-roll --human
```

Transitions come back as windows with bounds, not single timestamps. Write the bounds into the docs as bounds. Claiming
a precision you did not measure is the same failure as guessing, wearing a timestamp.

## After you write it

If the finding is an enum value or a specific observed fact, add it to
`tools/docs-build/scripts/validate-observed-enums.mjs` so a future rewrite cannot quietly drop it. Observed values are
the expensive part of this reference; nothing else protects them.
