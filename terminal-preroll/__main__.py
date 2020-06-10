"""
Terminal Preroll is a python applet designed to pretty-print to the terminal, creating a small, flexible animation
for use as a livestream preroll. It is minimally configurable, accepting a special set of configuration items.

Refer to https://github.com/zadammac/terminal_preroll for documentation and usage information

"""

__version__ = "pre-alpha"

import argparse
from blessings import Terminal
from datetime import timedelta
import json
import termcolor
from math import floor, ceil
from time import sleep


# Class Definitions


class namespace(object):
    """Abusing inheritance in this way gives us a catch-all namespace object for return-oriented design."""
    pass


# Function Definitions
def print_banner(banner_details, width):
    """Accepts an object of the type provided to ns by get_banner; that is, a dictionary of lists with the keys
    "banner_lines" and "line_colors". It then prints these out using termcolor and returns the number of lines printed.

    :param banner_details:
    :return: an integer representing the number of lines consumed.
    """

    lines = banner_details["banner_strings"]
    colors = banner_details["line_colors"]
    lines_printed = 0

    for i in range(len(lines)):
        line = ""
        try:
            line = termcolor.colored(lines[i].center(width-2), colors[i])
        except KeyError:  # This condition should only arise if a color was not provided.
            line = lines[i].center(width-2)
        finally:
            line_out = line
            print("|%s|" % line_out)
            lines_printed += 1

    return lines_printed


def print_time_row(ns):
    """Looks for a few arguments in the namespace object and prints a single row to the terminal as a result"""
    time_label = "|    Time: %s    |     Phase: %s" % (str(timedelta(seconds=ns.time_remaining)), ns.current_section)
    time_label = time_label + " " * (ns.term.width - (len(time_label)+1)) + "|"
    print(time_label)
    return ns


def first_screen(ns):
    """Now that we have a prepared screen, we can print the needful into it. This is the easiest the first time we do
    so, as there is no need for incremental updates or scrolling the screen.

    :param ns: a `namespace` state object, which must be instantiated by the parse_args, get_banner, and
    get_hype_strings functions provided in this package.
    :return: updated state object
    """
    with ns.term.location(0, 0):
        horizontal_frame = "[" + ("=" * (ns.term.width-2)) + "]"
        print(horizontal_frame)
        banner_height = print_banner(ns.banner, ns.term.width)
        print(horizontal_frame)
        ns = print_time_row(ns)
        print(horizontal_frame)

        ns.header_height = banner_height + 5
        ns.footer_height = 7

        hist_window_length = print_blank_history_window(ns.header_height, ns.footer_height, ns.term)

        ns.history = []
        for i in range(hist_window_length):
            ns.history.append("")

        ns.history.pop(0)
        ns.history.append("Becoming clever...")

        ns = print_footer(ns)
        ns.counting = True

        return ns


def print_blank_history_window(min, max, terminal):
    """Figures out the first row under the header, and writes until it reaches the row above the footer.

    :param min: integer number describing the height of the header
    :param max: integer number describing the height of the footer
    :param width: overall width of the terminal in characters.
    :return:
    """
    row = "|%s|" % (str(" " * (terminal.width-2)))
    lines_printed = 0
    for line in range((terminal.height - min - max)):
        print(row)
        lines_printed += 1

    return lines_printed


def print_footer(ns):
    """Updates state and prints the footer. More than a little gross."""

    ns.ticks += 1
    time_elapsed = ns.time_total - ns.time_remaining
    horizontal_frame = "[" + ("=" * (ns.term.width - 2)) + "]"
    print(horizontal_frame)
    row = "|%s|" % (str(" " * (ns.term.width - 2)))
    print(row)
    status_print(time_elapsed, ns.time_total, "Overall Progress", "Working...")
    status_print(ns.ticks, ns.ticks_per_segment, "Current Task    ", "Working...")
    print(row)
    print(horizontal_frame)

    if ns.ticks == ns.ticks_per_segment:
        ns.ticks = 0
        ns = increment_hype_objects(ns)

    return ns


def status_print(done, total, job, message):
    """Prints a basic status message. If not interrupted, prints it on one line"""
    percent = int(round((done / total) * 100))
    length_bar = Terminal().width - 29 - len(str(percent)) - len(message)
    done_bar = int(round((done / total) * length_bar))
    done_bar_print = str("#" * int(done_bar) + "-" * int(round((length_bar - done_bar))))
    if percent == 100:  # More Pretty Printing!
        if message == "Working...":
            message = "Done!    "
    text = ("\r| {0}: [{1}] {2}% - {3} |".format(job, done_bar_print, percent, message))
    print(text)


def parse_args(namespace):
    """Parse arguments and return the modified namespace object"""
    ns = namespace
    parser = argparse.ArgumentParser(description="""Terminal Preroll is a python applet designed to pretty-print to the terminal, creating a small, flexible animation
for use as a livestream preroll. It is minimally configurable, accepting a special set of configuration items.

Refer to https://github.com/zadammac/terminal_preroll for documentation and usage information""")
    parser.add_argument('-t', help="Time to count down in minutes",
                        action="store")
    parser.add_argument('-b', help="Path to the banner descriptor file",
                        action="store")
    parser.add_argument('-s', help="Path to the hype file", action="store")
    args = parser.parse_args()

    ns.term = Terminal()

    ns.time_remaining = int(args.t) * 60  # args are strings unless you say otherwise!
    ns.time_total = ns.time_remaining
    with open(args.b, "r") as f:
        ns.banner = json.load(f)
    with open(args.s, "r") as f:
        ns.hype_dict = json.load(f)
        ns.sections = list(ns.hype_dict.keys())
        ns.current_section = ns.sections.pop(0)

    return ns


def prepare_hype(ns):
    ns.ticks = -1

    # We need to know the grand total of hype strings in order to figure out how long each should take.
    sum_of_hype_objects = 0
    for each in ns.sections:
        for line in ns.hype_dict[each]:
            sum_of_hype_objects += 1
    ns.ticks_per_segment = int(ns.time_total / sum_of_hype_objects)
    ns.current_hype_string = ns.hype_dict[ns.current_section].pop(0)  # Grabs the first item from the first dict.
    return ns


def runtime():
    """Having a singular runtime like this allows easier if-name-main protection"""
    state = namespace()
    state = parse_args(state)
    state = prepare_hype(state)
    state = first_screen(state)
    while state.counting:
        state = update_screen(state)  # There's a lot of state that happens here.
        sleep(1)
        state.time_remaining -= 1
        if state.time_remaining < 1:
            state.counting = False
    exit(0)


def increment_hype_objects(ns):
    """ Changes hype state.

    :param ns:
    :return:
    """
    ns.history.pop(0)  # We want to take the first item out to make the list scroll UP
    ns.history.append(ns.current_hype_string)  # This is done, so it goes on the list.

    current_section = ns.hype_dict[ns.current_section]

    if len(current_section) == 0:  # If we finish a section, we must rotate.
        ns.current_section = ns.sections.pop(0)

    ns.current_hype_string = ns.hype_dict[ns.current_section].pop(0)

    return ns


def update_screen(ns):
    """"""
    with ns.term.location(0, ns.header_height-3):
        print_time_row(ns)
    with ns.term.location(0, ns.header_height):
        for each in ns.history:
            length = len(each)
            row = "|%s%s|" % (each, (" "*(ns.term.width-length-2)))
            print(row)
        ns = print_footer(ns)

    return ns


# Runtime goes here:
if __name__ == "__main__":
    runtime()
