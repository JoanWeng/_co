import os
import sys

class Parser:
    """解析 VM 指令"""
    
    C_ARITHMETIC = 0
    C_PUSH = 1
    C_POP = 2
    C_LABEL = 3
    C_GOTO = 4
    C_IF = 5
    C_FUNCTION = 6
    C_RETURN = 7
    C_CALL = 8
    
    def __init__(self, input_file):
        with open(input_file, 'r') as f:
            self.lines = f.readlines()
        self.current_command = ""
        self.current_line = -1
        
    def has_more_commands(self):
        return self.current_line < len(self.lines) - 1
    
    def advance(self):
        self.current_line += 1
        line = self.lines[self.current_line].strip()
        # 移除註解
        if '//' in line:
            line = line[:line.index('//')].strip()
        self.current_command = line
        
        # 跳過空行和註解
        while self.current_command == '' and self.has_more_commands():
            self.current_line += 1
            line = self.lines[self.current_line].strip()
            if '//' in line:
                line = line[:line.index('//')].strip()
            self.current_command = line
    
    def command_type(self):
        if not self.current_command:
            return None
        
        parts = self.current_command.split()
        cmd = parts[0]
        
        arithmetic_cmds = ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']
        
        if cmd in arithmetic_cmds:
            return self.C_ARITHMETIC
        elif cmd == 'push':
            return self.C_PUSH
        elif cmd == 'pop':
            return self.C_POP
        elif cmd == 'label':
            return self.C_LABEL
        elif cmd == 'goto':
            return self.C_GOTO
        elif cmd == 'if-goto':
            return self.C_IF
        elif cmd == 'function':
            return self.C_FUNCTION
        elif cmd == 'call':
            return self.C_CALL
        elif cmd == 'return':
            return self.C_RETURN
    
    def arg1(self):
        parts = self.current_command.split()
        if self.command_type() == self.C_ARITHMETIC:
            return parts[0]
        return parts[1]
    
    def arg2(self):
        parts = self.current_command.split()
        return int(parts[2])


