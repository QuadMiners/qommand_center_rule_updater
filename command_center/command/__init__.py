#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
    change <server_id>
        * 서버 변경

    system

        status  <server_id>
            * 상태 정보
            * 정기 점검에 필요한 모든 정보

        process <server_id>
            * 프로세스 상태 정보
            * 주요 데몬별 버전 정보
        hardware_info <server_id>
            * 모든 hardware 정보
            * memory , disk , 서버 model , server uuid, os 버전 등
        memory
            * 메모리 정보
        cpu
            * cpu 상태
        disk

        network

"""
import argparse
import cmd
import datetime
import re
import subprocess

from blessed import Terminal
import curses
import curses.textpad
import ipaddress
import sys
import math
import pandas as pd

from termcolor import cprint, colored

from command_center.library.AppObject import QObject
from command_center.library.utils import str_to_datetime


class ToolQuery(QObject):
    _start_date = None
    _end_date = None

    def __init__(self, init=None):
        if init is not None:
            for key, value in init.items():
                setattr(self, key, value)

    def attr_to_set(self, vals):
        ret = set()
        for val in vals:
            ret.add(val)
        return ret

    def required_check(self):
        ret = True

        if self._start_date is None:
            cprint("start_date is not set. required !! ", 'red')
            ret = False
        if self._end_date is None:
            cprint("end_date is not set. required !! ", 'red')
            ret = False

        return ret

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, val):
        if isinstance(val, datetime.datetime):
            self._start_date = val
        else:
            self._start_date = str_to_datetime(val)

    @property
    def end_date(self):
        return self._end_date

    @end_date.setter
    def end_date(self, val):
        if isinstance(val, datetime.datetime):
            self._end_date = val
        else:
            self._end_date = str_to_datetime(val)


filter_option = re.compile("((?P<cmd>.*?)\|(?P<filter>.*?)$)|^(?P<cmd2>.*?)$")


class NotSupportedFilterException(Exception):
    pass


def cmd_parse(arg):
    data = filter_option.search(arg)
    result = data.groupdict()
    if len(arg) <= 0:
        return None, 0, None

    if result.get('cmd2', None):
        ret = tuple(map(str, arg.split()))
        return ret, len(ret), None
    else:
        cmd = result.get('cmd', None)
        c_filter = result.get('filter', None)
        if c_filter and len(c_filter) > 0:
            r_filter = tuple(map(str, c_filter.split()))
            if r_filter[0] not in ('grep', 'exclude', 'limit', 'more'):
                cprint("not support filter options: {0}".format(r_filter[0]), color='red')
                # raise NotSupportedFilterException("not support filter options: {0}".format(r_filter[0]))
                return None, 0, None
            if len(r_filter) >= 2 and len(r_filter[1]) > 1:
                if r_filter[0] in ['more', 'limit']:
                    r_filter = (r_filter[0], r_filter[1])
                else:
                    r_filter = (r_filter[0], re.compile(r_filter[1]))
            else:
                cprint("filter length greater than 1 : Filter [ {0} ] ".format(r_filter[1]), color='red')
                # raise NotSupportedFilterException("filter length greater than 1 : Filter [ {0} ] ".format(r_filter[1]))
                return None, 0, None
        else:
            raise NotSupportedFilterException("Not Supported")

        ret = tuple(map(str, cmd.split()))
    return ret, len(ret), r_filter


class ToolCommandMixin(cmd.Cmd):
    # help command text need regex string
    # commands_help = ['\?', 'help']
    hidden_methods = None

    def cmd_parse(self, args):
        cmd_str, cmd_len, l_filter = cmd_parse(args)
        return cmd_str, cmd_len, l_filter

    def get_names(self):
        names = dir(self.__class__)
        hidden_methods = self.hidden_methods if 'hidden_methods' in names else []
        if hidden_methods is None:
            return names
        return [n for n in names if n not in hidden_methods]

    def choice_value(self, array_json):
        """
            {
                "select_value" : "display Name ",
                "select_value" : "display Name ",
            }
        """
        cprint("option ", 'red')
        cprint("", 'red')
        cprint("%-30s | %s" % ("info", "setting value"), 'yellow')
        cprint("-" * 50, 'yellow')
        for key, value in array_json:
            cprint("%-30s | %s" % (value, key), 'yellow')
        print("\n")

    def do_exit(self, arg):
        """
            exit      : You can't finish without required checking.
        """
        return True

    def emptyline(self):
        pass

    def exec_shell_command(self, cmd_str, readline=False):
        """
            execute shell command
        :param cmd_str:
        :return:
        """
        try:
            p = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if readline is True:
                return_code = p.returncode

                if return_code:
                    raise Exception(p.stdout, return_code)

                for line in p.stdout.readlines():
                    yield line.strip()
            else:
                p_status = p.wait(timeout=10)
                output, error = p.communicate()
                if error != b'':
                    cprint('output : %s' % output)
                    cprint('error : %s' % error)
                    return None
                return output.decode('utf-8')

        except OSError as e:
            cprint('OSError: {0}'.format(e), "red")
            return None

        except subprocess.SubprocessError as e:
            cprint('exception : %s' % e, "red")
            return None

    def filter(self, line: str, l_filter: tuple) -> bool:
        """
            filter
                grep , exclude

            if filter():  == > grep
                            return False  in False not in True

            if filter(): ==> exclude
                            return True  not in True  in False


        """
        ret = True
        if l_filter:
            fl = l_filter[1]
            if l_filter[0] == 'grep':
                if fl.search(line):
                    ret = False
            elif l_filter[0] == 'exclude':
                if not fl.search(line):
                    ret = False
        else:
            ret = False
        return ret


class NBBArgParser(argparse.ArgumentParser):
    def print_usage(self, file=None):
        cprint(self.format_usage(), 'yellow')

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        self.print_usage()
        args = {'prog': self.prog, 'message': message}
        cprint(('error: %(message)s') % args, 'red')


class NBBScreenMixin(object):
    lineno = 1
    width = 0
    height = 0
    stdscr: curses.window = None
    key = None
    maintitle = None

    def print_line(self, line, highlight=False):
        if self.lineno > (self.height - 2):
            return
        try:
            if highlight:
                line += " " * (self.width - len(line))
                self.stdscr.addstr(self.lineno, 0, line, curses.A_REVERSE)
            else:
                line += " " * (self.width - len(line))
                self.stdscr.addstr(self.lineno, 0, line, 0)
        except curses.error as e:
            # print("Curses Error : {0}".format(e))
            # raise
            pass
        self.lineno += 1

    def initscreen(self, stdscr, *args, **kwargs):
        self.stdscr = stdscr
        interval = 0
        k = 0
        self.maintitle = kwargs.get('title')
        # Clear and refresh the screen for a blank canvas
        stdscr.clear()
        stdscr.refresh()

        # Start colors in curses
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

        terminal = Terminal()

        while (self.key != 'q'):
            try:
                self.key = terminal.inkey(timeout=0.2)
                self.key_event()
                # Initialization
                stdscr.clear()
                self.height, self.width = stdscr.getmaxyx()

                # Declaration of strings
                statusbarstr = "Press 'q' to exit | STATUS BAR"
                if k == 0:
                    keystr = "No key press detected..."[:self.width - 1]

                # Rendering some text
                whstr = self.maintitle
                start_x_title = int((self.width // 2) - (len(whstr) // 2) - len(whstr) % 2)

                stdscr.attron(curses.color_pair(1))
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(0, 0, "")
                stdscr.addstr(0, start_x_title, whstr)
                """
                    Function 
                """
                values = self.datas(interval)
                self.refresh_window(*values)
                interval = 0.5

                # Render status bar
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(self.height - 1, 0, statusbarstr)
                stdscr.addstr(self.height - 1, len(statusbarstr), " " * (self.width - len(statusbarstr) - 1))
                stdscr.attroff(curses.color_pair(3))

                # Refresh the screen
                stdscr.refresh()

            except (KeyboardInterrupt, SystemExit):
                stdscr.refresh()
                break
        self.close()

    def key_event(self):
        key = self.key

    def close(self):
        """ clean up """
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


class NBBScrollScreen(object):
    UP = -1
    DOWN = 1
    MODE = 0
    MODE_NAME = ['General', 'SearchDown', 'SearchUp']
    statusbarstr = "Press 'q' to exit | STATUS BAR"
    custom_color_pair = {}

    def __init__(self, items, custom_color_pair={}):
        """ Initialize the screen window
        Attributes
            window: A full curses screen window
            width: The width of `window`
            height: The height of `window`
            max_lines: Maximum visible line count for `result_window`
            top: Available top line position for current page (used on scrolling)
            bottom: Available bottom line position for whole pages (as length of items)
            current: Current highlighted line number (as window cursor)
            page: Total page count which being changed corresponding to result of a query (starts from 0)
            mode: 0 -> common, 1 -> search
            ┌--------------------------------------┐
            |1. Item                               |
            |--------------------------------------| <- top = 1
            |2. Item                               |
            |3. Item                               |
            |4./Item///////////////////////////////| <- current = 3
            |5. Item                               |
            |6. Item                               |
            |7. Item                               |
            |8. Item                               | <- max_lines = 7
            |--------------------------------------|
            |9. Item                               |
            |10. Item                              | <- bottom = 10
            |                                      |
            |                                      | <- page = 1 (0 and 1)
            └--------------------------------------┘
        Returns
            None
        """
        self.window = None

        self.width = 0
        self.height = 0

        self.custom_color_pair = custom_color_pair

        self.init_curses()

        if isinstance(items, pd.DataFrame):
            self.items = items
        else:
            self.items = pd.DataFrame(items)

        self.max_lines = curses.LINES - 2
        self.top = 0
        self.bottom = self.items.size

        self.current = 0
        self.page = self.bottom // self.max_lines
        self.maintitle = ""
        self.search = None
        self.search_idx = []

    def init_curses(self):
        """Setup the curses"""
        self.window = curses.initscr()
        self.window.keypad(True)

        curses.noecho()
        curses.cbreak()

        curses.start_color()
        # Status Bar
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        # Header Bar
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_CYAN)
        # Selected Line
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        # Search Text Highlight
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_CYAN)

        # custom_color_set = {
        #     "some text": {
        #         "font": curses.COLOR_BLACK,
        #         "background": curses.COLOR_WHITE
        #     }
        # }
        custom_color_pair_int = 5
        for key, color_set in self.custom_color_pair.items():
            curses.init_pair(custom_color_pair_int, color_set['font'], color_set['background'])
            color_set['color_pair_idx'] = custom_color_pair_int
            custom_color_pair_int += 1

        self.height, self.width = self.window.getmaxyx()

    def run(self):
        """Continue running the TUI until get interrupted"""
        try:
            self.input_stream()
        except KeyboardInterrupt:
            pass
        finally:
            curses.endwin()

    def input_stream(self):

        """Waiting an input and run a proper method according to type of input"""
        while True:
            try:
                self.display()
                ch = self.window.getch()
                if ch in (curses.KEY_UP, ord('k')):
                    self.scroll(self.UP)
                elif ch in (curses.KEY_DOWN, ord('j')):
                    self.scroll(self.DOWN)
                elif ch in (curses.KEY_LEFT, ord('l')):
                    self.paging(self.UP)
                elif ch in (curses.KEY_RIGHT, ord('h')):
                    self.paging(self.DOWN)
                elif ch == ord('/'):
                    self.MODE = 1
                    self.search_input_text("/")
                elif ch == ord('?'):
                    self.MODE = 2
                    self.search_input_text("?")

                exit_key = [curses.ascii.ESC, ord('q'), ord('Q')]
                if self.MODE == 0:
                    # General Mode
                    if ch in exit_key:
                        # Exit Command
                        break
                elif self.MODE == 1 or self.MODE == 2:
                    # Search Mode
                    if ch == ord('n'):
                        # foward
                        if self.MODE == 1:
                            # SearchDown
                            self.search_down_next()
                        elif self.MODE == 2:
                            # SearchUp
                            self.search_up_next()
                    elif ch == ord('N'):
                        # reverse
                        if self.MODE == 1:
                            # SearchUp
                            self.search_up_next()
                        elif self.MODE == 2:
                            # SearchDown
                            self.search_down_next()
                    elif ch in exit_key:
                        # Exit Search Mode
                        self.MODE = 0
            except Exception as e:
                self.window.refresh()

    def search_input_text(self, prefix="/"):
        self.window.addstr(self.height - 1, 0, prefix)
        curses.echo()
        search_text = self.window.getstr(self.height - 1, len(prefix),
                                         self.width - (len(prefix) - len(self.statusbarstr)))
        curses.noecho()
        search_text = search_text.decode(encoding="utf-8").strip()
        self.search = re.compile(search_text)
        self.search_idx = list(self.items[self.items[0].str.contains(search_text)].index)

    def search_down_next(self):
        try:
            minValue = min(list(filter(lambda x: x - (self.current + self.top) > 0, self.search_idx)))
            self.move_page_idx(minValue)
        except:
            pass

    def search_up_next(self):
        try:
            maxValue = max(list(filter(lambda x: x - (self.current + self.top) < 0, self.search_idx)))
            self.move_page_idx(maxValue)
        except:
            pass

    def move_page_idx(self, idx):
        self.current = 0
        div, mod = divmod(idx, self.max_lines)
        self.top = (div * self.max_lines) + mod

    def scroll(self, direction):
        """Scrolling the window when pressing up/down arrow keys"""
        # next cursor position after scrolling
        next_line = self.current + direction

        # Up direction scroll overflow
        # current cursor position is 0, but top position is greater than 0
        if (direction == self.UP) and (self.top > 0 and self.current == 0):
            self.top += direction
            return
        # Down direction scroll overflow
        # next cursor position touch the max lines, but absolute position of max lines could not touch the bottom
        if (direction == self.DOWN) and (next_line == self.max_lines) and (self.top + self.max_lines < self.bottom):
            self.top += direction
            return
        # Scroll up
        # current cursor position or top position is greater than 0
        if (direction == self.UP) and (self.top > 0 or self.current > 0):
            self.current = next_line
            return
        # Scroll down
        # next cursor position is above max lines, and absolute position of next cursor could not touch the bottom
        if (direction == self.DOWN) and (next_line < self.max_lines) and (self.top + next_line < self.bottom):
            self.current = next_line
            return

    def paging(self, direction):
        """Paging the window when pressing left/right arrow keys"""
        current_page = (self.top + self.current) // self.max_lines
        next_page = current_page + direction
        # The last page may have fewer items than max lines,
        # so we should adjust the current cursor position as maximum item count on last page
        if next_page == self.page:
            self.current = min(self.current, self.bottom % self.max_lines - 1)

        # Page up
        # if current page is not a first page, page up is possible
        # top position can not be negative, so if top position is going to be negative, we should set it as 0
        if (direction == self.UP) and (current_page > 0):
            self.top = max(0, self.top - self.max_lines)
            return
        # Page down
        # if current page is not a last page, page down is possible
        if (direction == self.DOWN) and (current_page < self.page):
            self.top += self.max_lines
            return

    def display(self):
        """Display the items on window"""
        self.window.erase()

        skip_idx = -1
        current = self.current + 1

        # for idx, item in enumerate(self.items[self.top:self.top + self.max_lines]):
        items = [item for item in list(self.items.iloc[self.top:self.top + self.max_lines, :].to_dict()[0].values())]
        for idx, item in enumerate(items):
            idx += 1
            try:
                color_pair = 0
                if skip_idx != -1 and skip_idx > idx:
                    pass
                elif idx == current:
                    # Highlight the current cursor line
                    color_pair = curses.color_pair(3)
                    self.print_item(idx, 0, item[:self.width], color_pair)
                    if len(item) > self.width:
                        multiline = math.ceil(len(item) / self.width)
                        if not self.height < idx + multiline:
                            skip_idx = idx + multiline
                            for line_idx in range(1, multiline):
                                line_start_idx = (self.width * line_idx)
                                line_end_idx = line_start_idx + self.width
                                # Selected Second Line Print
                                if line_idx == multiline:
                                    space = (self.width - len(item[line_start_idx:])) * " "
                                    self.print_item(idx + line_idx, 0, item[line_start_idx:] + space, color_pair)
                                else:
                                    self.print_item(idx + line_idx, 0, item[line_start_idx:line_end_idx], color_pair)
                else:
                    self.print_item(idx, 0, item[:self.width], color_pair)
                    skip_idx == -1
            except Exception as e:
                raise

        # Rendering some text
        whstr = (self.maintitle + '(%s, %s)' % (self.MODE_NAME[self.MODE], self.top + self.current))
        start_x_title = int((self.width // 2) - (len(whstr) // 2) - len(whstr) % 2)

        self.window.addstr(0, start_x_title, whstr, curses.A_BOLD | curses.color_pair(2))
        # Declaration of strings
        statusbarstr = (" " * (self.width - len(self.statusbarstr) - 1)) + self.statusbarstr

        # Render status bar
        self.window.addstr(self.height - 1, 0, statusbarstr, curses.color_pair(1))
        self.window.refresh()

    def print_item(self, y=0, x=0, text="", color_pair=0):
        self.window.addnstr(y, x, text, self.width, color_pair)
        self.custom_color(y, text)
        if self.MODE == 1 or self.MODE == 2:
            self.search_text_highlight(y, text)

    def custom_color(self, y, text):
        for key, value in self.custom_color_pair.items():
            search_list = list(re.compile(key).finditer(text))
            color_pair = curses.color_pair(value['color_pair_idx'])
            color_pair = curses.A_BOLD | color_pair if value['bold'] else color_pair
            for search_item in search_list:
                start = search_item.start()
                end = search_item.end()
                highlight_text = text[start:end]
                self.window.addnstr(y, start, highlight_text, self.width, color_pair)

    def search_text_highlight(self, y, text):
        search_list = list(self.search.finditer(text))
        for search_item in search_list:
            start = search_item.start()
            end = search_item.end()
            highlight_text = text[start:end]
            self.window.addnstr(y, start, highlight_text, self.width, curses.color_pair(4))


def ValueInput(inputtext, valuetype=None, Default=False, color='magenta'):
    value = None
    while True:
        try:
            if isinstance(valuetype, list):
                cprint("\n---- Please enter in ------", "green")
                cprint(" , ".join(valuetype), "yellow")
                cprint("-" * 50, "green")
            value = input(colored(f'{inputtext} ', color))

            if Default or value:
                if value.strip() in ('exit', 'quit'):
                    return 'exit'

                if isinstance(valuetype, list):
                    if not Default or value:
                        if [item for item in valuetype if item == value]:
                            break
                        else:
                            cprint("The value entered is invalid  ", "red")
                            continue
                if valuetype == int:
                    try:
                        value = int(value)
                        value = str(value)
                    except ValueError:
                        cprint("Not Number Value  Please re-enter. ", "red")
                        continue
                if len(value.strip()) <= 0:
                    value = Default
                break
            else:
                cprint("This is not the Default Value  [ {0} ]  ".format(value), "red")

        except KeyboardInterrupt as k:
            raise k

    return value is None and "" or value.strip()


def ValueInput_dict(inputtext, valuetype_dict=None, Default=False):
    value_dict = dict()
    while True:

        try:
            if isinstance(valuetype_dict, dict):
                cprint("=======================", "green")
                cprint(" Please enter in  ", "green")
                cprint(" , ".join(valuetype_dict.keys()), "green")
                cprint("=======================", "green")

            value = input(inputtext)

            if Default or value:
                if isinstance(valuetype_dict, dict):
                    if not Default or value:
                        keys = value.strip().split(' ')[0::2]
                        values = value.lstrip().split(' ')[1::2]
                        for k, v in zip(keys, values):
                            if k not in valuetype_dict:
                                cprint(f"{k} is not in {', '.join(valuetype_dict.keys())}", "red")
                                return None
                            elif valuetype_dict[k] == 'ipaddr':
                                try:
                                    ipaddress.ip_address(v)
                                    value_dict[k] = v
                                except ValueError:
                                    cprint(f"The entered value type of {k} is invalid  ", "red")
                                    return None
                            elif type(v) != valuetype_dict[k]:
                                cprint(f"The entered value type of {k} is invalid  ", "red")
                                return None
                            else:
                                value_dict[k] = v
                break
            else:
                cprint("This is not the Default Value  [ {0} ]  ".format(value), "red")
                return None

        except KeyboardInterrupt:
            cprint("<<<< Install End  { KeyBoard Interrupt } >>> ", "red")
            sys.exit(1)
    return value_dict


filter_option = re.compile("((?P<cmd>.*?)\|(?P<filter>.*?)$)|^(?P<cmd2>.*?)$")


class NotSupportedFilterException(Exception):
    pass


def cmd_parse(arg):
    data = filter_option.search(arg)
    result = data.groupdict()
    if len(arg) <= 0:
        return None, 0, None

    if result.get('cmd2', None):
        ret = tuple(map(str, arg.split()))
        return ret, len(ret), None
    else:
        cmd = result.get('cmd', None)
        c_filter = result.get('filter', None)
        if c_filter and len(c_filter) > 0:
            r_filter = tuple(map(str, c_filter.split()))
            if r_filter[0] not in ('grep', 'exclude', 'limit', 'more'):
                cprint("not support filter options: {0}".format(r_filter[0]), color='red')
                # raise NotSupportedFilterException("not support filter options: {0}".format(r_filter[0]))
                return None, 0, None
            if len(r_filter) >= 2 and len(r_filter[1]) > 1:
                if r_filter[0] in ['more', 'limit']:
                    r_filter = (r_filter[0], r_filter[1])
                else:
                    r_filter = (r_filter[0], re.compile(r_filter[1]))
            else:
                cprint("filter length greater than 1 : Filter [ {0} ] ".format(r_filter[1]), color='red')
                # raise NotSupportedFilterException("filter length greater than 1 : Filter [ {0} ] ".format(r_filter[1]))
                return None, 0, None
        else:
            raise NotSupportedFilterException("Not Supported")

        ret = tuple(map(str, cmd.split()))
    return ret, len(ret), r_filter


def print_help_msg(summary: str, usage: list = [], options_args: list = [], filter_opt: list = [], color="green"):
    """
    print help message
    summary : 커맨드에 대한 기본 요약 정보 ex) NBB Syslog Print
    usage: 사용 방법 리스트, 각 라인을 요소로 구분해서 입력. ex) ["(nbb)# log [-d {date}| -a {app name}| -e {bool}]"]
    options: 옵션에 대한 설명
            ex) ["opt1", "opt2", "arg1", "agr2"]
            ex) ["-d: Select Date [YYYY-MM-DD]", "-a: Select Application", "-e: Print Error [True | False]"]
            ex) ["ipaddr: xxx.xxx.xxx.xxx", "start date / end date: YYYYMMDDHH24MI"]
    filter_opt: 사용가능한 필터 목록
            ex) ["grep", "exclude"]
    """
    msg = summary + \
          ("\nUsage:\n\t{usage_str}".format(usage_str="\n\t".join(usage)) if usage else "") + \
          ("\nOptions and Arguments:\n\t{opt_arg_str}".format(
              opt_arg_str="\n\t".join(options_args)) if options_args else "") + \
          ("\nFilter Options:\n\t{filter_str}".format(filter_str=", ".join(filter_opt)) if filter_opt else "")
    cprint(msg, color)
