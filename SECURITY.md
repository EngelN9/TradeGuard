# **Security Policy**

TradeGuard 是一個用於安全研究、監控與驗證股票及加密貨幣交易策略的平台。

本專案可能處理：

* 市場資料。  
* 策略程式碼。  
* 回測結果。  
* Paper trading 資料。  
* Shadow monitoring 資料。  
* 唯讀帳戶資訊。  
* 外部服務 API 憑證。  
* 持倉、成交與損益紀錄。  
* 使用者設定與稽核紀錄。

即使 TradeGuard 第一版不支援正式交易，任何安全缺陷仍可能造成：

* 敏感資料外洩。  
* 帳戶資訊外洩。  
* API key 遭竊。  
* 回測結果遭竄改。  
* 風險監控失效。  
* 策略驗證結果失真。  
* 使用者被錯誤資訊誤導。  
* Paper 或 shadow 環境被誤認為正式環境。  
* 未授權操作。  
* 供應鏈攻擊。  
* 惡意策略程式碼執行。

本文件說明如何安全回報漏洞、TradeGuard 的安全責任邊界，以及維護者處理安全問題的原則。

---

## **1\. 安全原則**

TradeGuard 的安全決策遵循以下優先順序：

1. 保護使用者帳戶與憑證。  
2. 防止未授權交易或資產操作能力出現。  
3. 保護策略、研究資料與交易紀錄。  
4. 保持研究結果完整性與可重現性。  
5. 保持風險監控、對帳與稽核能力。  
6. 保留事故證據。  
7. 在狀態不明時 fail closed。  
8. 誠實揭露安全限制。

TradeGuard 不會因開發速度、操作便利性或績效展示而降低安全控制。

---

## **2\. 支援版本**

目前 TradeGuard 尚處於：

EQUITY ADAPTER IMPLEMENTED / NOT TRADABLE

目前已完成 repository bootstrap、Prompt 2 核心資料合約與 Prompt 3 離線
資料基礎；尚未進入策略、回測或外部資料接入階段，也沒有正式下單、提款或
轉帳能力。

在第一個正式版本發布前，安全修正原則上只會套用至預設分支：

main

正式發布後，預計採用下列支援政策：

| 版本 | 安全更新 |
| ----- | ----- |
| 最新穩定版本 | 支援 |
| 前一個次要版本 | 視嚴重程度提供 |
| 更舊版本 | 不保證支援 |
| 開發分支 | 不保證穩定，但接受安全回報 |
| Fork 或第三方修改版 | 不由本專案保證 |

若漏洞只存在於第三方 fork，請優先聯絡該 fork 的維護者。

若漏洞同時影響 TradeGuard 上游版本，請依本文件回報。

---

## **3\. 安全責任邊界**

TradeGuard 第一版只允許：

research  
backtest  
replay  
paper  
shadow

第一版不支援：

canary  
live

TradeGuard 第一版不得：

* 使用正式交易 API key。  
* 自動送出正式訂單。  
* 提款。  
* 轉帳。  
* 管理子帳戶。  
* 建立或刪除交易所 API key。  
* 修改帳戶安全設定。  
* 自動提高風險限制。  
* 由大型語言模型直接決定正式交易。  
* 自動將策略晉級至正式交易。

如果你發現任何可以繞過上述限制的路徑，請將其視為安全漏洞回報。

---

## **4\. 如何回報安全漏洞**

請不要使用公開 GitHub Issue 回報尚未修復的安全漏洞。

主要私密通報管道：

