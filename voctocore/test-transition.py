#!/usr/bin/env python3
from configparser import SafeConfigParser
from lib.transitions import Composites, Transitions, L, T, R, B, X, Y
from PIL import Image, ImageDraw, ImageFont
# for integer maximum size
import sys
# for calling convert to generate animated GIF
from subprocess import call
import copy
import re
import logging
import argparse


def read_arguments():
    global Args
    # read arguments
    __all__ = ['Args']
    parser = argparse.ArgumentParser(
        description='transition - tool to generate voctomix transition animations for testing')
    parser.add_argument('composite', nargs='*',
                        help="list of composites to generate transitions between (use all available if not given)")
    parser.add_argument('-f', '--config', action='store', default="voctocore/default-config.ini",
                        help="name of the configuration file to load")
    parser.add_argument('-m', '--map', action='count',
                        help="print transition table")
    parser.add_argument('-l', '--list', action='count',
                        help="list available composites")
    parser.add_argument('-g', '--generate', action='count',
                        help="generate animation")
    parser.add_argument('-t', '--title', action='count', default=0,
                        help="draw composite names and frame count")
    parser.add_argument('-k', '--keys', action='count', default=0,
                        help="draw key frames")
    parser.add_argument('-c', '--corners', action='count', default=0,
                        help="draw calculated interpolation corners")
    parser.add_argument('-C', '--cross', action='count', default=0,
                        help="draw image cross through center")
    parser.add_argument('-r', '--crop', action='count', default=0,
                        help="draw image cropping border")
    parser.add_argument('-n', '--number', action='count',
                        help="when using -g: use consecutively numbers as file names")
    parser.add_argument('-P', '--nopng', action='count',
                        help="when using -g: do not write PNG files (forces -G)")
    parser.add_argument('-L', '--leave', action='count',
                        help="when using -g: do not delete temporary PNG files")
    parser.add_argument('-G', '--nogif', action='count',
                        help="when using -g: do not generate animated GIFS")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="also print WARNING (-v), INFO (-vv) and DEBUG (-vvv) messages")
    parser.add_argument('-s', '--size', action='store', default="960x540",
                        help="set frame size 'WxH' W and H must be pixels")
    parser.add_argument('-S', '--fps', '--speed', action='store', default=25,
                        help="animation resolution (frames per second)")
    Args = parser.parse_args()
    # implicit options
    if Args.nopng:
        Args.nogif = 1


def init_log():
    global Args, log
    # set up logging
    FORMAT = '%(message)s'
    logging.basicConfig(format=FORMAT)
    logging.root.setLevel([logging.ERROR, logging.WARNING,
                           logging.INFO, logging.DEBUG][Args.verbose])
    log = logging.getLogger('Transitions Test')


def read_config(filename=None):
    global log, Args
    if not filename:
        filename = Args.config
    # load INI files
    config = SafeConfigParser()
    config.read(filename)
    if Args.size:
        r = re.match(
            r'^\s*([\d]+)\s*x\s*([\d]+)\s*$', Args.size)
        if r:
            size = [int(r.group(1)), int(r.group(2))]
    else:
        # read frame size
        size = config.get('output', 'size').split('x')
        size = [int(size[0]), int(size[1])]

    # read frames per second
    fps = int(Args.fps if Args.fps else config.get('output', 'fps'))
    # read composites from configuration
    log.info("reading composites from configuration...")
    composites = Composites.configure(config.items('composites'), size)
    log.debug("read %d composites:\n\t%s\t" %
              (len(composites), '\n\t'.join(sorted(composites))))
    # maybe overwirte targets by arguments
    if Args.composite:
        # check for composites in arguments
        targets = [composites[c] for c in set(Args.composite)]
    else:
        # list of all relevant composites we like to target
        targets = Composites.targets(composites)
    intermediates = Composites.intermediates(composites)
    # list targets and itermediates
    if Args.list:
        print("%d targetable composite(s):\n\t%s\t" %
              (len(targets), '\n\t'.join([t.name for t in targets])))
        print("%d intermediate composite(s):\n\t%s\t" %
              (len(intermediates), '\n\t'.join([t.name for t in intermediates])))
    # read transitions from configuration
    log.info("reading transitions from configuration...")
    transitions = Transitions.configure(
        config.items('transitions'), composites, targets, fps)
    log.info("read %d transition(s)" % transitions.count())
    if Args.map:
        print("transition table:\n%s" % transitions)
    # maybe overwirte targets by arguments
    if Args.composite:
        # check for composites in arguments
        sequence = Args.composite
    else:
        # generate sequence of targets
        sequence = Transitions.travel([t.name for t in targets])
    log.debug("using %d target composite(s):\n\t%s\t" %
              (len(targets), '\n\t'.join([t.name for t in targets])))

    # return config
    return size, fps, sequence, transitions, composites


