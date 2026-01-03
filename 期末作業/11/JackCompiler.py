import sys
import os
import re

# ==========================================
# 1. 基礎定義
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

# 運算子對應到 VM 的指令或 OS 呼叫
OP_MAP = {
    '+': 'add', '-': 'sub', '*': 'call Math.multiply 2', '/': 'call Math.divide 2',
    '&': 'and', '|': 'or', '<': 'lt', '>': 'gt', '=': 'eq'
}

# Unary 運算子
UNARY_OP_MAP = {
    '-': 'neg', '~': 'not'
}

# Kind 到 Segment 的映射
KIND_TO_SEGMENT = {
    'STATIC': 'static',
    'FIELD': 'this',
    'ARG': 'argument',
    'VAR': 'local'
}

# ==========================================
# 2. JackTokenizer (與 Ch10 相同)
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
        content = re.sub(r'/\*.*?\*/', ' ', content, flags=re.S)
        content = re.sub(r'//.*', ' ', content)
        regex = r'([a-zA-Z_]\w*)|(\d+)|("[^"\n]*")|([{}()\[\].,;+\-*/&|<>=~])'
        matches = re.findall(regex, content)
        tokens = []
        for match in matches:
            for group in match:
                if group: tokens.append(group)
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
        if token in KEYWORDS: self.token_type = 'KEYWORD'
        elif token in SYMBOLS: self.token_type = 'SYMBOL'
        elif token.isdigit(): self.token_type = 'INT_CONST'
        elif token.startswith('"'): self.token_type = 'STRING_CONST'
        else: self.token_type = 'IDENTIFIER'

    def string_val(self): return self.current_token[1:-1]
    def peek(self):
        if self.has_more_tokens(): return self.tokens[self.current_token_idx]
        return ""

# ==========================================
# 3. SymbolTable (符號表 - Ch11 新增)
# ==========================================

class SymbolTable:
    def __init__(self):
        self.class_scope = {}      # {name: (type, kind, index)}
        self.subroutine_scope = {} # {name: (type, kind, index)}
        self.counts = {'STATIC': 0, 'FIELD': 0, 'ARG': 0, 'VAR': 0}

    def start_subroutine(self):
        self.subroutine_scope = {}
        self.counts['ARG'] = 0
        self.counts['VAR'] = 0

    def define(self, name, type, kind):
        # kind: STATIC, FIELD, ARG, VAR
        index = self.counts[kind]
        record = (type, kind, index)
        
        if kind in ['STATIC', 'FIELD']:
            self.class_scope[name] = record
        else:
            self.subroutine_scope[name] = record
            
        self.counts[kind] += 1

    def var_count(self, kind):
        return self.counts[kind]

    def kind_of(self, name):
        if name in self.subroutine_scope: return self.subroutine_scope[name][1]
        if name in self.class_scope: return self.class_scope[name][1]
        return None

    def type_of(self, name):
        if name in self.subroutine_scope: return self.subroutine_scope[name][0]
        if name in self.class_scope: return self.class_scope[name][0]
        return None

    def index_of(self, name):
        if name in self.subroutine_scope: return self.subroutine_scope[name][2]
        if name in self.class_scope: return self.class_scope[name][2]
        return None

# ==========================================
# 4. VMWriter (VM 輸出器 - Ch11 新增)
# ==========================================

class VMWriter:
    def __init__(self, output_file):
        self.outfile = open(output_file, 'w', encoding='utf-8')

    def close(self):
        self.outfile.close()

    def write_push(self, segment, index):
        self.outfile.write(f"push {segment} {index}\n")

    def write_pop(self, segment, index):
        self.outfile.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command):
        self.outfile.write(f"{command}\n")

    def write_label(self, label):
        self.outfile.write(f"label {label}\n")

    def write_goto(self, label):
        self.outfile.write(f"goto {label}\n")

    def write_if(self, label):
        self.outfile.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        self.outfile.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_locals):
        self.outfile.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.outfile.write("return\n")

# ==========================================
# 5. CompilationEngine (核心邏輯 - Ch11 修改)
# ==========================================

