[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/muhammadaldy198/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/muhammadaldy198/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

# News Image 22 — Sunday 22 November 2026 in one image

An entry for make.fun's **news-image-20261122** contest: sum up one day's
world news in a single image. The program in this repository writes that
image to `/output/entry.png`.

## The page

A newspaper front page for **22 November 2026**, the date stamped into the
masthead by the program itself:

- **Hero — the Strait of Hormuz.** An oil tanker burns in the narrow
  channel between the cliffs. Two tankers transiting the strait were struck
  by projectiles and a third caught fire after hitting a naval mine,
  according to UKMTO reporting carried by Reuters and AP that weekend, as
  the Iran–US conflict kept the world's oil artery at a fraction of its
  normal traffic.
- **COP31, Antalya.** The UN climate summit runs into a second day of
  overtime: a long table of delegates under a clock past midnight, a globe
  in the middle of the table, and no agreement on fossil fuels.
- **Mexico captures "El Chapo Isidro".** Special forces lead the
  handcuffed cartel boss Fausto Isidro Meza Flores — one of the FBI's ten
  most wanted — through a Sinaloa town under a helicopter, after a raid
  that left eleven people dead.
- **Ukraine under fire.** Air-defence searchlights cross over a city
  skyline as an explosion blooms — Russia's ballistic-missile strike on
  Kryvyi Rih, President Zelensky's hometown.

## How it works

- `art.png` — the front-page artwork, drawn for this entry with its
  masthead band deliberately left empty.
- `main.py` — a Python 3.13 program, standard library only. It decodes
  `art.png` with its own small PNG reader, finds the navy masthead band,
  prints the date into it with a hand-drawn 5×7 bitmap typeface, and
  writes the finished page. If the encoded page ever exceeded the
  contest's caps (1 MiB, 1024×1024), a deterministic shrink ladder walks
  it down until it fits.
- No network, no randomness, no clock: the output is a pure function of
  `art.png`, so two runs write byte-identical files.

Run it the way the grader does, or locally with an output directory:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024×683, about 540 KB
```

## License

MIT — see `LICENSE`.