def draw_text(draw, size, line_or_pos, text, fill=(255, 255, 255, 255), align=0):
    # get a font
    font = ImageFont.truetype("FreeSans.ttf",
                              11 if size[X] < 400 else
                              (13 if size[X] < 800 else
                               20))
    if type(line_or_pos) == int:
        assert not align
        line_factor = 1.3
        line_height = font.getsize("|")[Y] * line_factor
        # measure text size
        x = (size[X] - draw.textsize(text, font=font)[X]) / 2
        if line_or_pos >= 0:
            y = line_height * (line_or_pos - 1) + line_height * \
                (line_factor - 1.0)
        else:
            y = size[Y] + line_height * line_or_pos
    else:
        assert type(line_or_pos) == list
        x, y = line_or_pos
        if align == 0:
            x = (x - draw.textsize(text, font=font)[X]) / 2
        elif align == -1:
            x = x - draw.textsize(text, font=font)[X]
            y = y - draw.textsize(text, font=font)[Y]
    draw.text([x, y], text, font=font, fill=fill)


def draw_composite(size, composite, swap=False):
    # indices in size and tsize
    X, Y = 0, 1
    # create an image to draw into
    imageBg = Image.new('RGBA', size, (40, 40, 40, 255))
    imageA = Image.new('RGBA', size, (0, 0, 0, 0))
    imageB = Image.new('RGBA', size, (0, 0, 0, 0))
    imageFg = Image.new('RGBA', size, (0, 0, 0, 0))
    # create a drawing context
    drawBg = ImageDraw.Draw(imageBg)
    drawA = ImageDraw.Draw(imageA)
    drawB = ImageDraw.Draw(imageB)
    drawFg = ImageDraw.Draw(imageFg)
    if Args.cross:
        # mark center lines
        drawFg.line((size[X] / 2, 0, size[X] / 2, size[Y]),
                    fill=(0, 0, 0, 128))
        drawFg.line((0, size[Y] / 2, size[X], size[Y] / 2),
                    fill=(0, 0, 0, 128))

    # simulate swapping sources
    a, b = composite.A(), composite.B()
    if swap:
        a, b = b, a
        if Args.title:
            draw_text(drawFg, size, 2, "(swapped sources)")

    if Args.crop:
        # draw source frame
        drawA.rectangle(a.rect, outline=(128, 0, 0, a.alpha))
        drawB.rectangle(b.rect, outline=(0, 0, 128, b.alpha))
    # draw cropped source frame
    drawA.rectangle(a.cropped(), fill=(128, 0, 0, a.alpha))
    drawB.rectangle(b.cropped(), fill=(0, 0, 128, b.alpha))

    # silly way to draw on RGBA frame buffer, hey - it's python
    return Image.alpha_composite(
        Image.alpha_composite(
            Image.alpha_composite(imageBg, imageA), imageB), imageFg)


def draw_transition(size, transition, info=None):
    # get where to flip sources
    flip_at = transition.flip()
    # animation as a list of images
    images = []
    # render all frames
    for i in range(transition.frames()):
        # create an image to draw into
        imageBg = draw_composite(size, transition.composites[i],
                                 flip_at is not None and i >= flip_at)
        imageDesc = Image.new('RGBA', size, (0, 0, 0, 0))
        imageFg = Image.new('RGBA', size, (0, 0, 0, 0))
        # create a drawing context
        drawBg = ImageDraw.Draw(imageBg)
        drawDesc = ImageDraw.Draw(imageDesc)
        drawFg = ImageDraw.Draw(imageFg)

        acolor = (256, 128, 128, 128)
        bcolor = (128, 128, 256, 128)

        if Args.keys:
            n = 0
            for key in transition.keys():
                ac = key.A().rect
                bc = key.B().rect
                drawDesc.rectangle(ac, outline=acolor)
                draw_text(drawDesc, size,
                          [ac[L] + 2, ac[T] + 2],
                          "A.%d" % n, acolor, 1)
                drawDesc.rectangle(bc, outline=bcolor)
                draw_text(drawDesc, size,
                          [bc[R] - 2, bc[B] - 2],
                          "B.%d" % n, bcolor, -1)
                n += 1

        if Args.corners:
            # draw calculated corner points
            for n in range(0, i + 1):
                ar = transition.A(n).rect
                br = transition.B(n).rect
                drawDesc.rectangle(
                    (ar[R] - 2, ar[T] - 2, ar[R] + 2, ar[T] + 2), fill=acolor)
                drawDesc.rectangle(
                    (br[L] - 2, br[T] - 2, br[L] + 2, br[T] + 2), fill=bcolor)

                drawDesc.rectangle(
                    (ar[L] - 1, ar[T] - 1, ar[L] + 1, ar[T] + 1), fill=acolor)
                drawDesc.rectangle(
                    (ar[L] - 1, ar[B] - 1, ar[L] + 1, ar[B] + 1), fill=acolor)
                drawDesc.rectangle(
                    (ar[R] - 1, ar[B] - 1, ar[R] + 1, ar[B] + 1), fill=acolor)

                drawDesc.rectangle(
                    (br[R] - 1, br[T] - 1, br[R] + 1, br[T] + 1), fill=bcolor)
                drawDesc.rectangle(
                    (br[L] - 1, br[B] - 1, br[L] + 1, br[B] + 1), fill=bcolor)
                drawDesc.rectangle(
                    (br[R] - 1, br[B] - 1, br[R] + 1, br[B] + 1), fill=bcolor)

        if Args.title:
            draw_text(drawFg, size, -3, transition.name())
            if not info is None:
                draw_text(drawFg, size,  -2, info)
            draw_text(
                drawFg, size, -1, " → ".join([c.name for c in transition.keys()]))
            draw_text(drawFg, size, 1, "Frame %d" % i)
        # silly way to draw on RGBA frame buffer, hey - it's python
        images.append(
            Image.alpha_composite(
                Image.alpha_composite(imageBg, imageDesc), imageFg)
        )
    # return resulting animation images
    return images


