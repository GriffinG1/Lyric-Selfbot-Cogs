import discord
from discord.ext import commands
from time import time


'''Interpret Ly!'''

class LyError(Exception):
    pass


class EmptyStackError(LyError):
    pass


class InputError(LyError):
    pass


class BackupCellError(LyError):
    pass


class FunctionError(LyError):
    pass


class Stack(list):

    def get_value(self):
        if self:
            return self[-1]
        else:
            return None

    def pop_value(self):
        try:
            return self.pop()
        except IndexError:
            raise EmptyStackError("cannot pop from an empty stack")

    def add_value(self, value):
        if type(value) == list:
            self += value
        else:
            self.append(value)


def interpret(program, stdin, output_function, *, debug=False, delay=0, step_by_step=False):
    start = time()
    stacks = [Stack()]
    stack = stacks[0]
    stack_pointer = 0
    idx = 0
    backup = None
    functions = {}
    while idx < len(program):
        char = program[idx]
        try:
            next = program[idx + 1]
        except IndexError:
            next = None
        try:
            last = program[idx - 1]
        except IndexError:
            last = None
        if delay:
            time.sleep(delay)
        try:
            if next == "{":
                pass
            elif char.isdigit():
                stack.add_value(int(char))
            elif char == "[":
                if not stack.get_value():
                    extra = 0
                    for pos, char in enumerate(program[idx + 1:]):
                        # print("Char: " + char)
                        if char == "[":
                            extra += 1
                        elif char == "]":
                            if extra:
                                extra -= 1
                            else:
                                # print("Position: " + str(pos))
                                idx += pos
                                break
            elif char == "]":
                if not stack.get_value():
                    pass
                else:
                    extra = 0
                    for pos, char in reversed(list(enumerate(program[:idx]))):
                        # print("Char: " + char)
                        if char == "]":
                            extra += 1
                        elif char == "[":
                            if extra:
                                extra -= 1
                            else:
                                # print("Position: " + str(pos))
                                idx = pos
                                break
            elif char == "i":
                if last == "&":
                    for val in stdin[:]:
                        stack.add_value(ord(val))
                    stdin = ""
                else:
                    try:
                        stack.add_value(ord(stdin[0]))
                        # print("consumed input " + stdin[0])
                    except IndexError:
                        stack.add_value(0)
                    stdin = stdin[1:]
            elif char == "n":
                if last == "&":
                    if stdin:
                        split_stdin = stdin.split(" ")
                        split_stdin = list(filter(bool, split_stdin))
                        for val in split_stdin[:]:
                            try:
                                stack.add_value(int(val))
                            except ValueError:
                                raise InputError(
                                    "program expected integer input, got string instead")
                        stdin = ""
                    else:
                        pass
                else:
                    if stdin:
                        split_stdin = stdin.split(" ")
                        split_stdin = list(filter(bool, split_stdin))
                        try:
                            stack.add_value(int(split_stdin[0]))
                            stdin = " ".join(split_stdin[1:])
                        except ValueError:
                            raise InputError(
                                "program expected integer input, got string instead")
                    else:
                        stack.add_value(0)
            elif char == "o":
                if last == "&":
                    for val in stack[:]:
                        output_function(chr(val))
                        stack.pop_value()
                else:
                    output_function(chr(stack.pop_value()))
            elif char == "u":
                if last == "&":
                    output_function(" ".join([str(x) for x in stack[:]]))
                    for _ in stack[:]:
                        stack.pop_value()
                else:
                    output_function(stack.pop_value())
            elif char == "r":
                stack.reverse()
            elif char == "+":
                if last == "&":
                    stack.add_value(sum(stack))
                else:
                    x = stack.pop_value()
                    y = stack.pop_value()
                    stack.add_value(y + x)
            elif char == "-":
                x = stack.pop_value()
                y = stack.pop_value()
                stack.add_value(y - x)
            elif char == "*":
                x = stack.pop_value()
                y = stack.pop_value()
                stack.add_value(y * x)
            elif char == "/":
                x = stack.pop_value()
                y = stack.pop_value()
                stack.add_value(y / x)
            elif char == "%":
                x = stack.pop_value()
                y = stack.pop_value()
                stack.add_value(y % x)
            elif char == "^":
                x = stack.pop_value()
                y = stack.pop_value()
                stack.add_value(y ** x)
            elif char == "L":
                x = stack.pop_value()
                stack.add_value(int(stack.get_value() < x))
            elif char == "G":
                x = stack.pop_value()
                stack.add_value(int(stack.get_value() > x))
            elif char == '"':
                for pos, char in enumerate(program[idx + 1:]):
                    # print("Char: " + char)
                    if char == '"':
                        if program[idx + pos] == "\\":
                            stack.add_value(ord(char))
                        else:
                            # print("Position: " + str(pos))
                            idx += pos + 1
                            break
                    elif char == "n":
                        if program[idx + pos] == "\\":
                            stack.add_value(ord('\n'))
                        else:
                            stack.add_value(ord(char))
                    elif char == "\\" and program[idx + pos + 2] in ['"', 'n']:
                        pass
                    else:
                        stack.add_value(ord(char))
            elif char == "#":
                for pos, char in enumerate(program[idx + 1:]):
                    # print("Char: " + char)
                    if char == '\n':
                        # print("Position: " + str(pos))
                        idx += pos + 1
                        break
                else:  # we didn't break, thus we've reached EOF
                    return
            elif char == ";":
                return
            elif char == ":":
                if last == "&":
                    for val in stack[:]:
                        stack.add_value(val)
                else:
                    val = stack.get_value()
                    if val is not None:
                        stack.add_value(val)
            elif char == "p":
                if last == "&":
                    for _ in stack[:]:
                        stack.pop_value()
                else:
                    stack.pop_value()
            elif char == "!":
                if stack.pop_value() == 0:
                    stack.add_value(1)
                else:
                    stack.add_value(0)
            elif char == "l":
                if type(backup) == list:
                    for item in backup[:]:
                        stack.add_value(item)
                elif backup is not None:
                    stack.add_value(backup)
                else:
                    raise BackupCellError(
                        "attempted to load backup, but backup is empty")
            elif char == "s":
                if last == "&":
                    backup = stack[:]
                else:
                    backup = stack.get_value()
            elif char == "f":
                x = stack.pop_value()
                y = stack.pop_value()
                stack.add_value(x)
                stack.add_value(y)
            elif char == "<":
                if stack_pointer > 0:
                    stack_pointer -= 1
                else:
                    # since this changes the indexing we don't need to decrement the pointer
                    stacks.insert(0, Stack())
                stack = stacks[stack_pointer]
            elif char == ">":
                try:
                    stacks[stack_pointer + 1]
                except IndexError:
                    stacks.append(Stack())
                stack_pointer += 1
                stack = stacks[stack_pointer]
            elif char == "$":
                for _ in range(stack.pop_value()):
                    extra = 0
                    for pos, char in enumerate(program[idx + 1:]):
                        # print("Char: " + char)
                        if char == "[":
                            extra += 1
                        elif char == "]":
                            if extra:
                                extra -= 1
                            else:
                                # print("Position: " + str(pos))
                                idx += pos + 1
                                break
            elif char == "?":
                x = stack.pop_value()
                y = stack.pop_value()
                stack.add_value(random.randint(y, x))
            elif char == "{":
                function_name = last
                function_body = ""
                extra = 0
                for pos, char in enumerate(program[idx + 1:]):
                    # print("Char: " + char)
                    if char == "{":
                        extra += 1
                    elif char == "}":
                        if extra:
                            extra -= 1
                        else:
                            # print("Position: " + str(pos))
                            idx += pos
                            break
                    else:
                        function_body += char
                if function_name in functions:
                    function_params = function_body.split(",")
                    function_input = ""
                    for param in function_params:
                        if param.isdigit():
                            function_input += param + " "
                        elif param == "c":
                            function_input += chr(stack.pop_value())
                        elif param == "i":
                            function_input += str(stack.pop_value())

                    def stack_addition(val):
                        global stack
                        stack.add_value(val)

                    def function_execution(val):
                        global stack_addition
                        if type(val) != str:
                            stack.add_value(val)
                        else:
                            stack.add_value(ord(val))
                    try:
                        interpret(functions[function_name], function_input, function_execution,
                                  debug=debug, delay=delay, step_by_step=step_by_step)
                    except FunctionError as err:
                        err_info = str(err).split("$$")
                        output_function("Error occurred in function {}, index {}, instruction {} (zero-indexed, includes comments)".format(
                            function_name, err_info[1], err_info[2]))
                        output_function(err_info[0])
                        return
                else:
                    functions[function_name] = function_body
            elif char == "=":
                if stack.pop_value() == stack.get_value():
                    stack.add_value(1)
                else:
                    stack.add_value(0)
            elif char == "(":
                body = ""
                extra = 0
                for pos, char in enumerate(program[idx + 1:]):
                    # print("Char: " + char)
                    if char == "(":
                        extra += 1
                    elif char == ")":
                        if extra:
                            extra -= 1
                        else:
                            # print("Position: " + str(pos))
                            idx += pos
                            break
                    elif char.isdigit():
                        body += char
                try:
                    stack.add_value(int(body))
                except TypeError:
                    pass
            elif char == "y":
                stack.add_value(len(stack))
            elif char == "c":
                stack.add_value(len(str(stack.pop_value())))
            elif char == "S":
                x = str(stack.pop_value())
                for digit in x:
                    stack.add_value(int(digit))
            elif char == "J":
                try:
                    x = int("".join([str(x) for x in stack]))
                    for _ in stack[:]:
                        stack.pop_value()
                    stack.add_value(x)
                except TypeError:
                    raise EmptyStackError("cannot join an empty stack")
            elif char == "a":
                stack.sort()
        except (LyError, ZeroDivisionError) as err:
            if output_function.__name__ == "function_execution":
                raise FunctionError("{}: {}$${}$${}".format(
                    type(err).__name__, str(err), str(idx), char))
            output_function("Error occurred at program index {}, instruction {} (zero-indexed, includes comments)".format(idx, char))
            output_function(type(err).__name__ + ": " + str(err))
            return
        idx += 1
        if debug:
            output_function("%debug%" + " | ".join([char, str(stacks), str(backup), output_function.__name__]))
        if step_by_step:
            input()
        if time() - start > 3:
            return False

