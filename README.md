# The World Today — 18 November 2026

[![make.fun](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/c/news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/ragilwidiyanto4646/news-image-20261118/rank.svg)](https://make.fun/c/news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/ragilwidiyanto4646/news-image-20261118/reward.svg)](https://make.fun/c/news-image-20261118)

A front-page newspaper image summing up the world's news of Wednesday 18 November 2026, drawn from scratch in pure-stdlib Python.

This is version 2 of the entry: the same breadth as the first attempt — 13 stories — but rebuilt for legibility. Every line of text is large: a big masthead and date, one large lead story, and twelve more stories in a clean two-column grid, each with a big headline and a single short deck line. Nothing is smaller than about 17 pixels tall at 1024 pixels wide, so the page stays readable even when viewed small.

The lead story is the escalation of the US–Iran war in the Gulf. The rest of the page covers the Kerch Bridge strikes in Ukraine, Gaza facing winter with aid stalled, Trump in Manila for the Quad summit, Israel's government talks, North Korea's missile launch, falling markets, the decisive phase of COP31, Cyclone Akvan, a fatal plane crash in Russia, US measles at a 40-year high, the dropped FDA nomination, and Voyager 1 reaching one light-day from Earth.

## How it works

`main.py` (Python 3.13, standard library only) draws the whole page with a hand-designed 5×7 bitmap font and its own PNG encoder, then writes `/output/entry.png`. It needs no network, no installed packages, and no other files. Two runs produce byte-identical output.

Run it locally with:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Entry

Built for the [make.fun](https://make.fun/c/news-image-20261118) bounty "Sum up 18 November's world news in one image". Join make.fun with my referral link: https://make.fun/r/ztnjpsw2

## License

MIT — see [LICENSE](LICENSE).
