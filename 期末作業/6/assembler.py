#!/usr/bin/env python3
"""
Hack Assembler - Nand2Tetris Project 6
將 Hack 彙編語言 (.asm) 轉換為 Hack 機器碼 (.hack)
"""

import sys
import os
import re
from typing import Dict, List, Optional


class SymbolTable:
    """符號表：管理符號與記憶體位址的對應"""
    
    def __init__(self):
        self.table: Dict[str, int] = {
            # 預定義符號
            'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4,
            'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4,
            'R5': 5, 'R6': 6, 'R7': 7, 'R8': 8, 'R9': 9,
            'R10': 10, 'R11': 11, 'R12': 12, 'R13': 13, 'R14': 14, 'R15': 15,
            'SCREEN': 16384, 'KBD': 24576
        }
    
    def add_entry(self, symbol: str, address: int):
        """新增符號"""
        self.table[symbol] = address
    
    def contains(self, symbol: str) -> bool:
        """檢查符號是否存在"""
        return symbol in self.table
    
    def get_address(self, symbol: str) -> int:
        """取得符號對應的位址"""
        return self.table[symbol]


class Parser:
    """解析器：解析彙編指令"""
    
    A_COMMAND = 0
    C_COMMAND = 1
    L_COMMAND = 2
    
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.current_line = 0
        self.current_command = ""
    
    def has_more_commands(self) -> bool:
        """是否還有更多指令"""
        return self.current_line < len(self.lines)
    
    def advance(self):
        """讀取下一個指令"""
        if self.has_more_commands():
            self.current_command = self.lines[self.current_line]
            self.current_line += 1
    
    def command_type(self) -> int:
        """返回當前指令的類型"""
        if self.current_command.startswith('@'):
            return self.A_COMMAND
        elif self.current_command.startswith('('):
            return self.L_COMMAND
        else:
            return self.C_COMMAND
    
    def symbol(self) -> str:
        """返回 A 指令或 L 指令的符號"""
        if self.command_type() == self.A_COMMAND:
            return self.current_command[1:]
        elif self.command_type() == self.L_COMMAND:
            return self.current_command[1:-1]
        return ""
    
    def dest(self) -> Optional[str]:
        """返回 C 指令的 dest 部分"""
        if '=' in self.current_command:
            return self.current_command.split('=')[0]
        return None
    
    def comp(self) -> str:
        """返回 C 指令的 comp 部分"""
        cmd = self.current_command
        if '=' in cmd:
            cmd = cmd.split('=')[1]
        if ';' in cmd:
            cmd = cmd.split(';')[0]
        return cmd
    
    def jump(self) -> Optional[str]:
        """返回 C 指令的 jump 部分"""
        if ';' in self.current_command:
            return self.current_command.split(';')[1]
        return None


class Code:
    """代碼生成器：將助記符轉換為二進制碼"""
    
    DEST_TABLE = {
        None: '000', 'M': '001', 'D': '010', 'MD': '011',
        'A': '100', 'AM': '101', 'AD': '110', 'AMD': '111'
    }
    
    JUMP_TABLE = {
        None: '000', 'JGT': '001', 'JEQ': '010', 'JGE': '011',
        'JLT': '100', 'JNE': '101', 'JLE': '110', 'JMP': '111'
    }
    
    COMP_TABLE = {
        '0': '0101010', '1': '0111111', '-1': '0111010',
        'D': '0001100', 'A': '0110000', '!D': '0001101',
        '!A': '0110001', '-D': '0001111', '-A': '0110011',
        'D+1': '0011111', 'A+1': '0110111', 'D-1': '0001110',
        'A-1': '0110010', 'D+A': '0000010', 'D-A': '0010011',
        'A-D': '0000111', 'D&A': '0000000', 'D|A': '0010101',
        'M': '1110000', '!M': '1110001', '-M': '1110011',
        'M+1': '1110111', 'M-1': '1110010', 'D+M': '1000010',
        'D-M': '1010011', 'M-D': '1000111', 'D&M': '1000000',
        'D|M': '1010101'
    }
    
    @staticmethod
    def dest(mnemonic: Optional[str]) -> str:
        """返回 dest 助記符的二進制碼"""
        return Code.DEST_TABLE.get(mnemonic, '000')
    
    @staticmethod
    def comp(mnemonic: str) -> str:
        """返回 comp 助記符的二進制碼"""
        return Code.COMP_TABLE.get(mnemonic, '0000000')
    
    @staticmethod
    def jump(mnemonic: Optional[str]) -> str:
        """返回 jump 助記符的二進制碼"""
        return Code.JUMP_TABLE.get(mnemonic, '000')