class CodeWriter:
    """生成組合語言代碼"""
    
    def __init__(self, output_file):
        self.output = open(output_file, 'w')
        self.current_file = ""
        self.label_counter = 0
        self.current_function = ""
        self.call_counter = 0
        
    def set_file_name(self, file_name):
        self.current_file = os.path.splitext(os.path.basename(file_name))[0]
    
    def write_init(self):
        """寫入啟動代碼"""
        self.output.write("// Bootstrap code\n")
        self.output.write("@256\n")
        self.output.write("D=A\n")
        self.output.write("@SP\n")
        self.output.write("M=D\n")
        self.write_call("Sys.init", 0)
    
    def write_arithmetic(self, command):
        self.output.write(f"// {command}\n")
        
        if command in ['add', 'sub', 'and', 'or']:
            self.output.write("@SP\n")
            self.output.write("AM=M-1\n")
            self.output.write("D=M\n")
            self.output.write("A=A-1\n")
            
            if command == 'add':
                self.output.write("M=D+M\n")
            elif command == 'sub':
                self.output.write("M=M-D\n")
            elif command == 'and':
                self.output.write("M=D&M\n")
            elif command == 'or':
                self.output.write("M=D|M\n")
                
        elif command in ['neg', 'not']:
            self.output.write("@SP\n")
            self.output.write("A=M-1\n")
            
            if command == 'neg':
                self.output.write("M=-M\n")
            elif command == 'not':
                self.output.write("M=!M\n")
                
        elif command in ['eq', 'gt', 'lt']:
            label1 = f"LABEL_{self.label_counter}"
            label2 = f"LABEL_{self.label_counter + 1}"
            self.label_counter += 2
            
            self.output.write("@SP\n")
            self.output.write("AM=M-1\n")
            self.output.write("D=M\n")
            self.output.write("A=A-1\n")
            self.output.write("D=M-D\n")
            self.output.write(f"@{label1}\n")
            
            if command == 'eq':
                self.output.write("D;JEQ\n")
            elif command == 'gt':
                self.output.write("D;JGT\n")
            elif command == 'lt':
                self.output.write("D;JLT\n")
            
            self.output.write("@SP\n")
            self.output.write("A=M-1\n")
            self.output.write("M=0\n")
            self.output.write(f"@{label2}\n")
            self.output.write("0;JMP\n")
            self.output.write(f"({label1})\n")
            self.output.write("@SP\n")
            self.output.write("A=M-1\n")
            self.output.write("M=-1\n")
            self.output.write(f"({label2})\n")
    
    def write_push_pop(self, command, segment, index):
        self.output.write(f"// {command} {segment} {index}\n")
        
        if command == 'push':
            if segment == 'constant':
                self.output.write(f"@{index}\n")
                self.output.write("D=A\n")
            elif segment in ['local', 'argument', 'this', 'that']:
                seg_map = {'local': 'LCL', 'argument': 'ARG', 'this': 'THIS', 'that': 'THAT'}
                self.output.write(f"@{index}\n")
                self.output.write("D=A\n")
                self.output.write(f"@{seg_map[segment]}\n")
                self.output.write("A=D+M\n")
                self.output.write("D=M\n")
            elif segment == 'temp':
                self.output.write(f"@{5 + index}\n")
                self.output.write("D=M\n")
            elif segment == 'pointer':
                addr = 'THIS' if index == 0 else 'THAT'
                self.output.write(f"@{addr}\n")
                self.output.write("D=M\n")
            elif segment == 'static':
                self.output.write(f"@{self.current_file}.{index}\n")
                self.output.write("D=M\n")
            
            # Push D onto stack
            self.output.write("@SP\n")
            self.output.write("A=M\n")
            self.output.write("M=D\n")
            self.output.write("@SP\n")
            self.output.write("M=M+1\n")
            
        elif command == 'pop':
            if segment in ['local', 'argument', 'this', 'that']:
                seg_map = {'local': 'LCL', 'argument': 'ARG', 'this': 'THIS', 'that': 'THAT'}
                self.output.write(f"@{index}\n")
                self.output.write("D=A\n")
                self.output.write(f"@{seg_map[segment]}\n")
                self.output.write("D=D+M\n")
                self.output.write("@R13\n")
                self.output.write("M=D\n")
                self.output.write("@SP\n")
                self.output.write("AM=M-1\n")
                self.output.write("D=M\n")
                self.output.write("@R13\n")
                self.output.write("A=M\n")
                self.output.write("M=D\n")
            elif segment == 'temp':
                self.output.write("@SP\n")
                self.output.write("AM=M-1\n")
                self.output.write("D=M\n")
                self.output.write(f"@{5 + index}\n")
                self.output.write("M=D\n")
            elif segment == 'pointer':
                addr = 'THIS' if index == 0 else 'THAT'
                self.output.write("@SP\n")
                self.output.write("AM=M-1\n")
                self.output.write("D=M\n")
                self.output.write(f"@{addr}\n")
                self.output.write("M=D\n")
            elif segment == 'static':
                self.output.write("@SP\n")
                self.output.write("AM=M-1\n")
                self.output.write("D=M\n")
                self.output.write(f"@{self.current_file}.{index}\n")
                self.output.write("M=D\n")
    
    def write_label(self, label):
        self.output.write(f"// label {label}\n")
        self.output.write(f"({self.current_function}${label})\n")
    
    def write_goto(self, label):
        self.output.write(f"// goto {label}\n")
        self.output.write(f"@{self.current_function}${label}\n")
        self.output.write("0;JMP\n")
    
    def write_if(self, label):
        self.output.write(f"// if-goto {label}\n")
        self.output.write("@SP\n")
        self.output.write("AM=M-1\n")
        self.output.write("D=M\n")
        self.output.write(f"@{self.current_function}${label}\n")
        self.output.write("D;JNE\n")
    
    def write_function(self, function_name, num_locals):
        self.output.write(f"// function {function_name} {num_locals}\n")
        self.current_function = function_name
        self.output.write(f"({function_name})\n")
        
        for i in range(num_locals):
            self.output.write("@SP\n")
            self.output.write("A=M\n")
            self.output.write("M=0\n")
            self.output.write("@SP\n")
            self.output.write("M=M+1\n")
    
    def write_call(self, function_name, num_args):
        return_label = f"{function_name}$ret.{self.call_counter}"
        self.call_counter += 1
        
        self.output.write(f"// call {function_name} {num_args}\n")
        
        # Push return address
        self.output.write(f"@{return_label}\n")
        self.output.write("D=A\n")
        self.output.write("@SP\n")
        self.output.write("A=M\n")
        self.output.write("M=D\n")
        self.output.write("@SP\n")
        self.output.write("M=M+1\n")
        
        # Push LCL, ARG, THIS, THAT
        for segment in ['LCL', 'ARG', 'THIS', 'THAT']:
            self.output.write(f"@{segment}\n")
            self.output.write("D=M\n")
            self.output.write("@SP\n")
            self.output.write("A=M\n")
            self.output.write("M=D\n")
            self.output.write("@SP\n")
            self.output.write("M=M+1\n")
        
        # ARG = SP - 5 - num_args
        self.output.write("@SP\n")
        self.output.write("D=M\n")
        self.output.write(f"@{5 + num_args}\n")
        self.output.write("D=D-A\n")
        self.output.write("@ARG\n")
        self.output.write("M=D\n")
        
        # LCL = SP
        self.output.write("@SP\n")
        self.output.write("D=M\n")
        self.output.write("@LCL\n")
        self.output.write("M=D\n")
        
        # goto function_name
        self.output.write(f"@{function_name}\n")
        self.output.write("0;JMP\n")
        
        # (return_label)
        self.output.write(f"({return_label})\n")
    
    def write_return(self):
        self.output.write("// return\n")
        
        # FRAME = LCL
        self.output.write("@LCL\n")
        self.output.write("D=M\n")
        self.output.write("@R13\n")  # FRAME
        self.output.write("M=D\n")
        
        # RET = *(FRAME - 5)
        self.output.write("@5\n")
        self.output.write("A=D-A\n")
        self.output.write("D=M\n")
        self.output.write("@R14\n")  # RET
        self.output.write("M=D\n")
        
        # *ARG = pop()
        self.output.write("@SP\n")
        self.output.write("AM=M-1\n")
        self.output.write("D=M\n")
        self.output.write("@ARG\n")
        self.output.write("A=M\n")
        self.output.write("M=D\n")
        
        # SP = ARG + 1
        self.output.write("@ARG\n")
        self.output.write("D=M+1\n")
        self.output.write("@SP\n")
        self.output.write("M=D\n")
        
        # Restore THAT, THIS, ARG, LCL
        for segment, offset in [('THAT', 1), ('THIS', 2), ('ARG', 3), ('LCL', 4)]:
            self.output.write("@R13\n")
            self.output.write("D=M\n")
            self.output.write(f"@{offset}\n")
            self.output.write("A=D-A\n")
            self.output.write("D=M\n")
            self.output.write(f"@{segment}\n")
            self.output.write("M=D\n")
        
        # goto RET
        self.output.write("@R14\n")
        self.output.write("A=M\n")
        self.output.write("0;JMP\n")
    
    def close(self):
        self.output.close()


