# Nand2Tetris 第6–12章內容整理

從 **硬體完成後**，往上建構軟體系統：Assembler → VM → OS → Compiler → 完整平台。

## 作業說明
第六章~第九章由Claude生成

第九章~第十一章由gemini生成

網址:
[第六章](https://claude.ai/share/8a678e0b-9da8-4ff5-aacd-1f1fc4325002)
[第七章&第八章](https://claude.ai/share/53ba6c35-283d-4bb2-82a0-1262751b025d)
[第九章](https://claude.ai/share/8dea08fd-34ae-4e72-b18e-f556f3d531c6)
[第十章&第十一章](https://github.com/JoanWeng/_co/blob/main/%E6%9C%9F%E6%9C%AB%E4%BD%9C%E6%A5%AD/AI_Studio_Gemini%E5%B0%8D%E8%A9%B1)

貪吃蛇由Gemini完成

每一章的內容都有自己測試過，結果都是對的

因為我先做第八章，當時卡在SimpleFunction上很久，後來發現只需要對.vm檔案執行翻譯器，並執行.tst檔就行。是因為SimpleFunction裡面並沒有定義Sys.init函式，執行時要和第七章一樣對著.vm檔，而非目錄路徑

## 第 6 章：Assembler（組譯器）

### 核心目標

* 將 **Hack Assembly** 翻譯為 **16-bit Machine Code**

### Assembler 職責

* 處理符號（Symbols）
* 指令轉碼（Instruction Translation）

### 重要概念

* **兩次掃描（Two-pass）**：

  1. 第一遍：建立 Symbol Table（標籤 → ROM 位址）
  2. 第二遍：翻譯指令並配置變數 RAM 位址（從 RAM[16] 開始）

### 指令處理

* A-instruction：`@value / @symbol`
* C-instruction：`dest=comp;jump`

### 本章產出

* 一個可運作的 **Hack Assembler**

---

## 第 7 章：VM I — Stack Arithmetic（虛擬機第一部分）

### 核心目標

* 定義 **Virtual Machine（VM）指令集**
* 將高階語言運算抽象化為 Stack 操作

### VM 架構

* Stack-based machine
* 所有運算皆透過 Stack 進行

### 指令類型

* Stack operations：

  * `push`, `pop`
* Arithmetic / Logical：

  * `add`, `sub`, `neg`, `eq`, `gt`, `lt`, `and`, `or`, `not`

### 記憶體區段（Segments）

* `constant`
* `local`, `argument`
* `this`, `that`
* `temp`, `pointer`, `static`

### 本章產出

* VM Translator（算術與記憶體存取部分）

---

## 第 8 章：VM II — Program Control（虛擬機第二部分）

### 核心目標

* 支援 **流程控制與函式呼叫**

### 新增指令

* Program flow：

  * `label`, `goto`, `if-goto`
* Function calling：

  * `function`, `call`, `return`

### Function Call 機制

* 保存呼叫者狀態：

  * LCL, ARG, THIS, THAT
* 建立新 stack frame
* Return 時還原狀態

### 本章產出

* 完整 VM Translator（可翻譯多檔 VM 程式）

---

## 第 9 章：High-Level Language（高階語言 Jack）

### 核心目標

* 設計一個簡單的物件導向語言：**Jack**

### Jack 語言特色

* 類似 Java / C#
* 支援：

  * Class, Method, Function, Constructor
  * if / while / let / do / return

### 基本型別

* `int`, `char`, `boolean`
* Class type（物件）

### 本章產出

* Jack 語言規格（尚未實作編譯器）

---

## 第 10 章：Compiler I — Syntax Analysis（語法分析）

### 核心目標

* 將 Jack 程式轉為 **語法結構**

### 編譯器階段

* Tokenizer（Lexical Analysis）
* Parser（Syntax Analysis）

### Token 類型

* Keyword
* Symbol
* Identifier
* IntegerConstant
* StringConstant

### 輸出形式

* XML 語法樹（Parse Tree）

### 本章產出

* Jack Tokenizer + Parser

---

## 第 11 章：Compiler II — Code Generation（程式碼產生）

### 核心目標

* 將 Jack 程式 **直接翻譯成 VM Code**

### Symbol Table

* 類別層級：static, field
* 子程式層級：argument, local

### 程式碼生成重點

* 表達式運算
* 陣列存取
* 物件方法呼叫（this）
* Constructor / Method / Function 差異

### 本章產出

* 完整 Jack Compiler（Jack → VM）

---

## 第 12 章：Operating System（作業系統）

### 核心目標

* 為 Jack 程式提供 **執行期支援**

### OS 模組

* `Math`：乘除、平方根
* `String`：字串處理
* `Array`：陣列配置
* `Memory`：heap 管理
* `Screen`：螢幕輸出
* `Keyboard`：鍵盤輸入
* `Sys`：系統啟動

### 實作語言

* 使用 **Jack 本身** 實作 OS

### 本章產出

* 一套完整可用的 **Jack OS**