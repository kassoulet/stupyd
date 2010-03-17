#/usr/bin/python3

"""
stupyd - indent-like-python preprocessor - (c) 2010 Gautier Portet - <kassoulet gmail com>
"""

from sys import argv, stderr
from re import match
import re

stderr.write('stupyd - indent-like-python preprocessor - (c) 2010 Gautier Portet\n')

cpp_rules = dict(
    remove_empty_lines=True,

    # must keep end line colon
    keep_colon = ['private', 'protected', 'public', 'case', 'default'],

    # indent-free
    not_a_block = ['private', 'protected', 'public'],

    # line comment
    line_comment = '//',

    # line
    line_continuation = '\\',

    # string inserted at indent begin and end
    indent_begin = ' {',
    indent_end = '}\n',
    
    semicolon = ';\n',
    
    # do not append semicolon
    no_semicolon = [r';$', r',$', r'"$', r'^#'],

    # add a semicolon
    semicolon_after_indent = ['struct', 'class'],

    #
    replaces = [
        [r'for ([^:()]*):', r'for (\1):'], # add parenthesis to for
        [r'if ([^:()]*):', r'if (\1):'], # add parenthesis to if
        [r'while ([^:()]*):', r'while (\1):'], # add parenthesis to while
        [r'switch ([^:()]*):', r'switch (\1):'], # add parenthesis to switch
    ]
)

class Converter():

    def __init__(self, rules):
        """
        Create a converter for the specified set of rules.
        """
        self.__dict__.update(rules)
    
    def convert(self, filename):
        """
        Convert a file.
        """
        self.lines = open(filename).read().split('\n')

        self.remove_tabs()
        self.join_lines()
        self.strip_comments()
        self.indent()
        
        print('\n'.join(self.lines))

    def get_indent(self, s):
        """
        Return number of leading spaces/tabs of given string.
        """
        i = 0
        while s[i].isspace():
            i += 1
        return i

    def deindent(self, stack, indent):
        """
        Handles deindentation.
        """
        lines = []
        semicolon = False
        while(1):
            if not stack:
                break
            n, semicolon_ = stack.pop()
            if n < indent:
                stack.append((n, semicolon_,))
                break
            semicolon = semicolon_
            lines.append('%s' % (self.indent_end))
        if semicolon:
            lines.append(self.semicolon)
        return lines

    def indent(self):
        """
        Process indentation.
        """

        old = 0
        indent_stack = []
        lines = []
        add_semicolon = False
    
        for lineno, line in enumerate(self.lines):
            line = line.rstrip()
            sline = line.strip()
            if not sline:
                if not self.remove_empty_lines:
                    lines.append('')            
                continue
            if sline == 'pass':
                lines.append('')            
                continue
                
            indent = self.get_indent(line)

            diff = indent - old
            if diff > 0:
                indent_stack.append((old, add_semicolon,))
                if add_semicolon:
                    add_semicolon = False
            if diff < 0:
                line = ''.join(self.deindent(indent_stack, indent)) + line

            for r, sub in self.replaces:
                line = re.sub(r, sub, line)

            if line.endswith(':'):
                not_block = False
                for a in self.not_a_block:
                    if sline.startswith(a):
                        not_block = True
                keep = False
                for a in self.keep_colon:
                    if sline.startswith(a):
                        keep = True
                if not keep:
                    line = line[:-1]
                if not not_block:
                    line += self.indent_begin
                for ex in self.semicolon_after_indent:
                    if re.search(ex, line):
                        add_semicolon = True
            else:
                semicolon = True            
                for ex in self.no_semicolon:
                    if re.search(ex, line):
                        #print 'skipping', ex, line
                        semicolon = False
                        break
                if semicolon:            
                    line += self.semicolon

            old = indent
            lines.append(line)
        
        lines.extend(self.deindent(indent_stack, 0))
        self.lines = lines
    

    def remove_tabs(self):
        """
        Convert tabulations to 8 spaces.
        """
        lines = []
        for line in self.lines:
            line = line.replace('\t', ' ' * 8)
            lines.append(line)
        self.lines = lines

    def join_lines(self):
        """
        Concatenate continued lines.
        """
        if not self.line_continuation:
            return
        lines = []
        concat = []
        for line in self.lines:
            if line.endswith(self.line_continuation):
                concat.append(line[:-1])
                continue
            if concat:
                line = ''.join(concat) + line
                lines.append(line)
                for i in range(len(concat)):
                    lines.append('')
            else:
                lines.append(line)
            concat = []
        self.lines = lines

    def strip_comments(self):
        """
        Remove all comments from lines.
        """
        if not self.line_comment:
            return
        lines = []
        for line in self.lines:
            line, comment = self.split_comment(line)
            lines.append(line)
        self.lines = lines

    def split_comment(self, line):
        """
        Split a line in valid_code, comment.
        Only line comments for now.
        """
        # find all comment beginnings
        regex = r'%s.*?' % self.line_comment
        ss = [m.start() for m in re.finditer(regex, line)]

        # find all strings
        mm = list(re.finditer(r'"(.*[\\"]*.*)"', line))
        if mm:
            for m in mm:
                for s in ss:
                    if not m.start() < s < m.end():
                        return line[:s], line[s:]
        elif ss:
            # no strings, cut !
            return line[:ss[0]], line[ss[0]:]
        return line, None
    

converter = Converter(cpp_rules)
converter.convert(argv[1])