def translate_file(input_file, code_writer):
    parser = Parser(input_file)
    code_writer.set_file_name(input_file)
    
    while parser.has_more_commands():
        parser.advance()
        cmd_type = parser.command_type()
        
        if cmd_type == Parser.C_ARITHMETIC:
            code_writer.write_arithmetic(parser.arg1())
        elif cmd_type in [Parser.C_PUSH, Parser.C_POP]:
            command = 'push' if cmd_type == Parser.C_PUSH else 'pop'
            code_writer.write_push_pop(command, parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_LABEL:
            code_writer.write_label(parser.arg1())
        elif cmd_type == Parser.C_GOTO:
            code_writer.write_goto(parser.arg1())
        elif cmd_type == Parser.C_IF:
            code_writer.write_if(parser.arg1())
        elif cmd_type == Parser.C_FUNCTION:
            code_writer.write_function(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_CALL:
            code_writer.write_call(parser.arg1(), parser.arg2())
        elif cmd_type == Parser.C_RETURN:
            code_writer.write_return()


def main():
    if len(sys.argv) != 2:
        print("Usage: python VMTranslator.py <input.vm or directory>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if os.path.isfile(input_path):
        # 單一檔案
        output_file = input_path.replace('.vm', '.asm')
        code_writer = CodeWriter(output_file)
        translate_file(input_path, code_writer)
        code_writer.close()
    elif os.path.isdir(input_path):
        # 目錄
        output_file = os.path.join(input_path, os.path.basename(input_path) + '.asm')
        code_writer = CodeWriter(output_file)
        code_writer.write_init()
        
        vm_files = [f for f in os.listdir(input_path) if f.endswith('.vm')]
        for vm_file in sorted(vm_files):
            translate_file(os.path.join(input_path, vm_file), code_writer)
        
        code_writer.close()
    else:
        print("Error: Invalid input path")
        sys.exit(1)
    
    print(f"Translation completed: {output_file}")


if __name__ == '__main__':
    main()