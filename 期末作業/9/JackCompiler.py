"""
Jack Compiler - Nand2Tetris Chapter 10 & 11
將 Jack 語言編譯成 VM 代碼
"""

import os
import sys
import re
from enum import Enum
from typing import List, Dict, Optional

# ============= Tokenizer =============

class TokenType(Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    IDENTIFIER = "identifier"
    INT_CONST = "integerConstant"
    STRING_CONST = "stringConstant"

class JackTokenizer:
    KEYWORDS = {
        'class', 'constructor', 'function', 'method', 'field', 'static',
        'var', 'int', 'char', 'boolean', 'void', 'true', 'false', 'null',
        'this', 'let', 'do', 'if', 'else', 'while', 'return'
    }
    
    SYMBOLS = {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', 
               '/', '&', '|', '<', '>', '=', '~'}
    
    def __init__(self, input_text: str):
        self.tokens = []
        self.current = 0
        self._tokenize(input_text)
    
    def _tokenize(self, text: str):
        # 移除註解
        text = self._remove_comments(text)
        
        i = 0
        while i < len(text):
            # 跳過空白
            if text[i].isspace():
                i += 1
                continue
            
            # 字串常數
            if text[i] == '"':
                j = i + 1
                while j < len(text) and text[j] != '"':
                    j += 1
                self.tokens.append((TokenType.STRING_CONST, text[i+1:j]))
                i = j + 1
                continue
            
            # 符號
            if text[i] in self.SYMBOLS:
                self.tokens.append((TokenType.SYMBOL, text[i]))
                i += 1
                continue
            
            # 數字
            if text[i].isdigit():
                j = i
                while j < len(text) and text[j].isdigit():
                    j += 1
                self.tokens.append((TokenType.INT_CONST, int(text[i:j])))
                i = j
                continue
            
            # 關鍵字或識別符
            if text[i].isalpha() or text[i] == '_':
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                    j += 1
                word = text[i:j]
                if word in self.KEYWORDS:
                    self.tokens.append((TokenType.KEYWORD, word))
                else:
                    self.tokens.append((TokenType.IDENTIFIER, word))
                i = j
                continue
            
            i += 1
    
    def _remove_comments(self, text: str) -> str:
        # 移除 // 註解
        text = re.sub(r'//.*', '', text)
        # 移除 /* */ 註解
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        return text
    
    def has_more_tokens(self) -> bool:
        return self.current < len(self.tokens)
    
    def advance(self):
        self.current += 1
    
    def token_type(self) -> TokenType:
        return self.tokens[self.current][0]
    
    def token_value(self):
        return self.tokens[self.current][1]
    
    def peek(self, offset=1):
        idx = self.current + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return None

# ============= Symbol Table =============

class SymbolKind(Enum):
    STATIC = "static"
    FIELD = "field"
    ARG = "argument"
    VAR = "local"

class SymbolTable:
    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.indices = {kind: 0 for kind in SymbolKind}
    
    def start_subroutine(self):
        self.subroutine_scope = {}
        self.indices[SymbolKind.ARG] = 0
        self.indices[SymbolKind.VAR] = 0
    
    def define(self, name: str, type_: str, kind: SymbolKind):
        symbol = {
            'type': type_,
            'kind': kind,
            'index': self.indices[kind]
        }
        
        if kind in [SymbolKind.STATIC, SymbolKind.FIELD]:
            self.class_scope[name] = symbol
        else:
            self.subroutine_scope[name] = symbol
        
        self.indices[kind] += 1
    
    def var_count(self, kind: SymbolKind) -> int:
        return self.indices[kind]
    
    def kind_of(self, name: str) -> Optional[SymbolKind]:
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]['kind']
        if name in self.class_scope:
            return self.class_scope[name]['kind']
        return None
    
    def type_of(self, name: str) -> Optional[str]:
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]['type']
        if name in self.class_scope:
            return self.class_scope[name]['type']
        return None
    
    def index_of(self, name: str) -> Optional[int]:
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]['index']
        if name in self.class_scope:
            return self.class_scope[name]['index']
        return None

# ============= VM Writer =============

class VMWriter:
    def __init__(self):
        self.output = []
    
    def write_push(self, segment: str, index: int):
        self.output.append(f"push {segment} {index}")
    
    def write_pop(self, segment: str, index: int):
        self.output.append(f"pop {segment} {index}")
    
    def write_arithmetic(self, command: str):
        self.output.append(command)
    
    def write_label(self, label: str):
        self.output.append(f"label {label}")
    
    def write_goto(self, label: str):
        self.output.append(f"goto {label}")
    
    def write_if(self, label: str):
        self.output.append(f"if-goto {label}")
    
    def write_call(self, name: str, n_args: int):
        self.output.append(f"call {name} {n_args}")
    
    def write_function(self, name: str, n_locals: int):
        self.output.append(f"function {name} {n_locals}")
    
    def write_return(self):
        self.output.append("return")
    
    def get_output(self) -> str:
        return '\n'.join(self.output)

