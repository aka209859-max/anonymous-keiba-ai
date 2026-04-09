# Windows Batch File Encoding and Execution Error - Deep Investigation Request

## 🎯 Investigation Objective
Fix a Windows batch file that is corrupted due to encoding issues, preventing execution of a multi-phase AI prediction pipeline for Japanese local horse racing.

---

## 📋 Problem Summary

### Current Situation
- **Environment**: Windows 10 (Build 26100.7840), Japanese locale
- **Project**: `E:\anonymous-keiba-ai` - AI horse racing prediction system
- **Issue**: Batch file `run_all_optimized.bat` fails with encoding-related errors
- **Impact**: Cannot execute automated prediction pipeline (Phase 0-6)

### Error Symptoms
When executing `run_all_optimized.bat 43 2026-02-13`, the following errors occur:

```
'NCODING' は、内部コマンドまたは外部コマンド、
操作可能なプログラムまたはバッチ ファイルとして認識されていません。
'TE]' は、内部コマンドまたは外部コマンド、
操作可能なプログラムまたはバッチ ファイルとして認識されていません。
'""' は、内部コマンドまたは外部コマンド、
操作可能なプログラムまたはバッチ ファイルとして認識されていません。
'ET_DATE' は、内部コマンドまたは外部コマンド、
操作可能なプログラムまたはバッチ ファイルとして認識されていません。
```

**Analysis**: The batch file's content is being parsed incorrectly:
- `PYTHONIOENCODING=utf-8` is parsed as `'NCODING'`
- Variable names are split incorrectly
- Japanese characters (競馬場名) may be causing line breaks
- `echo` statements are fragmented

### What Works
✅ **Model files exist and are correct**:
- Location: `E:\anonymous-keiba-ai\data\models\tuned\`
- Files: 42 total (14 venues × 3 model types)
- Example: `funabashi_tuned_model.txt` (7.2MB), `funabashi_ranking_tuned_model.txt` (2.1MB), `funabashi_regression_tuned_model.txt` (2.4MB)

✅ **Python scripts work correctly**:
- Phase 0-8 prediction scripts are functional
- Models load successfully when scripts are called directly

✅ **Previous execution succeeded partially**:
- Output file was created: `船橋_20260213_ensemble_optimized.csv` (18,481 bytes)
- This proves the pipeline logic is correct

---

## 🔬 Technical Details

### Batch File Structure (Expected)
The batch file should:
1. Set UTF-8 environment (`chcp 65001`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`)
2. Accept 2 arguments: `KEIBAJO_CODE` (venue code, e.g., 43) and `DATE` (YYYY-MM-DD)
3. Map venue codes to Japanese names (30=門別, 35=盛岡, ..., 55=佐賀)
4. Execute pipeline:
   - Phase 0: Data acquisition
   - Phase 1: Feature engineering
   - Phase 7: Binary prediction
   - Phase 8: Ranking + Regression prediction
   - Phase 5: Ensemble integration
   - Phase 6: Text generation for distribution

### Encoding History
- Original file: Created with UTF-8 BOM encoding
- Issue: Windows `cmd.exe` cannot parse UTF-8 BOM correctly in Japanese locale
- Previous attempts:
  - Saved as Shift-JIS → still corrupted
  - Created via PowerShell with explicit encoding → file transfer issue
  - Renamed `.bat.old` back to `.bat` → current state (corrupted)

### Key Requirements
1. **14 venues must work**: Not just venue 43 (Funabashi), but all 14 racetracks (codes 30-55)
2. **Japanese text must display correctly**: Venue names and messages
3. **Stable execution**: No encoding-related errors
4. **Root cause fix**: Not a temporary workaround

---

## 🔍 Investigation Request

### Priority 1: Encoding Diagnosis
Please investigate:

1. **What is the exact encoding of the current file?**
   - Provide commands to check: BOM presence, actual encoding (UTF-8/UTF-16/Shift-JIS/CP932)
   - Example tools: `Get-Content -Encoding Byte`, `file` command, hex editor patterns

2. **Why does Windows cmd.exe fail to parse it?**
   - Japanese Windows locale specifics
   - `chcp 65001` vs `chcp 932` behavior
   - BOM handling differences