class Ly:

    def __init__(self, bot):
        self.bot = bot
        self.output = ""
        self.total_output = ""

    @commands.command(pass_context=True)
    async def ly(self, ctx, *, msg):
        """Interpret a Ly program."""
        args = msg.split()
        input = [x.split("input=")[1] for x in args if x.startswith("input=")]
        if not input:
            input = ""
        else:
            input = input[0]
        try:
            args.remove([x for x in args if x.startswith("input=")][0])
        except (ValueError, IndexError):
            pass
        debug = [x.split("debug=")[1] == "True" for x in args if x.startswith("debug=")]
        if debug:
            debug = debug[0]
        try:
            args.remove([x for x in args if x.startswith("debug=")][0])
        except (ValueError, IndexError):
            pass
        program = " ".join(args)
        self.output = ""
        self.total_output = ""
        if debug:
            def normal_execution(val):
                if val.startswith("%debug%"):
                    self.output += str(val.split("%debug%")[1]) + "\n"
                else:
                    self.output += "Outputted: " + str(val) + "\n"
                    self.total_output += str(val)
        else:
            def normal_execution(val):
                self.output += str(val)  
        result = interpret(program, input, normal_execution, debug=debug)
        if result is False:
            output += "... (time limit hit, output truncated)"
        if debug:
            self.output += "\nTotal output: " + self.total_output
        await self.bot.send_message(ctx.message.channel, "```\n" + self.output + "```")

def setup(bot):
    bot.add_cog(Ly(bot))