class CompilationEngine:
    def __init__(self, tokenizer, output_path):
        self.tokenizer = tokenizer
        self.vm_writer = VMWriter(output_path)
        self.symbol_table = SymbolTable()
        self.class_name = ""
        self.label_counter = 0
        
        if self.tokenizer.has_more_tokens():
            self.tokenizer.advance()

    def close(self):
        self.vm_writer.close()

    def _eat(self, token=None):
        # 簡單的推進，如果有傳入 token 可以做檢查 (此處省略嚴格檢查)
        val = self.tokenizer.current_token
        self.tokenizer.advance()
        return val

    def _new_label(self):
        self.label_counter += 1
        return f"L{self.label_counter}"

    # --- Structure ---

    def compile_class(self):
        self._eat('class')
        self.class_name = self._eat() # ClassName
        self._eat('{')
        
        while self.tokenizer.current_token in ['static', 'field']:
            self.compile_class_var_dec()
            
        while self.tokenizer.current_token in ['constructor', 'function', 'method']:
            self.compile_subroutine()
            
        self._eat('}')

    def compile_class_var_dec(self):
        kind_str = self._eat() # static / field
        kind = kind_str.upper()
        type = self._eat()     # int / char / ...
        name = self._eat()     # varName
        self.symbol_table.define(name, type, kind)
        
        while self.tokenizer.current_token == ',':
            self._eat(',')
            name = self._eat()
            self.symbol_table.define(name, type, kind)
        self._eat(';')

    def compile_subroutine(self):
        self.symbol_table.start_subroutine()
        
        sub_type = self._eat() # constructor / function / method
        return_type = self._eat()
        sub_name = self._eat()
        
        # Method 的第一個隱藏參數是 this
        if sub_type == 'method':
            self.symbol_table.define('this', self.class_name, 'ARG')
            
        self._eat('(')
        self.compile_parameter_list()
        self._eat(')')
        
        # Subroutine Body
        self._eat('{')
        while self.tokenizer.current_token == 'var':
            self.compile_var_dec()
            
        # 寫入 function 定義: function Class.Name nLocals
        full_name = f"{self.class_name}.{sub_name}"
        n_locals = self.symbol_table.var_count('VAR')
        self.vm_writer.write_function(full_name, n_locals)
        
        # 特殊處理: Constructor 需要 alloc, Method 需要設定 this
        if sub_type == 'constructor':
            field_count = self.symbol_table.var_count('FIELD')
            self.vm_writer.write_push('constant', field_count)
            self.vm_writer.write_call('Memory.alloc', 1)
            self.vm_writer.write_pop('pointer', 0) # this = alloc()
        elif sub_type == 'method':
            self.vm_writer.write_push('argument', 0)
            self.vm_writer.write_pop('pointer', 0) # this = arg0
            
        self.compile_statements()
        self._eat('}')

    def compile_parameter_list(self):
        if self.tokenizer.current_token != ')':
            type = self._eat()
            name = self._eat()
            self.symbol_table.define(name, type, 'ARG')
            while self.tokenizer.current_token == ',':
                self._eat(',')
                type = self._eat()
                name = self._eat()
                self.symbol_table.define(name, type, 'ARG')

    def compile_var_dec(self):
        self._eat('var')
        type = self._eat()
        name = self._eat()
        self.symbol_table.define(name, type, 'VAR')
        while self.tokenizer.current_token == ',':
            self._eat(',')
            name = self._eat()
            self.symbol_table.define(name, type, 'VAR')
        self._eat(';')

    # --- Statements ---

    def compile_statements(self):
        while self.tokenizer.current_token in ['let', 'if', 'while', 'do', 'return']:
            if self.tokenizer.current_token == 'let': self.compile_let()
            elif self.tokenizer.current_token == 'if': self.compile_if()
            elif self.tokenizer.current_token == 'while': self.compile_while()
            elif self.tokenizer.current_token == 'do': self.compile_do()
            elif self.tokenizer.current_token == 'return': self.compile_return()

    def compile_let(self):
        self._eat('let')
        var_name = self._eat()
        is_array = False
        
        # 處理陣列賦值: let a[i] = x
        if self.tokenizer.current_token == '[':
            is_array = True
            # Push array base address
            kind = self.symbol_table.kind_of(var_name)
            index = self.symbol_table.index_of(var_name)
            self.vm_writer.write_push(KIND_TO_SEGMENT[kind], index)
            
            self._eat('[')
            self.compile_expression() # 計算 index
            self._eat(']')
            
            self.vm_writer.write_arithmetic('add') # base + index
            
        self._eat('=')
        self.compile_expression() # 計算 RHS
        self._eat(';')
        
        if is_array:
            self.vm_writer.write_pop('temp', 0)    # 暫存 RHS 結果
            self.vm_writer.write_pop('pointer', 1) # 設定 that 到目標位址
            self.vm_writer.write_push('temp', 0)   # 取回 RHS
            self.vm_writer.write_pop('that', 0)    # 寫入
        else:
            # 一般變數賦值
            kind = self.symbol_table.kind_of(var_name)
            index = self.symbol_table.index_of(var_name)
            if kind:
                self.vm_writer.write_pop(KIND_TO_SEGMENT[kind], index)

    def compile_if(self):
        l1 = self._new_label()
        l2 = self._new_label()
        
        self._eat('if')
        self._eat('(')
        self.compile_expression()
        self._eat(')')
        
        self.vm_writer.write_arithmetic('not')
        self.vm_writer.write_if(l1) # 如果條件不成立，跳到 L1 (else/end)
        
        self._eat('{')
        self.compile_statements()
        self._eat('}')
        
        self.vm_writer.write_goto(l2) # 跳過 else 區塊
        
        self.vm_writer.write_label(l1)
        if self.tokenizer.current_token == 'else':
            self._eat('else')
            self._eat('{')
            self.compile_statements()
            self._eat('}')
            
        self.vm_writer.write_label(l2)

    def compile_while(self):
        l1 = self._new_label()
        l2 = self._new_label()
        
        self.vm_writer.write_label(l1)
        
        self._eat('while')
        self._eat('(')
        self.compile_expression()
        self._eat(')')
        
        self.vm_writer.write_arithmetic('not')
        self.vm_writer.write_if(l2) # 條件假，跳出迴圈
        
        self._eat('{')
        self.compile_statements()
        self._eat('}')
        
        self.vm_writer.write_goto(l1)
        self.vm_writer.write_label(l2)

    def compile_do(self):
        self._eat('do')
        # Do 語句其實就是一個表達式呼叫，但我們會丟棄回傳值
        self.compile_term() # 這會處理函數呼叫邏輯
        self._eat(';')
        self.vm_writer.write_pop('temp', 0) # 丟棄 void 函數預設回傳的 0

    def compile_return(self):
        self._eat('return')
        if self.tokenizer.current_token != ';':
            self.compile_expression()
        else:
            self.vm_writer.write_push('constant', 0) # void return 0
        self._eat(';')
        self.vm_writer.write_return()

    # --- Expressions ---

    def compile_expression(self):
        self.compile_term()
        while self.tokenizer.current_token in OP_MAP:
            op = self._eat()
            self.compile_term()
            # 輸出運算指令 (Postfix)
            if op in OP_MAP:
                cmd = OP_MAP[op]
                if cmd.startswith('call'):
                    # 處理 Math.multiply / Math.divide
                    parts = cmd.split()
                    self.vm_writer.write_call(parts[1], int(parts[2]))
                else:
                    self.vm_writer.write_arithmetic(cmd)

    def compile_term(self):
        token = self.tokenizer.current_token
        type = self.tokenizer.token_type
        
        if type == 'INT_CONST':
            val = self._eat()
            self.vm_writer.write_push('constant', val)
            
        elif type == 'STRING_CONST':
            s = self.tokenizer.string_val()
            self._eat()
            self.vm_writer.write_push('constant', len(s))
            self.vm_writer.write_call('String.new', 1)
            for char in s:
                self.vm_writer.write_push('constant', ord(char))
                self.vm_writer.write_call('String.appendChar', 2)
                
        elif type == 'KEYWORD':
            val = self._eat()
            if val == 'true':
                self.vm_writer.write_push('constant', 1) # 1
                self.vm_writer.write_arithmetic('neg')   # -1
            elif val in ['false', 'null']:
                self.vm_writer.write_push('constant', 0)
            elif val == 'this':
                self.vm_writer.write_push('pointer', 0)
                
        elif type == 'IDENTIFIER':
            # 需要 Lookahead 來判斷是 變數 / 陣列 / 函數呼叫
            name = self._eat()
            next_token = self.tokenizer.current_token
            
            if next_token == '[': # Array: a[i]
                self._eat('[')
                
                # Push array base
                kind = self.symbol_table.kind_of(name)
                idx = self.symbol_table.index_of(name)
                self.vm_writer.write_push(KIND_TO_SEGMENT[kind], idx)
                
                self.compile_expression() # index
                self._eat(']')
                
                self.vm_writer.write_arithmetic('add')
                self.vm_writer.write_pop('pointer', 1) # that = arr + i
                self.vm_writer.write_push('that', 0)
                
            elif next_token == '(' or next_token == '.': # Function Call
                self._compile_subroutine_call(name)
                
            else: # Simple Variable
                kind = self.symbol_table.kind_of(name)
                idx = self.symbol_table.index_of(name)
                if kind:
                    self.vm_writer.write_push(KIND_TO_SEGMENT[kind], idx)
                    
        elif token == '(':
            self._eat('(')
            self.compile_expression()
            self._eat(')')
            
        elif token in UNARY_OP_MAP:
            op = self._eat()
            self.compile_term()
            self.vm_writer.write_arithmetic(UNARY_OP_MAP[op])

    def _compile_subroutine_call(self, first_name):
        # 這裡處理 foo() 或 Class.foo() 或 var.method()
        n_args = 0
        full_func_name = ""
        
        if self.tokenizer.current_token == '.':
            self._eat('.')
            sub_name = self._eat()
            
            # 檢查 first_name 是 類別名 還是 變數名
            kind = self.symbol_table.kind_of(first_name)
            if kind: 
                # 是變數 (e.g., ball.move()) -> Method Call
                # Push 'this' (the object)
                idx = self.symbol_table.index_of(first_name)
                self.vm_writer.write_push(KIND_TO_SEGMENT[kind], idx)
                
                # 取得變數的型別 (Class Name)
                class_type = self.symbol_table.type_of(first_name)
                full_func_name = f"{class_type}.{sub_name}"
                n_args = 1 # 已經 push 了一個 this
            else:
                # 是類別 (e.g., Math.abs()) -> Function Call
                full_func_name = f"{first_name}.{sub_name}"
        else:
            # 隱式 Method Call (e.g., draw()) -> this.draw()
            self.vm_writer.write_push('pointer', 0) # push this
            full_func_name = f"{self.class_name}.{first_name}"
            n_args = 1
            
        self._eat('(')
        n_args += self.compile_expression_list()
        self._eat(')')
        
        self.vm_writer.write_call(full_func_name, n_args)

    def compile_expression_list(self):
        count = 0
        if self.tokenizer.current_token != ')':
            self.compile_expression()
            count += 1
            while self.tokenizer.current_token == ',':
                self._eat(',')
                self.compile_expression()
                count += 1
        return count