class Assembler:
    """主要的 Assembler 類別"""
    
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.output_file = input_file.replace('.asm', '.hack')
        self.symbol_table = SymbolTable()
        self.next_var_address = 16
    
    def clean_line(self, line: str) -> Optional[str]:
        """清理一行程式碼：移除空白和註解"""
        # 移除註解
        line = re.sub(r'//.*', '', line)
        # 移除空白
        line = line.strip()
        return line if line else None
    
    def read_file(self) -> List[str]:
        """讀取並清理輸入檔案"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"錯誤: 找不到檔案 '{self.input_file}'")
            print(f"請確認檔案存在於當前目錄: {os.getcwd()}")
            sys.exit(1)
        except Exception as e:
            print(f"讀取檔案時發生錯誤: {e}")
            sys.exit(1)
        
        cleaned_lines = []
        for line in lines:
            cleaned = self.clean_line(line)
            if cleaned:
                cleaned_lines.append(cleaned)
        
        return cleaned_lines
    
    def first_pass(self, lines: List[str]) -> List[str]:
        """第一次掃描：建立標籤符號表"""
        parser = Parser(lines)
        rom_address = 0
        instructions = []
        
        while parser.has_more_commands():
            parser.advance()
            
            if parser.command_type() == Parser.L_COMMAND:
                # 標籤指令：記錄標籤位址
                symbol = parser.symbol()
                self.symbol_table.add_entry(symbol, rom_address)
            else:
                # A 或 C 指令：記錄並增加 ROM 位址
                instructions.append(parser.current_command)
                rom_address += 1
        
        return instructions
    
    def second_pass(self, instructions: List[str]) -> List[str]:
        """第二次掃描：生成機器碼"""
        parser = Parser(instructions)
        machine_code = []
        
        while parser.has_more_commands():
            parser.advance()
            
            if parser.command_type() == Parser.A_COMMAND:
                # A 指令
                symbol = parser.symbol()
                
                if symbol.isdigit():
                    # 數字常數
                    address = int(symbol)
                else:
                    # 符號
                    if not self.symbol_table.contains(symbol):
                        # 新變數：分配位址
                        self.symbol_table.add_entry(symbol, self.next_var_address)
                        self.next_var_address += 1
                    address = self.symbol_table.get_address(symbol)
                
                # 轉換為 16 位元二進制
                binary = format(address, '016b')
                machine_code.append(binary)
            
            elif parser.command_type() == Parser.C_COMMAND:
                # C 指令
                dest = Code.dest(parser.dest())
                comp = Code.comp(parser.comp())
                jump = Code.jump(parser.jump())
                
                # C 指令格式：111accccccdddjjj
                binary = '111' + comp + dest + jump
                machine_code.append(binary)
        
        return machine_code
    
    def assemble(self):
        """執行彙編"""
        print(f"正在彙編: {self.input_file}")
        
        # 讀取檔案
        lines = self.read_file()
        
        # 第一次掃描：處理標籤
        instructions = self.first_pass(lines)
        
        # 第二次掃描：生成機器碼
        machine_code = self.second_pass(instructions)
        
        # 寫入輸出檔案
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for code in machine_code:
                f.write(code + '\n')
        
        print(f"彙編完成: {self.output_file}")
        print(f"生成了 {len(machine_code)} 行機器碼")


def main():
    if len(sys.argv) != 2:
        print("使用方式: python assembler.py <file.asm>")
        print(f"當前目錄: {os.getcwd()}")
        print("\n目錄中的 .asm 檔案:")
        asm_files = [f for f in os.listdir('.') if f.endswith('.asm')]
        if asm_files:
            for f in asm_files:
                print(f"  - {f}")
        else:
            print("  (沒有找到 .asm 檔案)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not input_file.endswith('.asm'):
        print("錯誤: 輸入檔案必須是 .asm 檔案")
        sys.exit(1)
    
    if not os.path.exists(input_file):
        print(f"錯誤: 檔案 '{input_file}' 不存在")
        print(f"當前目錄: {os.getcwd()}")
        sys.exit(1)
    
    assembler = Assembler(input_file)
    assembler.assemble()


if __name__ == '__main__':
    main()