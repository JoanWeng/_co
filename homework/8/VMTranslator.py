import sys
import os
import glob

# 定義指令類型常數
C_ARITHMETIC = 0
C_PUSH = 1
C_POP = 2
C_LABEL = 3
C_GOTO = 4
C_IF = 5
C_FUNCTION = 6
C_RETURN = 7
C_CALL = 8

class Parser:
    """
    負責讀取 .vm 檔案，移除空白與註解，並解析指令。
    """
    def __init__(self, input_file):
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        self.commands = []
        for line in lines:
            # 移除註解 // 和前後空白
            line = line.split('//')[0].strip()
            if line:
                self.commands.append(line)
        
        self.current_command = None
        self.current_index = -1

    def hasMoreCommands(self):
        return self.current_index < len(self.commands) - 1

    def advance(self):
        self.current_index += 1
        self.current_command = self.commands[self.current_index]

    def commandType(self):
        parts = self.current_command.split()
        cmd = parts[0]
        
        if cmd == 'return':
            return C_RETURN
        if cmd in ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']:
            return C_ARITHMETIC
        if cmd == 'push':
            return C_PUSH
        if cmd == 'pop':
            return C_POP
        if cmd == 'label':
            return C_LABEL
        if cmd == 'goto':
            return C_GOTO
        if cmd == 'if-goto':
            return C_IF
        if cmd == 'function':
            return C_FUNCTION
        if cmd == 'call':
            return C_CALL
        raise ValueError(f"Unknown command: {cmd}")

    def arg1(self):
        ctype = self.commandType()
        parts = self.current_command.split()
        if ctype == C_ARITHMETIC:
            return parts[0]
        return parts[1]

    def arg2(self):
        parts = self.current_command.split()
        return int(parts[2])

