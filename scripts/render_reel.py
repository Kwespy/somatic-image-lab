#!/usr/bin/env python3
"""Create one short TSIL Reel from an existing reading without touching it."""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from tsil_social import question_story_html, reading_data, screenshot, story_html


ROOT = Path(__file__).resolve().parents[1]
READINGS = ROOT / "readings"
DATA = ROOT / "data" / "readings.json"
EXPORTS = ROOT / "exports"
PAPER = "#f2efe7"
INK = "#0a0a0a"
ORANGE = "#ff5a1f"


def run(command):
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if completed.returncode:
        raise RuntimeError(completed.stdout.strip() or "No se pudo crear el Reel.")
    return completed.stdout


def tool_path(name):
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Falta {name}. Este computador necesita {name} para crear Reels.")
    return path


def font_path():
    options = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for option in options:
        if option.exists():
            return option
    raise RuntimeError("No encontre una tipografia Arial para crear el Reel.")


def get_reading(number):
    try:
        number = int(number)
    except ValueError as error:
        raise RuntimeError("Escribe el numero del reading, por ejemplo 028.") from error

    items = json.loads(DATA.read_text(encoding="utf-8"))
    item = next((entry for entry in items if int(entry["number"]) == number), None)
    if not item:
        raise RuntimeError(f"No encontre el reading {number:03d}.")
    page_path = READINGS / item["slug"] / "index.html"
    if not page_path.exists():
        raise RuntimeError(f"No encontre la pagina de reading {number:03d}.")
    return item, page_path.read_text(encoding="utf-8")


def render_label(magick, font, size, point_size, color, text, output, opaque=False):
    canvas = f"xc:{color}" if opaque else "xc:none"
    run([
        magick,
        "-size", size,
        canvas,
        "-font", str(font),
        "-pointsize", str(point_size),
        "-fill", INK if opaque else color,
        "-gravity", "center",
        "-kerning", "-24" if not opaque else "2",
        "-annotate", "0", text,
        str(output),
    ])


def title_words(title):
    paired = re.split(r"\s+(?:and|y)\s+", title.upper(), maxsplit=1, flags=re.I)
    if len(paired) == 2:
        return tuple(re.sub(r"^(?:THE|LO|EL|LA)\s+", "", part) for part in paired)
    words = title.upper().split()
    if not words:
        return "READING", "READING"
    if len(words) == 1:
        return words[0], words[0]
    return words[0], " ".join(words[1:])


def caption_text(reading, lang):
    if lang == "es":
        return (
            f"{reading['title_es']}\n"
            f"{reading['author']}\n\n"
            f"Lectura {int(reading['number']):03d}\n"
            "Lectura completa -> enlace en la bio.\n"
        )
    return (
        f"{reading['title_en']}\n"
        f"{reading['author']}\n\n"
        f"Reading {int(reading['number']):03d}\n"
        "Full reading -> link in bio.\n"
    )