def save_transition_gif(filename, size, info, transition, time):
    frames = transition.frames()
    # save animation
    log.info("generating transition '%s' (%d ms, %d frames)..." %
             (transition.name(), int(time), frames))
    images = draw_transition(size, transition, info)
    if not Args.nopng:
        imagenames = []
        delay = int(time / 10.0 / frames)
        log.info("saving animation frames into temporary files '%s0000.png'..'%s%04d.png'..." %
                 (filename, filename, transition.frames() - 1))
        for i in range(0, len(images)):
            imagenames.append("%s%04d.png" % (filename, i))
            # save an image
            images[i].save(imagenames[-1])
        # generate animated GIF by calling system command 'convert'
        if not Args.nogif:
            log.info("creating animated file '%s.gif' with delay %d..." %
                     (filename, delay))
            call(["convert", "-loop", "0"] +
                 ["-delay", "100"] + imagenames[:1] +
                 ["-delay", "%d" % delay] + imagenames[1:-1] +
                 ["-delay", "100"] + imagenames[-1:] +
                 ["%s.gif" % filename])
        # delete temporary files?
        if not Args.leave:
            log.info("deleting temporary PNG files...")
            call(["rm"] + imagenames)


def render_composites(size, composites):
    global log
    log.debug("rendering composites (%d items):\n\t%s\t" %
              (len(composites), '\n\t'.join([c.name for c in composites])))
    for c in composites:
        if Args.generate:
            print("saving composite file '%s.png' (%s)..." % (c.name, c.name))
            draw_composite(size, c).save("%s.png" % c.name)


def render_sequence(size, fps, sequence, transitions, composites):
    global log
    log.debug("rendering generated sequence (%d items):\n\t%s\t" %
              (len(sequence), '\n\t'.join(sequence)))
    # begin at first transition
    prev_name = sequence[0]
    prev = composites[prev_name]
    # cound findings
    not_found = []
    found = []
    # process sequence through all possible transitions
    for c_name in sequence[1:]:
        # fetch prev composite
        c = composites[c_name]
        # get the right transtion between prev and c
        log.debug("request transition (%d/%d): %s → %s" %
                  (len(found) + 1, len(sequence) - 1, prev_name, c_name))
        # actually search for a transitions that does a fade between prev and c
        transition = transitions.find(prev, c)
        # count findings
        if not transition:
            # report fetched transition
            log.warning("no transition found for: %s → %s" %
                        (prev_name, c_name))
            not_found.append("%s -> %s" % (prev_name, c_name))
        else:
            # report fetched transition
            log.debug("transition found: %s\n%s" %
                      (transition.name(), transition))
            found.append(transition.name())
            # get sequence frames
            frames = transition.frames()
            if Args.generate:
                filename = ("%03d" % len(
                    found)) if Args.number else "%s_%s" % (prev_name, c_name)
                print("saving transition animation file '%s.gif' (%s, %d frames)..." %
                      (filename, transition.name(), frames))
                # generate test images for transtion and save into animated GIF
                save_transition_gif(filename, size, "%s → %s" % (prev_name, c_name),
                                    transition, frames / fps * 1000.0)
        # remember current transition as next previous
        prev_name, prev = c_name, c
    # report findings
    if found:
        if Args.list:
            print("%d transition(s) available:\n\t%s" %
                  (len(found), '\n\t'.join(sorted(found))))
    if not_found:
        print("%d transition(s) could NOT be found:\n\t%s" %
              (len(not_found), "\n\t".join(sorted(not_found))))

read_arguments()
init_log()
cfg = read_config()
render_composites(cfg[0], Composites.targets(cfg[4]))
render_sequence(*cfg)
