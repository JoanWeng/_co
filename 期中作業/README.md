# Nand2Tetris 第1–5章內容整理

## 作業說明
第一章中大部分是老師上課講解時寫的，剩下的部分到第三章前都是ChatGPT生成(沒有網址)
第三章~第五章由Claude生成

網址:
[第三章](https://claude.ai/share/6d04af7c-f800-4c32-b0a0-483d91b9c9e9)
[第四章](https://claude.ai/share/1fd917a6-9a83-4516-83fa-d81c9bf33094)
[第五章](https://claude.ai/share/6ef31a06-1887-4242-abef-cb766aebe0aa)

每一章的內容都有自己測試過，結果都是對的

## 第 1 章：Boolean Logic（布林邏輯）

### 核心目標

* 以 **NAND Gate** 作為唯一基礎元件
* 建構所有必要的邏輯閘與多工元件

### 重要概念

* **NAND 是功能完備（functional complete）**：可組合出所有布林運算
* 布林運算：AND、OR、NOT、XOR
* 位元層級（bit-wise）與多位元（multi-bit）運算

### 實作元件（Chips）

* 基本邏輯閘：

  * `Not`, `And`, `Or`, `Xor`
* 多工／解多工：

  * `Mux`, `DMux`
* 多位元版本：

  * `Not16`, `And16`, `Mux16`

### 本章產出

* 一組可重複使用的 **組合邏輯元件庫**

---

## 第 2 章：Boolean Arithmetic（布林算術）

### 核心目標

* 在布林邏輯基礎上實作 **二進位算術運算**

### 重要概念

* 二進位加法（Binary Addition）
* 進位（Carry）傳遞
* Two's Complement（補數）表示法

### 實作元件

* 加法器：

  * `HalfAdder`
  * `FullAdder`
* 多位元加法：

  * `Add16`
* 算術邏輯單元：

  * `ALU`

### ALU 重點

* 輸入：`x`, `y`（16-bit）
* 控制位元：`zx, nx, zy, ny, f, no`
* 輸出：

  * 計算結果 `out`
  * 狀態旗標 `zr`（是否為 0）、`ng`（是否為負）

### 本章產出

* 一個可執行所有基本算術／邏輯運算的 **ALU**

---

## 第 3 章：Sequential Logic（循序邏輯）

### 核心目標

* 讓電路具備 **記憶能力（state）**

### 重要概念

* Clock（時脈）
* 狀態（State）與時間
* 組合邏輯 vs 循序邏輯

### 實作元件

* 基本儲存元件：

  * `Bit`
  * `Register`（16-bit）
* 記憶體模組：

  * `RAM8`, `RAM64`, `RAM512`, `RAM4K`, `RAM16K`
* 計數器：

  * `PC`（Program Counter）

### PC 功能

* `load`：載入新位址
* `inc`：+1
* `reset`：歸零

### 本章產出

* 完整的 **暫存器、記憶體與程式計數器**

---

## 第 4 章：Machine Language（機器語言）

### 核心目標

* 定義一套可被硬體直接執行的 **Hack 機器語言**

### Hack 電腦簡介

* 16-bit 電腦
* Harvard Architecture（指令與資料分離）

### 記憶體配置

* `ROM[0..32767]`：指令
* `RAM[0..16383]`：資料
* 特殊位址：

  * `R0–R15`
  * `SCREEN`
  * `KEYBOARD`

### 指令類型

* **A-instruction**：

  * `@value`（設定 A 暫存器）
* **C-instruction**：

  * `dest = comp ; jump`

### 本章產出

* 一套完整、簡單但可實際運作的 **機器語言規格**

---

## 第 5 章：Computer Architecture（電腦架構）

### 核心目標

* 整合前四章元件，建構一台完整電腦

### CPU 組成

* ALU
* 暫存器：A、D
* 控制邏輯（Control Logic）

### CPU 功能

* 解碼指令（A / C instruction）
* 控制 ALU 運算
* 控制資料寫入（A、D、Memory）
* 控制跳躍（Jump）與 PC 更新

### 電腦整體結構

* CPU
* Instruction Memory（ROM）
* Data Memory（RAM）

### 本章產出

* 一台可執行 Hack 機器語言的 **完整電腦（Computer.hdl）**