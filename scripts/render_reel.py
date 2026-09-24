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


def render_question_label(magick, font, text, output):
    """Render a transparent, wrapped opening phrase over the fixed Story card."""
    run([
        magick,
        "-background", "none",
        "-fill", INK,
        "-font", str(font),
        "-style", "Italic",
        "-pointsize", "104",
        "-interline-spacing", "-12",
        "-gravity", "northwest",
        "-size", "900x410",
        "caption:" + text,
        str(output),
    ])


def title_words(title):
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
    # The question arrives in two readable beats. The collision only starts
    # after both have landed; the final story has room to be inspected.
    return r"""
color=c=#f2efe7:s=1080x1920:d=14[base];
[base]drawgrid=x=0:y=0:w=54:h=54:color=0x0a0a0a@0.10:thickness=2:enable='between(t,7.0,12.0)',
drawbox=x=72:y=430:w=850:h=16:color=0x0a0a0a@1:t=fill:enable='between(t,7.15,12.0)',
drawbox=x=730:y=446:w=16:h=670:color=0x0a0a0a@1:t=fill:enable='between(t,7.15,12.0)',
drawbox=x=220:y=1110:w=630:h=16:color=0x0a0a0a@1:t=fill:enable='between(t,7.45,12.0)',
drawbox=x=220:y=1110:w=16:h=270:color=0x0a0a0a@1:t=fill:enable='between(t,7.45,12.0)'[grid];
[0:v]scale=1080:1920,setsar=1[opening];
[1:v]format=rgba[qone];
[2:v]format=rgba[qtwo];
[3:v]scale=1080:1920,setsar=1[story];
[story]split=5[band1source][band2source][band3source][band4source][storyfinal];
[band1source]crop=1080:140:0:245,scale=1450:188[b1];
[band2source]crop=1080:130:0:545,scale=1510:182[b2];
[band3source]crop=1080:130:0:805,scale=1390:170[b3];
[band4source]crop=1080:140:0:1090,scale=1480:192[b4];
[storyfinal]format=rgba,fade=t=in:st=12.0:d=0.18:alpha=1[final];
[4:v]format=rgba,split=4[word1a][word1bs][word1cs][word1ds];
[word1bs]scale=1370:321[word1b];[word1cs]scale=920:215[word1c];[word1ds]scale=580:136[word1d];
[5:v]format=rgba,split=4[word2a][word2bs][word2cs][word2ds];
[word2bs]scale=1370:321[word2b];[word2cs]scale=920:215[word2c];[word2ds]scale=580:136[word2d];
[base][opening]overlay=0:0:enable='between(t,0,7.0)'[card];
[card][qone]overlay=70:270:enable='between(t,1.2,4.0)'[first];
[first][qtwo]overlay=70:270:enable='between(t,4.0,7.0)'[intro];
[grid][intro]overlay=0:0:enable='between(t,0,7.0)'[stage];
[stage][word1a]overlay=x='1050-(t-7.0)*920':y=155:enable='between(t,7.0,8.35)'[a];
[a][word2a]overlay=x='-920+(t-7.35)*960':y=600:enable='between(t,7.35,8.8)'[b];
[b][word1b]overlay=x='-250+(t-7.1)*620':y=410:enable='between(t,7.1,8.65)'[c];
[c][word2b]overlay=x='760-(t-7.15)*720':y=300:enable='between(t,7.15,8.7)'[d];
[d][word1c]overlay=x='580-(t-7.3)*650':y=950:enable='between(t,7.3,8.65)'[e];
[e][word2c]overlay=x='-420+(t-7.4)*560':y=1180:enable='between(t,7.4,8.8)'[f];
[f][word1d]overlay=x='45+(t-7.55)*180':y=1380:enable='between(t,7.55,8.7)'[g];
[g][word2d]overlay=x='470-(t-7.5)*260':y=1490:enable='between(t,7.5,8.8)'[h];
[h][6:v]overlay=x=95:y='820+(t-8.15)*80':enable='between(t,8.15,12.0)'[i];
[i][b1]overlay=x='max(-1450\,min(-90\,(t-7.5)*1600-1450))':y=270:enable='between(t,7.5,8.85)'[j];
[j][b2]overlay=x='min(1080\,max(-280\,1080-(t-7.75)*1500))':y=560:enable='between(t,7.75,9.0)'[k];
[k][b3]overlay=x='max(-1390\,min(-110\,(t-7.95)*1650-1390))':y=875:enable='between(t,7.95,8.9)'[l];
[l][b4]overlay=x='min(1080\,max(-300\,1100-(t-8.2)*1700))':y=1170:enable='between(t,8.2,9.1)'[m];
[m][7:v]overlay=x=70:y=1450:enable='between(t,8.5,12.0)'[n];
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
        question_one_path = temp / "question-one.png"
        question_two_path = temp / "question-two.png"
        story_path = temp / "story.png"
        first_path = temp / "word-one.png"
        second_path = temp / "word-two.png"
        number_path = temp / "number.png"
        error_path = temp / "error.png"
        opening_one, opening_two = split_opening(data['ante'][lang] or data['lead'][lang])
        screenshot(question_story_html(data, lang, render=True, question_override=''), opening_path, (1080, 1920), prefer_chrome=True)
        render_question_label(magick, font, opening_one, question_one_path)
        render_question_label(magick, font, opening_two, question_two_path)
        screenshot(story_html(data, lang, "lines", render=True), story_path, (1080, 1920), prefer_chrome=True)
        render_label(magick, font, "2050x480", 390, INK, first_word, first_path)
        render_label(magick, font, "2050x480", 390, ORANGE, second_word, second_path)
        render_label(magick, font, "880x580", 520, INK, code, number_path)
        render_label(magick, font, "940x118", 50, ORANGE, f"{error_word} / ERROR MACHINE", error_path, opaque=True)
        run([
            ffmpeg, "-y",
            "-loop", "1", "-i", str(opening_path),
            "-loop", "1", "-i", str(question_one_path),
            "-loop", "1", "-i", str(question_two_path),
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