# ==========================================
# 6. 主程式
# ==========================================

def analyze_file(input_file, output_dir):
    if not input_file.endswith('.jack'): return
    
    base_name = os.path.basename(input_file)
    vm_name = base_name.replace('.jack', '.vm')
    output_path = os.path.join(output_dir, vm_name)
    
    print(f"Compiling: {base_name} -> output/{vm_name}")
    
    tokenizer = JackTokenizer(input_file)
    engine = CompilationEngine(tokenizer, output_path)
    engine.compile_class()
    engine.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python JackCompiler.py [file.jack|dir]")
        return
    
    path = sys.argv[1]
    OUTPUT_FOLDER_NAME = "output"

    if os.path.isdir(path):
        output_dir = os.path.join(path, OUTPUT_FOLDER_NAME)
        os.makedirs(output_dir, exist_ok=True)
        print(f"Processing directory: {path}")
        print(f"Output directory: {output_dir}\n")

        for filename in os.listdir(path):
            if filename.endswith(".jack"):
                analyze_file(os.path.join(path, filename), output_dir)
                
    elif os.path.isfile(path):
        dir_path = os.path.dirname(path)
        output_dir = os.path.join(dir_path, OUTPUT_FOLDER_NAME)
        os.makedirs(output_dir, exist_ok=True)
        analyze_file(path, output_dir)
    else:
        print("Invalid file or directory")

if __name__ == "__main__":
    main()