3. **What is the correct encoding for Japanese Windows batch files?**
   - Official Microsoft recommendations
   - Best practices for batch files with Japanese text
   - Successful case studies

### Priority 2: Root Cause Analysis
Please provide:

1. **Line-by-line parsing analysis**
   - Why is `PYTHONIOENCODING=utf-8` parsed as `'NCODING'`?
   - What causes `set "KEIBAJO_CODE=%~1"` to become `'ET_DATE'`?
   - Character-level breakdown of the corruption

2. **Common pitfalls**
   - UTF-8 BOM in batch files
   - Line ending issues (CRLF vs LF)
   - Character encoding mismatches

### Priority 3: Proven Solutions
Please provide:

1. **Step-by-step fix procedure**
   - Exact commands to convert the file
   - Tool recommendations (Windows built-in preferred)
   - Verification steps

2. **Prevention methods**
   - How to create batch files that never have this issue
   - Editor settings (VS Code, Notepad++, etc.)
   - Git configuration for Windows (core.autocrlf, etc.)

3. **Alternative approaches**
   - PowerShell scripts instead of batch files?
   - Python wrapper scripts?
   - WSL/Git Bash compatibility?

### Priority 4: Workaround Until Fix
**Immediate need**: A method to get the prediction pipeline running today

Options to evaluate:
- Use old batch file (`run_all.bat`) that works
- Create minimal batch file without Japanese text
- Direct Python execution with shell scripts
- Other emergency solutions

---

## 📎 Attached Files

Please analyze these files:

1. **Error log**: `Eanonymous-keiba-aicd Eanonymous-ke.md`
   - Contains full execution log with errors
   - Shows model files exist correctly
   - Proves partial success (output file created)

2. **Working batch file reference** (if available):
   - `run_all.bat` - older version that works
   - Can be used as comparison baseline

---

## 📊 Expected Deliverables

### 1. Diagnostic Report
```
- Current file encoding: [UTF-8 BOM / Shift-JIS / etc.]
- BOM signature: [EF BB BF / None / etc.]
- Line endings: [CRLF / LF / Mixed]
- Corruption pattern: [Detailed analysis]
- Root cause: [Explanation]
```

### 2. Fix Procedure (Preferred Solution)
```powershell
# Step 1: Backup current file
# Step 2: Convert encoding (exact command)
# Step 3: Verify (exact command)
# Step 4: Test execution
```

### 3. Code Template
Provide a **working batch file** that:
- Uses correct encoding for Japanese Windows
- Handles 14 venues (codes 30-55)
- Executes the 6-phase pipeline
- **Has been tested on Windows 10 Japanese locale**

### 4. Best Practices Document
- How to prevent this issue in the future
- Recommended tools and settings
- Git configuration for the team

---

## 🎯 Success Criteria

The solution is successful when:

1. ✅ `run_all_optimized.bat 43 2026-02-13` executes without encoding errors
2. ✅ All 14 venues work (codes 30, 35, 36, 42-48, 50, 51, 54, 55)
3. ✅ Japanese text displays correctly in console output
4. ✅ Pipeline completes Phase 0-6 successfully
5. ✅ Output files are generated:
   - `data\predictions\phase5\{venue}_{date}_ensemble_optimized.csv`
   - `predictions\{venue}_{date}_note.txt`
   - `predictions\{venue}_{date}_bookers.txt`
   - `predictions\{venue}_{date}_tweet.txt`

---

## 🔗 Reference Links (If Known)

- Microsoft Docs: [Windows Batch File Encoding](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/chcp)
- Stack Overflow: Similar issues (if you have examples)
- GitHub Issues: Batch file encoding problems (if you have examples)

---

## 📞 Contact & Follow-up

- **Urgency**: High - Production system needs to run daily
- **Timeline**: Solution needed within 24 hours
- **Follow-up**: Will provide additional files/logs if needed

---

**Investigation Date**: 2026-02-14  
**Issue ID**: BATCH-ENCODING-001  
**System**: Windows 10 Build 26100.7840, Japanese Locale  
**Project**: anonymous-keiba-ai Phase 7-8-5 Integration