class CodeWriter:
    """
    負責將解析後的 VM 指令寫入為 Hack Assembly (.asm)。
    """
    def __init__(self, output_file):
        self.file = open(output_file, 'w')
        self.file_name = ""
        self.label_count = 0 # 用於生成唯一的跳轉標籤 (如 EQ, GT, LT)
        self.call_count = 0  # 用於生成唯一的返回地址標籤

    def setFileName(self, file_name):
        # 設定當前正在處理的 vm 檔名 (用於 static 變數)
        self.file_name = os.path.basename(file_name).replace('.vm', '')

    def writeInit(self):
        """
        Chapter 8: Bootstrap code
        初始化 SP=256，並呼叫 Sys.init
        """
        self.file.write("// Bootstrap code\n")
        self.file.write("@256\n")
        self.file.write("D=A\n")
        self.file.write("@SP\n")
        self.file.write("M=D\n")
        self.writeCall("Sys.init", 0)

    def writeLabel(self, label):
        # 格式: (FunctionName$LabelName)
        # 但在 SimpleFunction 這種測試中，標籤通常是局部的
        self.file.write(f"({label})\n")

    def writeGoto(self, label):
        self.file.write(f"@{label}\n")
        self.file.write("0;JMP\n")

    def writeIf(self, label):
        # Pop stack to D, if D != 0 jump
        self.file.write("@SP\nAM=M-1\nD=M\n")
        self.file.write(f"@{label}\n")
        self.file.write("D;JNE\n")

    def writeFunction(self, function_name, num_locals):
        self.file.write(f"// function {function_name} {num_locals}\n")
        self.file.write(f"({function_name})\n")
        # 初始化區域變數 (push 0 num_locals 次)
        for _ in range(num_locals):
            self.file.write("@SP\nA=M\nM=0\n@SP\nM=M+1\n")

    def writeReturn(self):
        self.file.write("// return\n")
        # FRAME = LCL (使用 R13 暫存 FRAME)
        self.file.write("@LCL\nD=M\n@R13\nM=D\n")
        
        # RET = *(FRAME - 5) (使用 R14 暫存 RET)
        self.file.write("@5\nA=D-A\nD=M\n@R14\nM=D\n")
        
        # *ARG = pop() -> 將回傳值放到呼叫者的堆疊頂端
        self.file.write("@SP\nAM=M-1\nD=M\n@ARG\nA=M\nM=D\n")
        
        # SP = ARG + 1 -> 恢復 SP
        self.file.write("@ARG\nD=M+1\n@SP\nM=D\n")
        
        # 恢復 THAT, THIS, ARG, LCL
        # THAT = *(FRAME - 1)
        self.file.write("@R13\nAM=M-1\nD=M\n@THAT\nM=D\n")
        # THIS = *(FRAME - 2)
        self.file.write("@R13\nAM=M-1\nD=M\n@THIS\nM=D\n")
        # ARG = *(FRAME - 3)
        self.file.write("@R13\nAM=M-1\nD=M\n@ARG\nM=D\n")
        # LCL = *(FRAME - 4)
        self.file.write("@R13\nAM=M-1\nD=M\n@LCL\nM=D\n")
        
        # goto RET
        self.file.write("@R14\nA=M\n0;JMP\n")

    def writeCall(self, function_name, num_args):
        return_label = f"{function_name}$ret.{self.call_count}"
        self.call_count += 1
        
        self.file.write(f"// call {function_name} {num_args}\n")
        
        # push return-address
        self.file.write(f"@{return_label}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
        
        # push LCL, ARG, THIS, THAT
        for segment in ['LCL', 'ARG', 'THIS', 'THAT']:
            self.file.write(f"@{segment}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            
        # ARG = SP - n - 5
        self.file.write(f"@SP\nD=M\n@5\nD=D-A\n@{num_args}\nD=D-A\n@ARG\nM=D\n")
        
        # LCL = SP
        self.file.write("@SP\nD=M\n@LCL\nM=D\n")
        
        # goto f
        self.file.write(f"@{function_name}\n0;JMP\n")
        
        # (return-address)
        self.file.write(f"({return_label})\n")

    def writeArithmetic(self, command):
        self.file.write(f"// {command}\n")
        if command in ['add', 'sub', 'and', 'or']:
            self.file.write("@SP\nAM=M-1\nD=M\nA=A-1\n")
            if command == 'add': self.file.write("M=D+M\n")
            elif command == 'sub': self.file.write("M=M-D\n")
            elif command == 'and': self.file.write("M=D&M\n")
            elif command == 'or':  self.file.write("M=D|M\n")
            
        elif command in ['neg', 'not']:
            self.file.write("@SP\nA=M-1\n")
            if command == 'neg': self.file.write("M=-M\n")
            elif command == 'not': self.file.write("M=!M\n")
            
        elif command in ['eq', 'gt', 'lt']:
            label_true = f"JUMP_TRUE_{self.label_count}"
            label_end = f"JUMP_END_{self.label_count}"
            self.label_count += 1
            
            self.file.write("@SP\nAM=M-1\nD=M\nA=A-1\nD=M-D\n")
            self.file.write(f"@{label_true}\n")
            
            if command == 'eq': self.file.write("D;JEQ\n")
            elif command == 'gt': self.file.write("D;JGT\n")
            elif command == 'lt': self.file.write("D;JLT\n")
            
            # False case (0)
            self.file.write("@SP\nA=M-1\nM=0\n")
            self.file.write(f"@{label_end}\n0;JMP\n")
            
            # True case (-1)
            self.file.write(f"({label_true})\n")
            self.file.write("@SP\nA=M-1\nM=-1\n")
            
            self.file.write(f"({label_end})\n")

    def writePushPop(self, command, segment, index):
        self.file.write(f"// {'push' if command == C_PUSH else 'pop'} {segment} {index}\n")
        
        # 處理 Segment Mapping
        segment_map = {
            'local': 'LCL', 'argument': 'ARG', 
            'this': 'THIS', 'that': 'THAT'
        }
        
        if command == C_PUSH:
            if segment == 'constant':
                self.file.write(f"@{index}\nD=A\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment in segment_map:
                self.file.write(f"@{segment_map[segment]}\nD=M\n@{index}\nA=D+A\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment == 'temp':
                self.file.write(f"@5\nD=A\n@{index}\nA=D+A\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment == 'pointer':
                this_or_that = 'THIS' if index == 0 else 'THAT'
                self.file.write(f"@{this_or_that}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")
            elif segment == 'static':
                self.file.write(f"@{self.file_name}.{index}\nD=M\n@SP\nA=M\nM=D\n@SP\nM=M+1\n")

        elif command == C_POP:
            if segment in segment_map:
                # Address = SegmentPointer + Index
                self.file.write(f"@{segment_map[segment]}\nD=M\n@{index}\nD=D+A\n@R13\nM=D\n") # R13 暫存目標地址
                self.file.write("@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D\n")
            elif segment == 'temp':
                self.file.write(f"@5\nD=A\n@{index}\nD=D+A\n@R13\nM=D\n")
                self.file.write("@SP\nAM=M-1\nD=M\n@R13\nA=M\nM=D\n")
            elif segment == 'pointer':
                this_or_that = 'THIS' if index == 0 else 'THAT'
                self.file.write(f"@SP\nAM=M-1\nD=M\n@{this_or_that}\nM=D\n")
            elif segment == 'static':
                self.file.write(f"@SP\nAM=M-1\nD=M\n@{self.file_name}.{index}\nM=D\n")

    def close(self):
        self.file.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python VMTranslator.py [file.vm|directory]")
        return

    input_path = sys.argv[1]
    
    # 判斷輸入是檔案還是目錄
    vm_files = []
    output_file = ""
    is_dir = False

    if os.path.isdir(input_path):
        is_dir = True
        dir_name = os.path.basename(os.path.normpath(input_path))
        output_file = os.path.join(input_path, dir_name + ".asm")
        # 抓取該目錄下所有 .vm 檔
        vm_files = glob.glob(os.path.join(input_path, "*.vm"))
    else:
        output_file = input_path.replace(".vm", ".asm")
        vm_files = [input_path]

    code_writer = CodeWriter(output_file)

    # ------------------ 修正的關鍵邏輯 ------------------
    # 只有當目錄模式下，且存在 'Sys.vm' 時，才寫入 Bootstrap code。
    # 這解決了 SimpleFunction.tst 的報錯，同時保留了 FibonacciElement 等完整程式的功能。
    has_sys = False
    if is_dir:
        for f in vm_files:
            if os.path.basename(f) == "Sys.vm":
                has_sys = True
                break
    
    if is_dir and has_sys:
        code_writer.writeInit()
    # ---------------------------------------------------

    for vm_file in vm_files:
        parser = Parser(vm_file)
        code_writer.setFileName(vm_file)
        
        while parser.hasMoreCommands():
            parser.advance()
            ctype = parser.commandType()
            
            if ctype == C_ARITHMETIC:
                code_writer.writeArithmetic(parser.arg1())
            elif ctype in [C_PUSH, C_POP]:
                code_writer.writePushPop(ctype, parser.arg1(), parser.arg2())
            elif ctype == C_LABEL:
                code_writer.writeLabel(parser.arg1())
            elif ctype == C_GOTO:
                code_writer.writeGoto(parser.arg1())
            elif ctype == C_IF:
                code_writer.writeIf(parser.arg1())
            elif ctype == C_FUNCTION:
                code_writer.writeFunction(parser.arg1(), parser.arg2())
            elif ctype == C_RETURN:
                code_writer.writeReturn()
            elif ctype == C_CALL:
                code_writer.writeCall(parser.arg1(), parser.arg2())

    code_writer.close()
    print(f"Successfully generated {output_file}")

if __name__ == "__main__":
    main()