[GitHub Private Vulnerability Reporting](https://github.com/EngelN9/TradeGuard/security/advisories/new)

如果 Private Vulnerability Reporting 暫時不可用，請勿透過公開 Issue、
Pull Request 或公開個人檔案傳送漏洞細節。可以使用 repository 擁有者公開
個人檔案中列出的私人聯絡方式，僅通知維護者恢復上述私密通報管道；在管道
恢復前，不得傳送可利用細節或敏感資料。

### **回報標題**

建議使用：

\[SECURITY\] TradeGuard vulnerability report

### **回報內容**

請盡可能包含：

* 漏洞摘要。  
* 受影響版本或 commit SHA。  
* 受影響元件。  
* 漏洞類型。  
* 前置條件。  
* 重現步驟。  
* 最小可重現範例。  
* 預期行為。  
* 實際行為。  
* 可能影響。  
* 是否已被公開利用。  
* 是否可能接觸真實憑證或帳戶資料。  
* 建議修正方式。  
* 測試環境。  
* 相關 log。  
* Screenshot 或錄影。  
* Proof of concept。

請先移除或遮罩：

* API key。  
* Secret。  
* Access token。  
* Session cookie。  
* Authorization header。  
* 帳戶號碼。  
* 個人識別資訊。  
* 真實持倉。  
* 真實成交紀錄。  
* 不可公開的市場資料。  
* 第三方使用者資料。

---

## **5\. 請勿公開揭露**

在維護者完成修正並同意揭露前，請勿：

* 建立公開 GitHub Issue。  
* 建立公開 Pull Request。  
* 發布完整 proof of concept。  
* 發布可直接利用的 exploit。  
* 公開貼出真實 secret。  
* 公開受影響使用者資料。  
* 公開尚未撤銷的 API key。  
* 對非自有帳戶進行測試。  
* 對正式服務執行破壞性測試。  
* 以漏洞取得、修改或刪除他人資料。  
* 透過漏洞送出任何真實交易。  
* 透過漏洞嘗試提款或轉移資產。  
* 造成服務阻斷。  
* 刪除或修改稽核紀錄。

我們支持負責任揭露，但不授權對第三方系統、交易所、券商或其他使用者帳戶進行測試。

---

## **6\. 安全回報處理流程**

收到安全回報後，維護者預計依下列流程處理：

收到回報  
  ↓  
確認收件  
  ↓  
初步分類  
  ↓  
重現與影響評估  
  ↓  
建立私人修正分支  
  ↓  
開發修正與回歸測試  
  ↓  
安全審查  
  ↓  
發布修正  
  ↓  
通知回報者  
  ↓  
協調公開揭露  
  ↓  
事故與控制改善

### **目標回應時間**

下列時間是目標，不是法律或服務等級保證：

| 階段 | 目標時間 |
| ----- | ----- |
| 確認收到回報 | 3 個工作日內 |
| 初步嚴重程度評估 | 7 個工作日內 |
| 提供下一步狀態 | 14 個工作日內 |
| 高嚴重度問題修正 | 依影響與複雜度優先處理 |
| 協調公開揭露 | 修正可用後進行 |

若問題涉及：

* 正式憑證外洩。  
* 帳戶接管。  
* 未授權交易能力。  
* 資料庫外洩。  
* 遠端程式碼執行。  
* 供應鏈攻擊。  
* 稽核紀錄遭竄改。  
* 安全限制被繞過。

維護者應立即啟動緊急事故處理。

---

## **7\. 嚴重程度分類**

TradeGuard 應綜合考慮：

* 可利用性。  
* 所需權限。  
* 是否需要使用者互動。  
* 影響資料範圍。  
* 是否影響帳戶或憑證。  
* 是否可能產生未授權交易。  
* 是否能持久化控制系統。  
* 是否可繞過風控。  
* 是否會破壞研究完整性。  
* 是否會隱藏事故。  
* 是否可影響多位使用者。

### **Critical**

範例：

* 遠端未授權程式碼執行。  
* 正式或高權限 API key 外洩。  
* 未授權提款或資產轉移能力。  
* 未授權正式下單能力。  
* 任意使用者帳戶接管。  
* 可繞過所有權限與風控。  
* 可竄改不可變稽核紀錄。  
* 可修改研究資料並隱藏痕跡。  
* 供應鏈攻擊導致惡意程式碼被發布。  
* 讀取所有使用者秘密或帳戶資料。  
* 惡意策略外掛逃逸隔離環境。

### **High**

範例：

* 跨使用者資料存取。  
* 權限提升。  
* Read-only API key 外洩。  
* 任意檔案讀取。  
* 任意檔案寫入。  
* SSRF 可存取內部服務或雲端 metadata。  
* SQL injection。  
* 認證繞過。  
* 可關閉重要風控或告警。  
* 可將 shadow 環境誤標為 live。  
* 可修改 promotion evidence。  
* 可持久竄改回測結果。

### **Medium**

範例：

* 儲存型 XSS。  
* CSRF 影響敏感設定。  
* 部分敏感資訊洩漏。  
* Log 中包含被遮罩不完整的識別資訊。  
* Rate-limit 缺失導致資源耗盡。  
* 不安全預設設定。  
* 權限檢查只在前端執行。  
* 可偽造非關鍵稽核欄位。  
* 錯誤訊息暴露內部結構。

### **Low**

範例：

* 不影響機密性、完整性或可用性的資訊揭露。  
* 安全標頭缺失，但無實際利用路徑。  
* 低風險版本資訊揭露。  
* 不敏感頁面的反射型 XSS。  
* 文件中的安全建議不完整。

最終嚴重程度由維護者依實際影響決定。

---

## **8\. 安全漏洞範圍**

以下類型通常屬於有效安全回報。

### **8.1 認證與授權**

* 認證繞過。  
* Session fixation。  
* Session hijacking。  
* 密碼重設問題。  
* MFA 繞過。  
* RBAC 繞過。  
* IDOR。  
* Cross-tenant data access。  
* 權限提升。  
* 未授權設定變更。  
* 未授權策略 promotion。

### **8.2 Secret 與憑證**

* API key 外洩。  
* Secret 被記錄到 log。  
* Secret 出現在前端 bundle。  
* Secret 出現在錯誤訊息。  
* Secret 出現在 Git 歷史。  
* Secret 未加密儲存。  
* Secret 可被低權限使用者讀取。  
* Secret redaction 可被繞過。  
* 憑證撤銷後仍可使用。  
* 高權限 key 被錯誤接受。

### **8.3 外部 API**

* SSRF。  
* 不安全 redirect。  
* Webhook 簽章驗證錯誤。  
* Replay attack。  
* API 回應未驗證。  
* TLS 驗證遭停用。  
* Certificate validation 錯誤。  
* Rate-limit 處理可被濫用。  
* 外部狀態被錯誤視為成功。  
* Sandbox 與正式 API endpoint 混淆。

### **8.4 資料與資料庫**

* SQL injection。  
* 未授權資料讀取。  
* 未授權資料修改。  
* 未授權資料刪除。  
* Backup 外洩。  
* 不安全 migration。  
* 多租戶隔離錯誤。  
* 不可變資料可被覆寫。  
* Dataset manifest 可被偽造。  
* Checksum 驗證可被繞過。  
* 稽核紀錄可被刪改。

### **8.5 Web 安全**

* XSS。  
* CSRF。  
* Clickjacking。  
* Open redirect。  
* CORS 錯誤。  
* CSP 問題。  
* Cookie 安全屬性缺失。  
* Path traversal。  
* 檔案上傳漏洞。  
* 不安全 deserialization。  
* Template injection。

### **8.6 程式碼執行與策略外掛**

* 任意程式碼執行。  
* Sandbox escape。  
* 惡意 pickle 或不安全序列化。  
* 未受限制策略 plugin。  
* 任意 shell command。  
* 任意 Python import。  
* 可透過報告模板執行程式碼。  
* 可透過資料檔案觸發程式碼。  
* 可透過 notebook 或 strategy package 存取 host secret。

### **8.7 研究完整性**

下列問題若可被惡意利用，也可能視為安全漏洞：

* 回測結果可被未授權修改。  
* 策略版本可被替換但保留原 hash。  
* Run manifest 可被偽造。  
* Git commit 與實際程式碼不一致。  
* Dataset checksum 驗證被停用。  
* 不利結果可從稽核歷史刪除。  
* Paper 結果可被標示為 live。  
* 失敗驗證可被隱藏。  
* Promotion gate 可被未授權繞過。

### **8.8 供應鏈**

* 惡意 dependency。  
* Dependency confusion。  
* Typosquatting。  
* 不安全 GitHub Actions。  
* 過度寬鬆 workflow permissions。  
* Pull Request 可取得 repository secret。  
* 未固定 Actions commit。  
* 不可信建置產物。  
* Container image 遭竄改。  
* Release artifact 缺乏完整性驗證。  
* Lockfile 可被繞過。

---

## **9\. 通常不屬於漏洞的問題**

以下問題通常不視為安全漏洞，除非能證明具體安全影響：

* 單純缺少功能。  
* 策略表現不佳。  
* 回測虧損。  
* 市場資料供應商錯誤。  
* 公開資訊揭露。  
* 已知且明確標示的限制。  
* 不支援特定瀏覽器。  
* 不影響安全的 UI 問題。  
* 需要實體存取已解鎖裝置的問題。  
* Self-XSS。  
* 只影響回報者自己資料的非持久問題。  
* 無敏感操作的 CSRF。  
* 無法重現的自動掃描結果。  
* 缺乏具體影響的版本過舊警告。  
* 單純缺少特定 HTTP header。  
* 理論性攻擊但無實際利用路徑。  
* 需要 root 或系統管理員權限才能利用的問題。  
* 第三方服務自身的漏洞。  
* 使用者自行將 secret 公開後造成的損害。  
* 使用未支援版本造成的問題。  
* 社交工程。  
* Phishing。  
* Denial-of-service 壓力測試。  
* 大量自動化掃描。

若掃描器發現依賴漏洞，請提供：

* 受影響套件。  
* 受影響版本。  
* TradeGuard 是否實際使用脆弱程式路徑。  
* 可利用條件。  
* 實際影響。

只提供 CVE 編號通常不足以判定漏洞成立。

---

## **10\. 安全測試限制**

除非取得明確書面授權，請勿：

* 掃描正式服務。  
* 執行大規模自動化掃描。  
* 執行壓力測試。  
* 執行 DoS。  
* 執行 DDoS。  
* 測試真實使用者帳戶。  
* 測試非自有 API key。  
* 存取非自有資料。  
* 修改或刪除資料。  
* 執行 social engineering。  
* 對維護者進行 phishing。  
* 測試第三方交易所或券商。  
* 嘗試提款。  
* 嘗試資產轉移。  
* 嘗試建立真實訂單。  
* 上傳惡意程式至公開服務。  
* 破壞 log 或 audit trail。

安全研究應優先使用：

* 本機環境。  
* 自建測試環境。  
* Mock service。  
* Sandbox。  
* Paper account。  
* 合成資料。  
* 自有測試帳戶。

---

## **11\. API Key 與帳戶安全**

### **11.1 允許權限**

TradeGuard 第一版只應接受：

* Public market-data key。  
* Read-only account key。  
* Sandbox key。  
* Paper trading key。

### **11.2 禁止權限**

TradeGuard 第一版不得要求：

* 提款權限。  
* 資產轉移權限。  
* 子帳戶管理權限。  
* API key 管理權限。  
* 正式交易權限。  
* 未限制來源 IP 的高權限 key。  
* 可修改帳戶安全設定的權限。

若系統收到超出允許範圍的 key，應：

1. 拒絕保存。  
2. 拒絕啟用。  
3. 顯示明確錯誤。  
4. 不記錄完整 key。  
5. 建議使用者立即撤銷並建立最小權限 key。

### **11.3 Key 儲存**

憑證必須：

* 不提交至 Git。  
* 不放入前端。  
* 不寫入一般 log。  
* 不顯示完整內容。  
* 靜態加密。  
* 傳輸中加密。  
* 使用最小權限。  
* 支援撤銷。  
* 支援輪替。  
* 限制存取角色。  
* 保存存取稽核紀錄。

### **11.4 Key 顯示**

介面只能顯示遮罩值，例如：

abcd••••••••wxyz

不得顯示完整 secret。

---

## **12\. Secret 洩漏處理**

若發現任何 secret 已提交至 Git 或公開位置，必須假設該 secret 已被洩漏。

處理順序：

1. 立即撤銷 secret。  
2. 建立新的最小權限 secret。  
3. 暫停受影響整合。  
4. 檢查存取紀錄。  
5. 檢查異常操作。  
6. 確認是否影響帳戶或資料。  
7. 從目前分支移除 secret。  
8. 視需要清理 Git 歷史。  
9. 通知受影響使用者。  
10. 建立事故紀錄。  
11. 新增 secret scanning 規則。  
12. 新增 regression test。  
13. 完成 root-cause analysis。

只從最新 commit 刪除 secret 並不代表 secret 已安全。

---

## **13\. 個人資料與敏感資料**

TradeGuard 應避免收集不必要的個人資料。

可能的敏感資料包括：

* 電子郵件。  
* 使用者名稱。  
* IP address。  
* 帳戶識別碼。  
* 交易所帳戶資訊。  
* 券商帳戶資訊。  
* 持倉。  
* 成交。  
* 損益。  
* API key metadata。  
* 稽核紀錄。  
* 使用者操作歷史。

安全原則：

* 資料最小化。  
* 用途限制。  
* 最短必要保存期間。  
* 最小權限。  
* 加密。  
* 存取稽核。  
* 支援刪除或匿名化。  
* 避免在 log 中保存敏感資料。  
* 避免在測試中使用真實資料。

---

## **14\. Log 安全**

Log 不得包含：

* API secret。  
* Access token。  
* Refresh token。  
* Session cookie。  
* Authorization header。  
* 密碼。  
* 完整帳戶號碼。  
* 完整交易所 UID。  
* 私人金鑰。  
* Seed phrase。  
* 未遮罩個人資料。  
* 完整 request body 中的敏感欄位。

安全相關 log 應至少包含：

* 事件時間。  
* Actor。  
* Action。  
* Resource。  
* Result。  
* Source IP 或來源識別。  
* Correlation ID。  
* Environment。  
* Failure reason。  
* 風險等級。

Log 必須防止：

* Log injection。  
* Newline injection。  
* 未授權修改。  
* 未授權刪除。  
* 敏感資料洩漏。

---

## **15\. 稽核紀錄**

安全與高風險操作必須寫入 append-only audit log。

最低範圍：

* 登入。  
* 登出。  
* MFA 變更。  
* Session 撤銷。  
* 權限變更。  
* API key 建立、更新、撤銷。  
* 設定變更。  
* 策略版本變更。  
* Promotion 決策。  
* 風險限制變更。  
* 告警處理。  
* 對帳差異處理。  
* 資料集替換。  
* Manifest 變更。  
* 安全事故。  
* 管理員操作。

稽核紀錄不得由一般使用者修改或刪除。

---

## **16\. 認證與 Session**

正式部署時應：

* 使用安全密碼雜湊。  
* 支援 MFA。  
* 使用安全、HttpOnly、SameSite cookie。  
* 啟用 TLS。  
* 限制 session 有效期。  
* 支援 session 撤銷。  
* 登出時失效 session。  
* 高風險操作要求重新驗證。  
* 防止 session fixation。  
* 防止暴力破解。  
* 對異常登入產生告警。

高風險操作例如：

* 修改權限。  
* 修改風險限制。  
* 新增外部帳戶。  
* 新增 API key。  
* 變更環境。  
* 批准 strategy promotion。  
* 匯出敏感資料。

---

## **17\. RBAC**

建議角色：

viewer  
researcher  
operator  
risk\_reviewer  
security\_reviewer  
administrator

角色應採 deny-by-default。

### **Viewer**

可以：

* 查看非敏感 dashboard。  
* 查看已授權研究報告。

不得：

* 修改設定。  
* 匯入憑證。  
* 執行研究。  
* 修改策略。  
* 執行 paper 操作。

### **Researcher**

可以：

* 執行研究。  
* 建立回測。  
* 建立報告。  
* 管理自有策略版本。

不得：

* 修改系統權限。  
* 存取其他使用者 secret。  
* 批准自己的高風險 promotion。  
* 修改平台級風控。

### **Operator**

可以：

* 管理 paper／shadow 工作。  
* 處理非安全告警。  
* 查看對帳狀態。

不得：

* 查看完整 secret。  
* 修改安全角色。  
* 繞過風控。

### **Risk Reviewer**

可以：

* 審查風險。  
* 審查 promotion。  
* 拒絕策略晉級。  
* 暫停高風險研究或監控工作。

不得：

* 直接修改研究結果。  
* 修改稽核紀錄。

### **Security Reviewer**

可以：

* 查看安全事件。  
* 撤銷憑證。  
* 撤銷 session。  
* 審查權限與安全設定。

### **Administrator**

管理員權限必須受到：

* MFA。  
* Step-up authentication。  
* Audit log。  
* 最小必要存取。  
* Session time limit。  
* 定期權限審查。

---

## **18\. 外部服務安全**

所有外部服務 adapter 必須：

* 驗證 TLS。  
* 設定 timeout。  
* 設定有限 retry。  
* 避免無限重試。  
* 驗證回應 schema。  
* 驗證 endpoint。  
* 防止 SSRF。  
* 限制 redirect。  
* 遵守 rate limit。  
* 保存外部 request ID。  
* 不將未知狀態視為成功。  
* 區分 sandbox 與正式 endpoint。  
* 不自動切換到正式 endpoint。

若外部服務回傳未知或不一致狀態，TradeGuard 必須 fail closed。

---

## **19\. Webhook 安全**

若未來支援 webhook，必須：

* 驗證簽章。  
* 驗證時間戳。  
* 防止 replay。  
* 限制 body 大小。  
* 驗證 content type。  
* 驗證 schema。  
* 使用 constant-time signature comparison。  
* 保存 event ID。  
* 實作 idempotency。  
* 拒絕過期事件。  
* 不信任來源 IP 作為唯一驗證。

---

## **20\. 檔案上傳安全**

若支援上傳：

* CSV。  
* Parquet。  
* JSON。  
* Strategy package。  
* Report template。  
* Notebook。

必須：

* 限制檔案大小。  
* 限制副檔名。  
* 驗證實際檔案格式。  
* 防止 path traversal。  
* 防止 zip bomb。  
* 防止 archive traversal。  
* 隔離處理。  
* 不直接執行上傳內容。  
* 不使用不安全反序列化。  
* 掃描惡意內容。  
* 使用隨機伺服器端檔名。  
* 禁止使用使用者提供路徑。  
* 記錄 checksum。  
* 保存來源與上傳者。

禁止直接載入不可信：

pickle  
joblib  
dill  
marshal

除非已建立明確隔離與信任機制。

---

## **21\. 策略程式碼安全**

策略程式碼可能具有等同任意程式碼執行的能力。

第一版應假設：

> 自訂策略程式碼是不可信輸入。

策略執行應考慮：

* Process isolation。  
* Container isolation。  
* Read-only filesystem。  
* No host socket。  
* No Docker socket。  
* No cloud metadata access。  
* No repository secret。  
* No production database credential。  
* Network deny-by-default。  
* CPU limit。  
* Memory limit。  
* Execution timeout。  
* File-size limit。  
* Process-count limit。  
* Restricted temporary directory。  
* Structured output validation。

禁止僅依靠 Python 語言層級 sandbox 宣稱可安全執行任意不可信策略。

若尚未具備可靠隔離，TradeGuard 必須只允許受信任管理者安裝策略。

---

## **22\. 大型語言模型安全**

若 TradeGuard 使用大型語言模型，必須將其視為不可信外部輸入與非確定性元件。

大型語言模型不得：

* 直接存取正式 secret。  
* 直接存取完整帳戶資料。  
* 直接送單。  
* 修改風險限制。  
* 批准 promotion。  
* 執行任意 shell command。  
* 將自然語言內容直接轉為系統命令。  
* 將模型輸出視為權威數值。  
* 自動執行模型產生的程式碼。  
* 將未遮罩 log 傳送至外部模型。

必須防範：

* Prompt injection。  
* Indirect prompt injection。  
* Data exfiltration。  
* Tool abuse。  
* Untrusted document instructions。  
* Model output manipulation。  
* Hallucinated security conclusions。  
* Secret leakage。

任何模型輸出都必須經：

* Schema validation。  
* 權限驗證。  
* 人工審查或確定性程式驗證。  
* 安全邊界檢查。

---

## **23\. Dependency 安全**

所有依賴必須：

* 使用 lockfile。  
* 使用可信套件來源。  
* 審查授權。  
* 執行 dependency scanning。  
* 避免未維護套件。  
* 避免不必要依賴。  
* 優先固定版本。  
* 記錄新增理由。  
* 審查 transitive dependencies。  
* 定期更新。

依賴漏洞處理應評估：

* TradeGuard 是否實際使用受影響程式路徑。  
* 是否可從外部到達。  
* 是否需要特定設定。  
* 是否已有緩解措施。  
* 升級是否造成相容性風險。

不得只為消除掃描警告而盲目升級高風險依賴。

---

## **24\. GitHub Actions 安全**

GitHub Actions workflow 必須：

* 使用最小 `permissions`。  
* 預設 `contents: read`。  
* 只在必要工作授予寫入權限。  
* 不讓不可信 Pull Request 存取 secret。  
* 避免對 fork PR 使用高權限 `pull_request_target`。  
* 固定第三方 Action 至完整 commit SHA。  
* 審查第三方 Action。  
* 不輸出 secret。  
* 不執行未驗證的 PR 內容與高權限 secret 組合。  
* 保護 release workflow。  
* 保存建置 provenance。  
* 驗證 artifact checksum。

禁止將 Docker socket 或雲端正式憑證提供給不可信 PR 工作。

---

## **25\. Container 安全**

Container 應：

* 使用最小基底映像。  
* 固定 image digest。  
* 使用非 root 使用者。  
* 使用 read-only filesystem。  
* 移除不必要套件。  
* 不包含 secret。  
* 不包含 Git credential。  
* 設定 resource limit。  
* 限制 Linux capabilities。  
* 啟用 `no-new-privileges`。  
* 執行 image scan。  
* 產生 SBOM。  
* 驗證部署 image digest。

不得將 Docker socket 掛載給一般應用程式容器。

---

## **26\. Database 安全**

資料庫必須：

* 不公開暴露至網際網路。  
* 使用獨立應用帳戶。  
* 使用最小權限。  
* 加密連線。  
* 加密備份。  
* 定期備份。  
* 測試還原。  
* 記錄管理操作。  
* 限制 production migration 權限。  
* 使用 parameterized query。  
* 保護 audit table。  
* 隔離不同環境。

研究、測試與正式監控環境不得共用相同資料庫帳戶。

---

## **27\. 備份安全**

備份必須：

* 加密。  
* 有存取控制。  
* 有保存期限。  
* 有完整性驗證。  
* 有刪除政策。  
* 定期測試還原。  
* 不包含不必要 secret。  
* 與主要系統故障域分離。  
* 記錄建立與還原操作。

備份成功不代表系統可恢復。必須定期執行 restore test。

---

## **28\. 安全設定**

安全相關設定必須：

* 版本化。  
* Schema 驗證。  
* Fail closed。  
* 不使用危險預設值。  
* 支援 redaction。  
* 產生 deterministic hash。  
* 記錄變更者。  
* 記錄變更原因。  
* 記錄生效時間。  
* 保存 audit event。  
* 支援 rollback。

下列設定不得由一般使用者修改：

* 認證模式。  
* Session policy。  
* Secret storage。  
* RBAC。  
* Audit retention。  
* Security logging。  
* 外部 endpoint allowlist。  
* Strategy execution isolation。  
* 允許的 API key 權限。  
* Environment boundary。

---

## **29\. 安全標頭**

Web 部署應考慮：

* Content-Security-Policy。  
* Strict-Transport-Security。  
* X-Content-Type-Options。  
* Referrer-Policy。  
* Permissions-Policy。  
* Frame-ancestors。  
* Secure cookies。  
* HttpOnly cookies。  
* SameSite cookies。

CSP 不應依賴廣泛的：

unsafe-inline  
unsafe-eval

除非已有書面理由與替代控制。

---

## **30\. Rate Limiting**

下列端點應具有 rate limit：

* 登入。  
* 密碼重設。  
* MFA 驗證。  
* API key 驗證。  
* 檔案上傳。  
* 報告產生。  
* 高成本回測。  
* 外部資料抓取。  
* 搜尋。  
* 匯出。  
* 管理操作。

Rate limit 必須避免：

* 使用單一可偽造 header 作為唯一識別。  
* 讓攻擊者藉由耗盡配額鎖定其他使用者。  
* 回傳敏感帳戶是否存在。

---

## **31\. 錯誤處理**

錯誤回應不得暴露：

* Stack trace。  
* Database schema。  
* Secret。  
* Internal path。  
* Cloud metadata。  
* Dependency credential。  
* 完整外部 API 回應。  
* 使用者敏感資料。

錯誤必須：

* 提供 correlation ID。  
* 區分使用者錯誤與系統錯誤。  
* 在伺服器端保留足夠診斷資料。  
* 對未知安全狀態 fail closed。  
* 不將 exception 靜默吞掉。

---

## **32\. 環境隔離**

至少應區分：

development  
test  
research  
paper  
shadow

不同環境必須：

* 使用不同憑證。  
* 使用不同資料庫。  
* 使用不同 secret。  
* 使用不同 endpoint。  
* 使用清楚環境標示。  
* 防止設定誤用。  
* 防止 shadow 連接正式交易權限。  
* 防止 development 讀取正式資料。

任何環境不明確時，系統必須拒絕啟動。

---

## **33\. 安全事件**

安全事件包括但不限於：

* Secret 外洩。  
* 帳戶接管。  
* 未授權資料存取。  
* 未授權設定變更。  
* 未授權策略執行。  
* 權限提升。  
* 供應鏈攻擊。  
* 惡意 dependency。  
* Audit log 損壞。  
* Backup 外洩。  
* Repository 被入侵。  
* Release artifact 被竄改。  
* 系統出現正式交易能力。  
* 不可信策略逃逸隔離。  
* Paper 或 shadow 被誤標。  
* 研究資料遭惡意修改。

---

## **34\. 事故處理流程**

發現安全事故後，應依序執行：

### **34.1 Containment**

1. 停用受影響服務。  
2. 撤銷受影響 session。  
3. 撤銷受影響 API key。  
4. 封鎖惡意來源。  
5. 暫停受影響 adapter。  
6. 停止受影響策略工作。  
7. 禁止新的 promotion。  
8. 保持證據完整。

### **34.2 Investigation**

1. 建立事故編號。  
2. 記錄事故時間線。  
3. 保存 log。  
4. 保存 audit events。  
5. 保存設定與 hash。  
6. 保存 container digest。  
7. 保存 deployment version。  
8. 保存外部 request ID。  
9. 確認受影響使用者。  
10. 確認受影響資料。  
11. 確認是否涉及帳戶。  
12. 確認是否涉及交易能力。

### **34.3 Eradication**

1. 修復 root cause。  
2. 移除惡意程式。  
3. 更新依賴。  
4. 輪替 secret。  
5. 修正權限。  
6. 修正設定。  
7. 新增偵測規則。  
8. 新增 regression test。

### **34.4 Recovery**

1. 從可信版本重新部署。  
2. 驗證 artifact。  
3. 驗證資料完整性。  
4. 驗證 audit log。  
5. 驗證權限。  
6. 驗證 secret。  
7. 重新執行安全測試。  
8. 逐步恢復服務。  
9. 加強監控。

### **34.5 Post-incident**

1. 完成 root-cause analysis。  
2. 完成影響評估。  
3. 記錄控制失效。  
4. 更新 runbook。  
5. 更新 threat model。  
6. 更新測試。  
7. 更新告警。  
8. 通知受影響使用者。  
9. 協調漏洞揭露。  
10. 追蹤改善項目。

禁止為美化事故影響而刪除證據或修改紀錄。

---

## **35\. 安全修正**

安全修正應：

* 使用私人分支或私人 fork。  
* 限制知道漏洞細節的人員。  
* 新增最小重現測試。  
* 新增 regression test。  
* 評估 backward compatibility。  
* 評估資料 migration。  
* 評估 secret rotation。  
* 評估是否需要通知使用者。  
* 評估是否需要發布 CVE。  
* 產生可驗證 release artifact。  
* 提供升級與緩解說明。

安全修正不得：

* 僅隱藏錯誤訊息。  
* 僅在前端加入檢查。  
* 僅增加警告。  
* 將 fail-closed 改為 fail-open。  
* 刪除失敗測試。  
* 降低權限驗證。  
* 偽造測試結果。

---

## **36\. 安全公告**

安全公告應包含：

* 漏洞摘要。  
* 受影響版本。  
* 不受影響版本。  
* 嚴重程度。  
* 攻擊前置條件。  
* 可能影響。  
* 修正版本。  
* 升級方式。  
* 暫時緩解措施。  
* Secret 是否需要輪替。  
* 資料是否可能外洩。  
* Credit。  
* 揭露時間線。

公告不得包含：

* 未撤銷 secret。  
* 真實使用者資料。  
* 不必要的完整 exploit。  
* 可識別受害者的資訊。

---

## **37\. 漏洞揭露與 Credit**

在符合下列條件時，維護者可以公開感謝安全研究者：

* 回報為首次有效回報。  
* 回報內容完整。  
* 遵守負責任揭露。  
* 未造成不必要損害。  
* 研究者同意公開名稱。

研究者可以選擇：

* 使用真實姓名。  
* 使用暱稱。  
* 使用組織名稱。  
* 保持匿名。

未經研究者同意，不應公開其身份。

---

## **38\. Bug Bounty**

目前 TradeGuard 沒有正式 bug bounty 計畫。

NO BUG BOUNTY PROGRAM

提交漏洞不代表一定能獲得：

* 金錢獎勵。  
* 禮品。  
* 報酬。  
* 工作機會。  
* 公開 credit。

若未來建立 bug bounty，將另行更新本文件。

---

## **39\. Safe Harbor**

在適用法律允許範圍內，如果安全研究者：

* 善意進行研究。  
* 遵守本政策。  
* 只測試自有環境或獲授權環境。  
* 不存取他人資料。  
* 不造成服務中斷。  
* 不執行真實交易。  
* 不嘗試提款或資產轉移。  
* 不公開未修復漏洞。  
* 立即回報意外取得的敏感資料。  
* 在確認漏洞後停止進一步擴大影響。

本專案維護者原則上不會因符合本政策的善意安全研究而主動採取法律行動。

此 safe harbor：

* 不構成法律契約。  
* 不代表第三方同意。  
* 不涵蓋交易所、券商、雲端供應商或其他服務。  
* 不授權違反當地法律。  
* 不授權存取非自有帳戶。  
* 不授權破壞性測試。

---

## **40\. 第三方漏洞**

若漏洞位於：

* 交易所。  
* 券商。  
* 市場資料供應商。  
* 雲端平台。  
* 作業系統。  
* 第三方套件。  
* 外部身份驗證服務。

請優先遵循該第三方的安全回報政策。

若該漏洞會直接影響 TradeGuard，仍可通知本專案維護者，但不要提供：

* 第三方真實 secret。  
* 非自有帳戶資料。  
* 未授權取得的資料。  
* 可能違反第三方政策的內容。

---

## **41\. Security Checklist**

開發者提交安全相關變更前，應確認：

\- \[ \] 無真實 secret  
\- \[ \] 無高權限 API key  
\- \[ \] 無正式交易權限  
\- \[ \] 無提款或轉帳能力  
\- \[ \] 採用最小權限  
\- \[ \] 權限檢查位於後端  
\- \[ \] 敏感資料已遮罩  
\- \[ \] Log 不含 secret  
\- \[ \] 外部輸入已驗證  
\- \[ \] SQL 使用參數化查詢  
\- \[ \] 無不安全反序列化  
\- \[ \] 無任意程式碼執行  
\- \[ \] 無 path traversal  
\- \[ \] 無 SSRF  
\- \[ \] 無 XSS  
\- \[ \] 無 CSRF  
\- \[ \] Session 安全  
\- \[ \] Rate limit 適當  
\- \[ \] Audit log 已更新  
\- \[ \] Fail-closed 行為已測試  
\- \[ \] Security regression test 已新增  
\- \[ \] Dependency scan 通過  
\- \[ \] Secret scan 通過  
\- \[ \] Container scan 通過  
\- \[ \] 已提供 rollback plan  
\- \[ \] 已列出 known limitations

---

## **42\. 維護者安全檢查**

維護者應定期檢查：

* Repository 權限。  
* Branch protection。  
* CODEOWNERS。  
* GitHub Actions permissions。  
* Repository secrets。  
* Dependabot 或等效工具。  
* Secret scanning。  
* Dependency scanning。  
* Container scanning。  
* 未使用帳戶。  
* 未使用 API key。  
* 過期 session。  
* 管理員權限。  
* Backup restore。  
* Audit log 完整性。  
* Security contact 是否有效。  
* SECURITY.md 是否仍符合實際系統。

---

## **43\. 安全文件更新**

下列變更發生時，必須重新審查本文件：

* 新增正式使用者帳戶。  
* 新增 MFA。  
* 新增外部 API key。  
* 新增 read-only 帳戶整合。  
* 新增 paper adapter。  
* 新增 shadow monitoring。  
* 新增策略 plugin。  
* 新增檔案上傳。  
* 新增大型語言模型功能。  
* 新增雲端部署。  
* 新增多租戶。  
* 新增付款功能。  
* 新增正式交易能力。  
* 改變資料保存政策。  
* 改變授權。  
* 發生重大安全事故。

---

## **44\. 未來正式交易的要求**

若未來提議加入：

canary  
live

不得只修改設定即可啟用。

至少必須先完成：

* 獨立 RFC。  
* Threat model。  
* 法律與法規審查。  
* 正式交易責任邊界。  
* 獨立風險引擎。  
* 多人核准。  
* MFA。  
* Step-up authentication。  
* Kill switch。  
* 憑證保管。  
* IP allowlist。  
* Order idempotency。  
* 外部對帳。  
* Unknown-order handling。  
* Disaster recovery。  
* Incident response。  
* Security penetration test。  
* 第三方安全審查。  
* Canary capital limit。  
* 人工 promotion。  
* 正式交易專用 SECURITY.md 更新。

在上述條件完成前，任何正式下單路徑都應視為安全缺陷。

---

## **45\. 聯絡資訊**

安全回報：

請使用 GitHub 的私密漏洞回報：

https://github.com/EngelN9/TradeGuard/security/advisories/new

如果該功能暫時不可用，請勿建立包含漏洞細節的公開 Issue。維護者必須先
恢復私密回報管道，再接收可利用細節或敏感資料。

一般問題請使用 GitHub Issues，但請勿在公開 Issue 張貼漏洞細節或敏感資料。

Repository：

https://github.com/EngelN9/TradeGuard

---

## **46\. 最終安全原則**

TradeGuard 的安全目標不只是防止系統被入侵。

TradeGuard 還必須防止：

* 使用者被錯誤研究結果誤導。  
* 回測證據遭竄改。  
* 模擬結果被描述為真實績效。  
* 策略繞過風險限制。  
* 未授權帳戶資料被存取。  
* 不可信程式碼接觸 secret。  
* Shadow 系統意外取得交易權限。  
* AI 代理自行建立高風險功能。  
* 安全事故被隱藏或刪除。

當系統狀態、資料完整性、權限或外部帳戶狀態無法確認時：

> TradeGuard 必須停止高風險操作、保存證據並 fail closed，而不是猜測系統仍然安全。
