import sys
import os
import re

# ==========================================
# 1. 基礎定義 (關鍵字與符號)
# ==========================================

KEYWORDS = {
    'class', 'constructor', 'function', 'method', 'field', 'static', 'var',
    'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this',
    'let', 'do', 'if', 'else', 'while', 'return'
}

SYMBOLS = {
    '{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&',
    '|', '<', '>', '=', '~'
}

XML_MAP = {
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    '&': '&amp;'
}

OPS = {'+', '-', '*', '/', '&', '|', '<', '>', '='}

# ==========================================
# 2. JackTokenizer (分詞器)
# ==========================================

class JackTokenizer:
    def __init__(self, input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.tokens = self._tokenize(content)
        self.current_token_idx = 0
        self.current_token = ""
        self.token_type = ""

    def _tokenize(self, content):
        # 移除區塊註釋
        content = re.sub(r'/\*.*?\*/', ' ', content, flags=re.S)
        # 移除單行註釋
        content = re.sub(r'//.*', ' ', content)
        
        # Regex 提取 Token
        regex = r'([a-zA-Z_]\w*)|(\d+)|("[^"\n]*")|([{}()\[\].,;+\-*/&|<>=~])'
        matches = re.findall(regex, content)
        
        tokens = []
        for match in matches:
            for group in match:
                if group:
                    tokens.append(group)
        return tokens

    def has_more_tokens(self):
        return self.current_token_idx < len(self.tokens)

    def advance(self):
        if self.has_more_tokens():
            self.current_token = self.tokens[self.current_token_idx]
            self.current_token_idx += 1
            self._set_token_type()

    def _set_token_type(self):
        token = self.current_token
        if token in KEYWORDS:
            self.token_type = 'KEYWORD'
        elif token in SYMBOLS:
            self.token_type = 'SYMBOL'
        elif token.isdigit():
            self.token_type = 'INT_CONST'
        elif token.startswith('"'):
            self.token_type = 'STRING_CONST'
        else:
            self.token_type = 'IDENTIFIER'

    def string_val(self): return self.current_token[1:-1]

    def peek(self):
        if self.has_more_tokens():
            return self.tokens[self.current_token_idx]
        return ""

# ==========================================
# 3. CompilationEngine (語法分析引擎)
# ==========================================

class CompilationEngine:
    def __init__(self, tokenizer, output_path):
        # 確保父目錄存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.outfile = open(output_path, 'w', encoding='utf-8')
        self.tokenizer = tokenizer
        self.indent_level = 0
        
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def close(self):
        self.outfile.close()

    def _write_tag(self, tag, value=None, is_terminal=False):
        indent = '  ' * self.indent_level
        if is_terminal:
            val_escaped = XML_MAP.get(value, value)
            self.outfile.write(f"{indent}<{tag}> {val_escaped} </{tag}>\n")
        else:
            if value == 'start':
                self.outfile.write(f"{indent}<{tag}>\n")
                self.indent_level += 1
            elif value == 'end':
                self.indent_level -= 1
                indent = '  ' * self.indent_level
                self.outfile.write(f"{indent}</{tag}>\n")

    def _process(self, expected_token=None):
        curr_token = self.tokenizer.current_token
        curr_type = self.tokenizer.token_type
        
        tag_map = {
            'KEYWORD': 'keyword',
            'SYMBOL': 'symbol',
            'IDENTIFIER': 'identifier',
            'INT_CONST': 'integerConstant',
            'STRING_CONST': 'stringConstant'
        }
        
        tag = tag_map.get(curr_type)
        if curr_type == 'STRING_CONST':
            value = self.tokenizer.string_val()
        else:
            value = curr_token

        self._write_tag(tag, value, is_terminal=True)
        self.tokenizer.advance()

    # --- Structure ---
    def compile_class(self):
        self._write_tag('class', 'start')
        self._process('class')
        self._process()
        self._process('{')
        while self.tokenizer.current_token in ['static', 'field']:
            self.compile_class_var_dec()
        while self.tokenizer.current_token in ['constructor', 'function', 'method']:
            self.compile_subroutine()
        self._process('}')
        self._write_tag('class', 'end')

    def compile_class_var_dec(self):
        self._write_tag('classVarDec', 'start')
        self._process() 
        self._process()
        self._process()
        while self.tokenizer.current_token == ',':
            self._process(',')
            self._process()
        self._process(';')
        self._write_tag('classVarDec', 'end')

    def compile_subroutine(self):
        self._write_tag('subroutineDec', 'start')
        self._process()
        self._process()
        self._process()
        self._process('(')
        self.compile_parameter_list()
        self._process(')')
        self.compile_subroutine_body()
        self._write_tag('subroutineDec', 'end')

    def compile_parameter_list(self):
        self._write_tag('parameterList', 'start')
        if self.tokenizer.current_token != ')':
            self._process()
            self._process()
            while self.tokenizer.current_token == ',':
                self._process(',')
                self._process()
                self._process()
        self._write_tag('parameterList', 'end')

    def compile_subroutine_body(self):
        self._write_tag('subroutineBody', 'start')
        self._process('{')
        while self.tokenizer.current_token == 'var':
            self.compile_var_dec()
        self.compile_statements()
        self._process('}')
        self._write_tag('subroutineBody', 'end')

    def compile_var_dec(self):
        self._write_tag('varDec', 'start')
        self._process('var')
        self._process()
        self._process()
        while self.tokenizer.current_token == ',':
            self._process(',')
            self._process()
        self._process(';')
        self._write_tag('varDec', 'end')

    # --- Statements ---
    def compile_statements(self):
        self._write_tag('statements', 'start')
        while self.tokenizer.current_token in ['let', 'if', 'while', 'do', 'return']:
            if self.tokenizer.current_token == 'let': self.compile_let()
            elif self.tokenizer.current_token == 'if': self.compile_if()
            elif self.tokenizer.current_token == 'while': self.compile_while()
            elif self.tokenizer.current_token == 'do': self.compile_do()
            elif self.tokenizer.current_token == 'return': self.compile_return()
        self._write_tag('statements', 'end')

    def compile_let(self):
        self._write_tag('letStatement', 'start')
        self._process('let')
        self._process()
        if self.tokenizer.current_token == '[':
            self._process('[')
            self.compile_expression()
            self._process(']')
        self._process('=')
        self.compile_expression()
        self._process(';')
        self._write_tag('letStatement', 'end')

    def compile_if(self):
        self._write_tag('ifStatement', 'start')
        self._process('if')
        self._process('(')
        self.compile_expression()
        self._process(')')
        self._process('{')
        self.compile_statements()
        self._process('}')
        if self.tokenizer.current_token == 'else':
            self._process('else')
            self._process('{')
            self.compile_statements()
            self._process('}')
        self._write_tag('ifStatement', 'end')

    def compile_while(self):
        self._write_tag('whileStatement', 'start')
        self._process('while')
        self._process('(')
        self.compile_expression()
        self._process(')')
        self._process('{')
        self.compile_statements()
        self._process('}')
        self._write_tag('whileStatement', 'end')

    def compile_do(self):
        self._write_tag('doStatement', 'start')
        self._process('do')
        self._process()
        if self.tokenizer.current_token == '.':
            self._process('.')
            self._process()
        self._process('(')
        self.compile_expression_list()
        self._process(')')
        self._process(';')
        self._write_tag('doStatement', 'end')

    def compile_return(self):
        self._write_tag('returnStatement', 'start')
        self._process('return')
        if self.tokenizer.current_token != ';':
            self.compile_expression()
        self._process(';')
        self._write_tag('returnStatement', 'end')

    # --- Expressions ---
    def compile_expression(self):
        self._write_tag('expression', 'start')
        self.compile_term()
        while self.tokenizer.current_token in OPS:
            self._process()
            self.compile_term()
        self._write_tag('expression', 'end')

    def compile_term(self):
        self._write_tag('term', 'start')
        token = self.tokenizer.current_token
        type = self.tokenizer.token_type
        
        if type in ['INT_CONST', 'STRING_CONST', 'KEYWORD']:
            self._process()
        elif type == 'IDENTIFIER':
            next_token = self.tokenizer.peek()
            if next_token == '[':
                self._process()
                self._process('[')
                self.compile_expression()
                self._process(']')
            elif next_token == '(' or next_token == '.':
                self._process()
                if self.tokenizer.current_token == '.':
                    self._process('.')
                    self._process()
                self._process('(')
                self.compile_expression_list()
                self._process(')')
            else:
                self._process()
        elif token == '(':
            self._process('(')
            self.compile_expression()
            self._process(')')
        elif token in ['-', '~']:
            self._process()
            self.compile_term()
        self._write_tag('term', 'end')

    def compile_expression_list(self):
        self._write_tag('expressionList', 'start')
        if self.tokenizer.current_token != ')':
            self.compile_expression()
            while self.tokenizer.current_token == ',':
                self._process(',')
                self.compile_expression()
        self._write_tag('expressionList', 'end')

# ==========================================
# 4. 主程式 (修改後：新增 output 資料夾邏輯)
# ==========================================

def analyze_file(input_file, output_dir):
    """
    input_file: 原始 .jack 檔案的完整路徑
    output_dir: 輸出的資料夾路徑
    """
    if not input_file.endswith('.jack'):
        return
    
    # 取得原始檔名 (例如 Main.jack)
    base_name = os.path.basename(input_file)
    # 替換副檔名 (例如 Main.xml)
    xml_name = base_name.replace('.jack', '.xml')
    # 組合完整的輸出路徑
    output_path = os.path.join(output_dir, xml_name)
    
    print(f"Compiling: {base_name} -> output/{xml_name}")
    
    tokenizer = JackTokenizer(input_file)
    engine = CompilationEngine(tokenizer, output_path)
    engine.compile_class()
    engine.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python JackAnalyzer.py [file.jack|dir]")
        return
    
    path = sys.argv[1]
    
    # 定義輸出資料夾名稱
    OUTPUT_FOLDER_NAME = "output"

    if os.path.isdir(path):
        # 如果輸入是目錄，在該目錄下建立 output 資料夾
        output_dir = os.path.join(path, OUTPUT_FOLDER_NAME)
        # exist_ok=True 表示如果資料夾已存在也不會報錯
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Processing directory: {path}")
        print(f"Output directory: {output_dir}\n")

        for filename in os.listdir(path):
            if filename.endswith(".jack"):
                full_input_path = os.path.join(path, filename)
                analyze_file(full_input_path, output_dir)
                
    elif os.path.isfile(path):
        # 如果輸入是檔案，在該檔案所在目錄下建立 output 資料夾
        dir_path = os.path.dirname(path)
        output_dir = os.path.join(dir_path, OUTPUT_FOLDER_NAME)
        os.makedirs(output_dir, exist_ok=True)
        
        analyze_file(path, output_dir)
    else:
        print("Invalid file or directory")

if __name__ == "__main__":
    main()