def split_opening(text):
    """Split an opening into two readable beats without hard-coding a reading."""
    text = ' '.join((text or '').split())
    if not text:
        return '', ''
    candidates = [m.end() for m in re.finditer(r'[,;:—–]|\b(?:and|but|or|y|pero|o)\b', text, re.I)]
    midpoint = len(text) / 2
    if candidates:
        cut = min(candidates, key=lambda point: abs(point - midpoint))
    else:
        words = list(re.finditer(r'\S+', text))
        if len(words) < 4:
            return text, text
        cut = words[len(words) // 2 - 1].end()
    first, second = text[:cut].strip(), text[cut:].strip()
    return (first or text), (second or text)


def reel_filter():
    # The opening card never moves or gets cropped. Its five diagram bars are
    # separate transparent objects that travel smoothly inside the field.
    return r"""
color=c=#f2efe7:s=1080x1920:d=14[base];
[base]drawgrid=x=0:y=0:w=54:h=54:color=0x0a0a0a@0.10:thickness=2:enable='between(t,7.0,12.0)',
drawbox=x=72:y=430:w=850:h=16:color=0x0a0a0a@1:t=fill:enable='between(t,7.15,12.0)',
drawbox=x=730:y=446:w=16:h=670:color=0x0a0a0a@1:t=fill:enable='between(t,7.15,12.0)',
drawbox=x=220:y=1110:w=630:h=16:color=0x0a0a0a@1:t=fill:enable='between(t,7.45,12.0)',
drawbox=x=220:y=1110:w=16:h=270:color=0x0a0a0a@1:t=fill:enable='between(t,7.45,12.0)'[grid];
[0:v]scale=1080:1920,setsar=1[opening];
[1:v]format=rgba[bar1];[2:v]format=rgba[bar2];[3:v]format=rgba[bar3];[4:v]format=rgba[bar4];[5:v]format=rgba[bar5];
[6:v]scale=1080:1920,setsar=1[story];
[story]format=rgba[final];
[7:v]format=rgba,split=4[word1a][word1bs][word1cs][word1ds];
[word1bs]scale=1370:321[word1b];[word1cs]scale=920:215[word1c];[word1ds]scale=580:136[word1d];
[8:v]format=rgba,split=4[word2a][word2bs][word2cs][word2ds];
[word2bs]scale=1370:321[word2b];[word2cs]scale=920:215[word2c];[word2ds]scale=580:136[word2d];
[grid][opening]overlay=0:0:enable='between(t,0,7.0)'[card];
[card][bar1]overlay=x='105+35*sin(2*PI*t/5.8)':y=963:enable='between(t,0,7.0)'[drift1];
[drift1][bar2]overlay=x=333:y='1004+28*sin(2*PI*t/5.1+0.8)':enable='between(t,0,7.0)'[drift2];
[drift2][bar3]overlay=x='420+50*sin(2*PI*t/6.4+1.5)':y=1034:enable='between(t,0,7.0)'[drift3];
[drift3][bar4]overlay=x=786:y='1036+36*sin(2*PI*t/5.6+2.1)':enable='between(t,0,7.0)'[drift4];
[drift4][bar5]overlay=x='164+70*sin(2*PI*t/4.9+2.8)':y=1132:enable='between(t,0,7.0)'[stage];
[stage][word1a]overlay=x='1050-(t-7.0)*331.2':y=155:enable='gte(t,7.0)*lt(t,10.75)'[a];
[a][word2a]overlay=x='-920+(t-7.9722)*345.6':y=600:enable='gte(t,7.9722)*lt(t,12)'[b];
[b][word1b]overlay=x='-250+(t-7.2778)*223.2':y=410:enable='gte(t,7.2778)*lt(t,11.5833)'[c];
[c][word2b]overlay=x='760-(t-7.4167)*259.2':y=300:enable='gte(t,7.4167)*lt(t,11.7222)'[d];
[d][word1c]overlay=x='580-(t-7.8333)*234':y=950:enable='gte(t,7.8333)*lt(t,11.5833)'[e];
[e][word2c]overlay=x='-420+(t-8.1111)*201.6':y=1180:enable='gte(t,8.1111)*lt(t,12)'[f];
[f][word1d]overlay=x='45+(t-8.5278)*64.8':y=1380:enable='gte(t,8.5278)*lt(t,11.7222)'[g];
[g][word2d]overlay=x='470-(t-8.3889)*93.6':y=1490:enable='gte(t,8.3889)*lt(t,12)'[h];
[h][9:v]overlay=x=95:y=820:enable='gte(t,7.0)*lt(t,12.0)'[i];
[i][10:v]overlay=x=70:y=1450:enable='gte(t,7.0)*lt(t,12.0)'[n];
[n][final]overlay=0:0:enable='gte(t,12.0)',format=yuv420p[video]
""".replace("\n", "")


def create_reel(number, lang):
    reading, page = get_reading(number)
    data = reading_data(reading, page)
    magick = tool_path("magick")
    ffmpeg = tool_path("ffmpeg")
    font = font_path()
    first_word, second_word = title_words(data["title"][lang])
    error_word = data["error_word"][lang].upper() or "ERROR MACHINE"
    code = f"{int(reading['number']):03d}"
    EXPORTS.mkdir(exist_ok=True)
    reel_path = EXPORTS / f"tsil-{code}-{lang}-glitch-reel.mp4"
    caption_path = EXPORTS / f"tsil-{code}-{lang}-instagram-caption.txt"

    with tempfile.TemporaryDirectory(prefix="tsil-reel-") as temp_dir:
        temp = Path(temp_dir)
        opening_path = temp / "opening.png"
        story_path = temp / "story.png"
        bar_paths = [temp / f"bar-{index}.png" for index in range(1, 6)]
        first_path = temp / "word-one.png"
        second_path = temp / "word-two.png"
        number_path = temp / "number.png"
        error_path = temp / "error.png"
        question_story = EXPORTS / f"tsil-{code}-{lang}-story-question.png"
        graphic_story = EXPORTS / f"tsil-{code}-{lang}-story-graphic.png"
        # Render the complete card without its five diagram bars. The bars
        # are created below as clean shapes, so no slice of text or paper can
        # move across the title.
        opening_html = question_story_html(data, lang, render=True)
        opening_html = opening_html.replace(
            "</style>", ".pixel{display:none!important}</style>", 1
        )
        screenshot(opening_html, opening_path, (1080, 1920), prefer_chrome=True)
        if graphic_story.exists():
            shutil.copyfile(graphic_story, story_path)
        else:
            screenshot(story_html(data, lang, "lines", render=True), story_path, (1080, 1920), prefer_chrome=True)
        for path, size in zip(bar_paths, ((432, 36), (36, 71), (536, 36), (36, 94), (320, 36))):
            run([magick, "-size", f"{size[0]}x{size[1]}", f"xc:{INK}", str(path)])
        render_label(magick, font, "2050x480", 390, INK, first_word, first_path)
        render_label(magick, font, "2050x480", 390, ORANGE, second_word, second_path)
        render_label(magick, font, "880x580", 520, INK, code, number_path)
        render_label(magick, font, "940x118", 50, ORANGE, f"{error_word} / ERROR MACHINE", error_path, opaque=True)
        run([
            ffmpeg, "-y",
            "-loop", "1", "-i", str(opening_path),
            *sum((["-loop", "1", "-i", str(path)] for path in bar_paths), []),
            "-loop", "1", "-i", str(story_path),
            "-loop", "1", "-i", str(first_path),
            "-loop", "1", "-i", str(second_path),
            "-loop", "1", "-i", str(number_path),
            "-loop", "1", "-i", str(error_path),
            "-filter_complex", reel_filter(),
            "-map", "[video]",
            "-t", "14",
            "-r", "30",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-movflags", "+faststart",
            "-an",
            str(reel_path),
        ])

    caption_path.write_text(caption_text(reading, lang), encoding="utf-8")
    return reel_path, caption_path


def main():
    parser = argparse.ArgumentParser(description="Crea un Reel TSIL a partir de un reading publicado localmente.")
    parser.add_argument("--number", required=True, help="Numero del reading, por ejemplo 028")
    parser.add_argument("--lang", choices=("es", "en"), default="en")
    args = parser.parse_args()
    try:
        reel_path, caption_path = create_reel(args.number, args.lang)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"REEL: {reel_path}")
    print(f"CAPTION: {caption_path}")


if __name__ == "__main__":
    main()