# ============= Compilation Engine =============

class CompilationEngine:
    def __init__(self, tokenizer: JackTokenizer):
        self.tokenizer = tokenizer
        self.symbol_table = SymbolTable()
        self.vm_writer = VMWriter()
        self.class_name = ""
        self.label_counter = 0
    
    def _get_label(self, prefix: str) -> str:
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label
    
    def _expect(self, expected):
        value = self.tokenizer.token_value()
        if value != expected:
            raise Exception(f"Expected {expected}, got {value}")
        self.tokenizer.advance()
    
    def compile_class(self):
        self._expect('class')
        self.class_name = self.tokenizer.token_value()
        self.tokenizer.advance()
        self._expect('{')
        
        # classVarDec*
        while self.tokenizer.token_value() in ['static', 'field']:
            self.compile_class_var_dec()
        
        # subroutineDec*
        while self.tokenizer.token_value() in ['constructor', 'function', 'method']:
            self.compile_subroutine()
        
        self._expect('}')
    
    def compile_class_var_dec(self):
        kind_str = self.tokenizer.token_value()
        kind = SymbolKind.STATIC if kind_str == 'static' else SymbolKind.FIELD
        self.tokenizer.advance()
        
        type_ = self.tokenizer.token_value()
        self.tokenizer.advance()
        
        # varName
        name = self.tokenizer.token_value()
        self.symbol_table.define(name, type_, kind)
        self.tokenizer.advance()
        
        # (',' varName)*
        while self.tokenizer.token_value() == ',':
            self.tokenizer.advance()
            name = self.tokenizer.token_value()
            self.symbol_table.define(name, type_, kind)
            self.tokenizer.advance()
        
        self._expect(';')
    
    def compile_subroutine(self):
        self.symbol_table.start_subroutine()
        
        subroutine_type = self.tokenizer.token_value()  # constructor|function|method
        self.tokenizer.advance()
        
        return_type = self.tokenizer.token_value()  # void|type
        self.tokenizer.advance()
        
        subroutine_name = self.tokenizer.token_value()
        self.tokenizer.advance()
        
        # method 需要將 this 加入參數
        if subroutine_type == 'method':
            self.symbol_table.define('this', self.class_name, SymbolKind.ARG)
        
        self._expect('(')
        self.compile_parameter_list()
        self._expect(')')
        
        # subroutineBody
        self._expect('{')
        
        # varDec*
        while self.tokenizer.token_value() == 'var':
            self.compile_var_dec()
        
        # 寫入 function 宣告
        n_locals = self.symbol_table.var_count(SymbolKind.VAR)
        self.vm_writer.write_function(f"{self.class_name}.{subroutine_name}", n_locals)
        
        # constructor 需要分配記憶體
        if subroutine_type == 'constructor':
            n_fields = self.symbol_table.var_count(SymbolKind.FIELD)
            self.vm_writer.write_push("constant", n_fields)
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)
        
        # method 需要設定 this
        if subroutine_type == 'method':
            self.vm_writer.write_push("argument", 0)
            self.vm_writer.write_pop("pointer", 0)
        
        # statements
        self.compile_statements()
        
        self._expect('}')
    
    def compile_parameter_list(self):
        if self.tokenizer.token_value() == ')':
            return
        
        type_ = self.tokenizer.token_value()
        self.tokenizer.advance()
        name = self.tokenizer.token_value()
        self.symbol_table.define(name, type_, SymbolKind.ARG)
        self.tokenizer.advance()
        
        while self.tokenizer.token_value() == ',':
            self.tokenizer.advance()
            type_ = self.tokenizer.token_value()
            self.tokenizer.advance()
            name = self.tokenizer.token_value()
            self.symbol_table.define(name, type_, SymbolKind.ARG)
            self.tokenizer.advance()
    
    def compile_var_dec(self):
        self._expect('var')
        type_ = self.tokenizer.token_value()
        self.tokenizer.advance()
        
        name = self.tokenizer.token_value()
        self.symbol_table.define(name, type_, SymbolKind.VAR)
        self.tokenizer.advance()
        
        while self.tokenizer.token_value() == ',':
            self.tokenizer.advance()
            name = self.tokenizer.token_value()
            self.symbol_table.define(name, type_, SymbolKind.VAR)
            self.tokenizer.advance()
        
        self._expect(';')
    
    def compile_statements(self):
        while self.tokenizer.token_value() in ['let', 'if', 'while', 'do', 'return']:
            if self.tokenizer.token_value() == 'let':
                self.compile_let()
            elif self.tokenizer.token_value() == 'if':
                self.compile_if()
            elif self.tokenizer.token_value() == 'while':
                self.compile_while()
            elif self.tokenizer.token_value() == 'do':
                self.compile_do()
            elif self.tokenizer.token_value() == 'return':
                self.compile_return()
    
    def compile_let(self):
        self._expect('let')
        var_name = self.tokenizer.token_value()
        self.tokenizer.advance()
        
        # 處理陣列
        is_array = False
        if self.tokenizer.token_value() == '[':
            is_array = True
            self.tokenizer.advance()
            self.compile_expression()
            self._expect(']')
            
            # 計算陣列地址
            self._push_variable(var_name)
            self.vm_writer.write_arithmetic("add")
        
        self._expect('=')
        self.compile_expression()
        self._expect(';')
        
        if is_array:
            self.vm_writer.write_pop("temp", 0)
            self.vm_writer.write_pop("pointer", 1)
            self.vm_writer.write_push("temp", 0)
            self.vm_writer.write_pop("that", 0)
        else:
            self._pop_variable(var_name)
    
    def compile_if(self):
        self._expect('if')
        self._expect('(')
        self.compile_expression()
        self._expect(')')
        
        label_true = self._get_label("IF_TRUE")
        label_false = self._get_label("IF_FALSE")
        label_end = self._get_label("IF_END")
        
        self.vm_writer.write_if(label_true)
        self.vm_writer.write_goto(label_false)
        self.vm_writer.write_label(label_true)
        
        self._expect('{')
        self.compile_statements()
        self._expect('}')
        
        if self.tokenizer.token_value() == 'else':
            self.vm_writer.write_goto(label_end)
            self.vm_writer.write_label(label_false)
            
            self.tokenizer.advance()
            self._expect('{')
            self.compile_statements()
            self._expect('}')
            
            self.vm_writer.write_label(label_end)
        else:
            self.vm_writer.write_label(label_false)
    
    def compile_while(self):
        self._expect('while')
        
        label_start = self._get_label("WHILE_EXP")
        label_end = self._get_label("WHILE_END")
        
        self.vm_writer.write_label(label_start)
        
        self._expect('(')
        self.compile_expression()
        self._expect(')')
        
        self.vm_writer.write_arithmetic("not")
        self.vm_writer.write_if(label_end)
        
        self._expect('{')
        self.compile_statements()
        self._expect('}')
        
        self.vm_writer.write_goto(label_start)
        self.vm_writer.write_label(label_end)
    
    def compile_do(self):
        self._expect('do')
        self.compile_subroutine_call()
        self._expect(';')
        self.vm_writer.write_pop("temp", 0)  # 丟棄返回值
    
    def compile_return(self):
        self._expect('return')
        
        if self.tokenizer.token_value() != ';':
            self.compile_expression()
        else:
            self.vm_writer.write_push("constant", 0)
        
        self._expect(';')
        self.vm_writer.write_return()
    
    def compile_expression(self):
        self.compile_term()
        
        ops = {'+': 'add', '-': 'sub', '*': None, '/': None,
               '&': 'and', '|': 'or', '<': 'lt', '>': 'gt', '=': 'eq'}
        
        while self.tokenizer.token_value() in ops:
            op = self.tokenizer.token_value()
            self.tokenizer.advance()
            self.compile_term()
            
            if op == '*':
                self.vm_writer.write_call("Math.multiply", 2)
            elif op == '/':
                self.vm_writer.write_call("Math.divide", 2)
            else:
                self.vm_writer.write_arithmetic(ops[op])
    
    def compile_term(self):
        token_type = self.tokenizer.token_type()
        value = self.tokenizer.token_value()
        
        # integerConstant
        if token_type == TokenType.INT_CONST:
            self.vm_writer.write_push("constant", value)
            self.tokenizer.advance()
        
        # stringConstant
        elif token_type == TokenType.STRING_CONST:
            self.vm_writer.write_push("constant", len(value))
            self.vm_writer.write_call("String.new", 1)
            for char in value:
                self.vm_writer.write_push("constant", ord(char))
                self.vm_writer.write_call("String.appendChar", 2)
            self.tokenizer.advance()
        
        # keywordConstant
        elif value in ['true', 'false', 'null', 'this']:
            if value == 'true':
                self.vm_writer.write_push("constant", 0)
                self.vm_writer.write_arithmetic("not")
            elif value in ['false', 'null']:
                self.vm_writer.write_push("constant", 0)
            elif value == 'this':
                self.vm_writer.write_push("pointer", 0)
            self.tokenizer.advance()
        
        # (expression)
        elif value == '(':
            self.tokenizer.advance()
            self.compile_expression()
            self._expect(')')
        
        # unaryOp term
        elif value in ['-', '~']:
            op = value
            self.tokenizer.advance()
            self.compile_term()
            if op == '-':
                self.vm_writer.write_arithmetic("neg")
            else:
                self.vm_writer.write_arithmetic("not")
        
        # varName | varName[expression] | subroutineCall
        elif token_type == TokenType.IDENTIFIER:
            next_token = self.tokenizer.peek()
            
            # 陣列存取
            if next_token and next_token[1] == '[':
                var_name = value
                self.tokenizer.advance()
                self._expect('[')
                self.compile_expression()
                self._expect(']')
                self._push_variable(var_name)
                self.vm_writer.write_arithmetic("add")
                self.vm_writer.write_pop("pointer", 1)
                self.vm_writer.write_push("that", 0)
            
            # 子程序呼叫
            elif next_token and next_token[1] in ['.', '(']:
                self.compile_subroutine_call()
            
            # 變數
            else:
                self._push_variable(value)
                self.tokenizer.advance()
    
    def compile_subroutine_call(self):
        name = self.tokenizer.token_value()
        self.tokenizer.advance()
        
        n_args = 0
        
        # method call: object.method() 或 method()
        if self.tokenizer.token_value() == '.':
            self.tokenizer.advance()
            method_name = self.tokenizer.token_value()
            self.tokenizer.advance()
            
            # 檢查是否為變數（物件）
            if self.symbol_table.kind_of(name) is not None:
                self._push_variable(name)
                n_args = 1
                class_name = self.symbol_table.type_of(name)
                full_name = f"{class_name}.{method_name}"
            else:
                full_name = f"{name}.{method_name}"
        else:
            # 當前類別的 method
            self.vm_writer.write_push("pointer", 0)
            n_args = 1
            full_name = f"{self.class_name}.{name}"
        
        self._expect('(')
        n_args += self.compile_expression_list()
        self._expect(')')
        
        self.vm_writer.write_call(full_name, n_args)
    
    def compile_expression_list(self) -> int:
        n_args = 0
        
        if self.tokenizer.token_value() != ')':
            self.compile_expression()
            n_args = 1
            
            while self.tokenizer.token_value() == ',':
                self.tokenizer.advance()
                self.compile_expression()
                n_args += 1
        
        return n_args
    
    def _push_variable(self, name: str):
        kind = self.symbol_table.kind_of(name)
        index = self.symbol_table.index_of(name)
        
        segment_map = {
            SymbolKind.STATIC: "static",
            SymbolKind.FIELD: "this",
            SymbolKind.ARG: "argument",
            SymbolKind.VAR: "local"
        }
        
        self.vm_writer.write_push(segment_map[kind], index)
    
    def _pop_variable(self, name: str):
        kind = self.symbol_table.kind_of(name)
        index = self.symbol_table.index_of(name)
        
        segment_map = {
            SymbolKind.STATIC: "static",
            SymbolKind.FIELD: "this",
            SymbolKind.ARG: "argument",
            SymbolKind.VAR: "local"
        }
        
        self.vm_writer.write_pop(segment_map[kind], index)

# ============= Main Compiler =============

def compile_file(jack_file: str):
    """編譯單一 .jack 檔案"""
    with open(jack_file, 'r') as f:
        content = f.read()
    
    tokenizer = JackTokenizer(content)
    engine = CompilationEngine(tokenizer)
    engine.compile_class()
    
    vm_file = jack_file.replace('.jack', '.vm')
    with open(vm_file, 'w') as f:
        f.write(engine.vm_writer.get_output())
    
    print(f"Compiled: {jack_file} -> {vm_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py <file.jack | directory>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if os.path.isfile(path):
        if path.endswith('.jack'):
            compile_file(path)
        else:
            print("Error: File must have .jack extension")
    
    elif os.path.isdir(path):
        jack_files = [f for f in os.listdir(path) if f.endswith('.jack')]
        if not jack_files:
            print(f"No .jack files found in {path}")
            sys.exit(1)
        
        for jack_file in jack_files:
            compile_file(os.path.join(path, jack_file))
    
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)

if __name__ == '__main__':
    main()