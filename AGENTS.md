# **AGENTS.md — TradeGuard 安全研究、監控與策略驗證規格**

> 本文件是 TradeGuard 儲存庫對 AI 程式設計代理、人類開發者、研究員與維運人員的最高層級工程規格。

> 除非子目錄存在範圍更窄且要求更嚴格的 `AGENTS.md`，否則本文件適用於整個儲存庫。

> TradeGuard 的使命是協助使用者安全地研究、監控、比較與驗證既有股票及加密貨幣交易策略。TradeGuard 不保證獲利、不構成投資建議，也不得將回測績效描述為未來報酬的承諾。

---

## **0\. 規範用語**

本文件中的關鍵詞依下列強度解讀：

* **MUST／必須**：不可違反。  
* **MUST NOT／禁止**：不可執行。  
* **SHOULD／應該**：除非有明確、可審查且已記錄的理由，否則必須遵循。  
* **SHOULD NOT／不應**：除非有明確、可審查且已記錄的理由，否則不得採用。  
* **MAY／可以**：可選實作。  
* **FAIL CLOSED／失敗關閉**：狀態不明、資料不足或驗證失敗時，停止產生新的風險建議或自動動作。  
* **POINT-IN-TIME／時間點一致**：研究資料只能使用該歷史時間點實際可取得的資訊。  
* **PROMOTION／晉級**：策略由研究、回測、模擬或影子階段移至下一個更接近真實市場的階段。

當「提高績效」與下列目標衝突時，永遠優先下列目標：

1. 正確性。  
2. 資料完整性。  
3. 可重現性。  
4. 資訊安全。  
5. 法令遵循。  
6. 風險限制。  
7. 可稽核性。  
8. 使用者資產安全。

---

## **1\. 專案使命**

TradeGuard 是一個面向個人量化研究者、小型交易團隊與策略開發者的策略研究與風險監控平台。

TradeGuard 統一支援：

1. 股票與加密貨幣歷史資料匯入。  
2. 資料品質檢查與時間點一致性驗證。  
3. 既有策略的標準化接入。  
4. 確定性回測。  
5. Walk-forward analysis。  
6. 樣本外驗證。  
7. 交易成本與滑價壓力測試。  
8. Look-ahead bias 與資料洩漏偵測。  
9. 參數穩健性與過度擬合分析。  
10. Paper trading 與 shadow monitoring。  
11. 策略、投資組合及帳戶風險監控。  
12. 實際績效與回測預期偏差分析。  
13. 可重現研究報告。  
14. 版本化策略與研究結果比較。  
15. 告警、稽核紀錄與事故調查。

TradeGuard 的核心價值不是「預測市場」，而是：

> 讓使用者知道一個策略的績效是否可信、風險是否可接受、實際運作是否偏離研究假設。

---

## **2\. 產品責任邊界**

### **2.1 TradeGuard 是什麼**

TradeGuard 是：

* 策略研究平台。  
* 回測與驗證平台。  
* 策略風險監控平台。  
* Paper／shadow 環境觀測平台。  
* 策略版本與績效比較平台。  
* 交易營運稽核工具。  
* 既有交易引擎的安全監控層。  
* 可重現量化研究工作台。

### **2.2 TradeGuard 不是什麼**

第一版 TradeGuard 不是：

* 保證獲利的交易機器人。  
* 代客操盤服務。  
* 投資顧問服務。  
* 跟單平台。  
* 訊號販售平台。  
* 資產保管平台。  
* 交易所。  
* 券商。  
* 高頻交易平台。  
* 超低延遲執行引擎。  
* 自動管理客戶資金的系統。  
* 由大型語言模型直接決定買賣的系統。  
* 未經使用者確認即可正式下單的系統。

### **2.3 預設禁止正式交易**

TradeGuard 的預設執行模式必須為：

research

第一版允許的環境：

research  
backtest  
replay  
paper  
shadow

下列環境預設不存在或必須完全停用：

canary  
live

任何 AI 代理不得自行新增、啟用或模擬正式下單能力。

---

## **3\. 核心安全原則**

### **3.1 不保證獲利**

所有文件、介面與報告必須明確區分：

* 歷史績效。  
* 模擬績效。  
* Paper trading 績效。  
* Shadow 績效。  
* 真實交易績效。

禁止使用下列類型的描述：

* 穩賺。  
* 保證獲利。  
* 無風險。  
* 必勝策略。  
* 穩定月收益。  
* AI 自動替你賺錢。  
* 高勝率等於高報酬。  
* 回測成功即可直接實盤。

### **3.2 策略不得繞過風險層**

所有策略輸出只能形成：

Signal  
TargetPosition  
TradeProposal

策略模組禁止直接：

* 呼叫券商或交易所下單 API。  
* 存取正式交易憑證。  
* 送出正式訂單。  
* 修改帳戶權限。  
* 提款。  
* 轉帳。  
* 取消平台級風控。  
* 修改不可變稽核紀錄。

### **3.3 不確定狀態必須停止**

出現下列任一情況時，系統必須停止產生新的交易建議或風險增加建議：

* 市場資料過期。  
* 資料來源互相矛盾。  
* 時區無法確認。  
* 股票交易時段無法確認。  
* 公司行動資料缺失。  
* 加密貨幣交易對規格未知。  
* 費率資料缺失。  
* 風控設定驗證失敗。  
* 策略版本無法辨識。  
* 帳戶或持倉狀態無法對帳。  
* 回測資料 manifest 不完整。  
* 研究執行環境無法重現。

### **3.4 研究結果必須可重現**

每一次研究、回測、重播與驗證執行都必須保存：

* `run_id`  
* 策略名稱。  
* 策略版本。  
* Git commit SHA。  
* 設定檔版本。  
* 設定檔 hash。  
* 資料集版本。  
* 資料 manifest。  
* 資料時間範圍。  
* universe 定義。  
* 隨機種子。  
* 套件 lockfile。  
* Python 版本。  
* 作業系統與容器資訊。  
* 成本模型版本。  
* 滑價模型版本。  
* 結果摘要。  
* 警告與驗證失敗項目。

相同輸入、相同版本及相同設定，必須得到一致結果，除非文件明確指出非確定性來源。

---

## **4\. 支援市場**

TradeGuard 長期支援兩類市場：

1. 股票現貨。  
2. 加密貨幣現貨。

兩類市場可以共享研究與監控框架，但禁止假設市場微結構相同。

### **4.1 股票市場**

股票模組必須處理：

* 交易所時區。  
* 交易日曆。  
* 休市。  
* 半日市。  
* 盤前與盤後。  
* 開盤與收盤集合競價。  
* 暫停交易。  
* 漲跌幅限制。  
* 股票分割。  
* 反向分割。  
* 現金股利。  
* 股票股利。  
* 增資。  
* 減資。  
* 合併。  
* 分拆。  
* 代號變更。  
* 下市。  
* ETF 成分變動。  
* Survivorship bias。  
* Point-in-time universe。  
* Lot size。  
* Tick size。  
* 交易稅。  
* 手續費。  
* 借券與放空限制。

第一版股票功能應優先支援：

* 高流動性 ETF。  
* 大型股。  
* Long-only。  
* Cash-only。  
* 日線或分鐘級研究。  
* Paper／shadow monitoring。

### **4.2 加密貨幣市場**

加密貨幣模組必須處理：

* 24/7 交易。  
* 交易所維護。  
* REST 與 WebSocket 差異。  
* 交易對 precision。  
* Tick size。  
* Step size。  
* Minimum quantity。  
* Minimum notional。  
* Maker／taker fee。  
* Funding 資料的存在與否。  
* Stablecoin 脫鉤。  
* Quote asset 風險。  
* 交易所集中風險。  
* 流動性急遽下降。  
* 交易所 API 語意漂移。  
* Rate limit。  
* 交易對下架。  
* 鏈上暫停充值或提款。  
* Venue insolvency risk。  
* 24 小時不中斷資料缺口。

第一版加密貨幣功能應優先支援：

* 高流動性現貨交易對。  
* Long／flat。  
* 無槓桿。  
* 無借貸。  
* 無期貨。  
* 無永續合約。  
* 無選擇權。  
* Paper／shadow monitoring。

### **4.3 禁止直接跨市場共用的內容**

股票與加密貨幣禁止無條件共用：

* 年化因子。  
* 交易時段邏輯。  
* 缺口處理方式。  
* 成本模型。  
* 滑價模型。  
* Fill 模型。  
* 最小下單單位。  
* 精度規則。  
* 波動率門檻。  
* 流動性門檻。  
* 風險預算。  
* 再平衡頻率。  
* 策略參數。  
* Benchmark。  
* Corporate action 邏輯。  
* Stablecoin 風險邏輯。

任何策略從股票移植至加密貨幣，或從加密貨幣移植至股票，都必須建立：

* 新策略版本。  
* 新市場設定。  
* 新成本模型。  
* 新研究報告。  
* 新樣本外驗證。  
* 新 promotion record。

禁止只替換 symbol 後宣稱策略適用於另一市場。

---

## **5\. 建議系統架構**

TradeGuard 應優先採用模組化單體，避免第一版過早拆分為複雜微服務。

建議邏輯架構：

資料來源  
  ↓  
資料擷取與標準化  
  ↓  
資料品質閘門  
  ↓  
Point-in-time 資料集  
  ↓  
策略介面與策略執行器  
  ↓  
確定性回測／Replay  
  ↓  
成本、成交與風險模型  
  ↓  
驗證與壓力測試  
  ↓  
Paper／Shadow 監控  
  ↓  
報告、告警與 Web 儀表板

建議部署平面：

Research Plane  
\- Historical data  
\- Backtesting  
\- Validation  
\- Experiment tracking  
\- Report generation

Monitoring Plane  
\- Paper/shadow event ingestion  
\- Position and exposure monitoring  
\- Health checks  
\- Alerts  
\- Reconciliation

Control Plane  
\- Configuration review  
\- Strategy version management  
\- Read-only dashboards  
\- Controlled paper/shadow actions  
\- Audit log

TradeGuard 不應讓瀏覽器成為研究或監控工作的唯一執行環境。長時間工作必須由後端程序執行。

---

## **6\. 建議技術基線**

除非 ADR 明確批准其他方案，第一版建議採用：

### **6.1 後端**

* Python 3.12 或以上。  
* FastAPI。  
* Pydantic。  
* SQLAlchemy。  
* Alembic。  
* PostgreSQL。  
* Polars 或 Pandas。  
* NumPy。  
* SciPy。  
* PyArrow。  
* DuckDB。  
* Redis 僅在有明確需求時使用。  
* Celery、Dramatiq 或其他工作佇列必須經 ADR 決定。

### **6.2 前端**

* TypeScript。  
* React。  
* Next.js。  
* OpenAPI 產生型別。  
* Responsive Web UI。  
* 圖表元件不得偷偷重新計算後端風控結果。

### **6.3 工程品質**

* `uv` 或其他可重現 dependency lock。  
* `ruff`  
* `mypy` 或 `pyright`  
* `pytest`  
* `hypothesis`  
* `pre-commit`  
* Docker  
* Docker Compose  
* GitHub Actions  
* Secret scanning  
* Dependency scanning  
* Container scanning

### **6.4 數值規則**

下列資料不得使用二進位浮點數作為權威持久化表示：

* 金額。  
* 價格。  
* 數量。  
* 手續費。  
* 稅。  
* 名目曝險。  
* 帳戶餘額。

權威計算與持久化應使用：

decimal.Decimal

統計、最佳化及矩陣運算可以使用浮點數，但輸入輸出邊界必須經明確轉換、容差驗證及文件說明。

---

## **7\. 建議儲存庫結構**

tradeguard/  
├── AGENTS.md  
├── README.md  
├── LICENSE  
├── SECURITY.md  
├── CONTRIBUTING.md  
├── CODEOWNERS  
├── pyproject.toml  
├── uv.lock  
├── Makefile  
├── docker-compose.yml  
├── .env.example  
├── .gitignore  
├── configs/  
│   ├── base.yaml  
│   ├── research.yaml  
│   ├── backtest.yaml  
│   ├── replay.yaml  
│   ├── paper.yaml  
│   ├── shadow.yaml  
│   ├── markets/  
│   │   ├── crypto\_spot.yaml  
│   │   └── equities\_cash.yaml  
│   ├── costs/  
│   ├── risk/  
│   └── strategies/  
├── src/  
│   └── tradeguard/  
│       ├── api/  
│       ├── audit/  
│       ├── backtest/  
│       ├── cli/  
│       ├── config/  
│       ├── costs/  
│       ├── data/  
│       ├── domain/  
│       ├── execution\_models/  
│       ├── experiments/  
│       ├── features/  
│       ├── markets/  
│       │   ├── crypto/  
│       │   └── equities/  
│       ├── monitoring/  
│       ├── portfolio/  
│       ├── reconciliation/  
│       ├── reports/  
│       ├── risk/  
│       ├── strategies/  
│       ├── validation/  
│       └── workers/  
├── web/  
│   ├── app/  
│   ├── components/  
│   ├── lib/  
│   └── tests/  
├── tests/  
│   ├── unit/  
│   ├── integration/  
│   ├── property/  
│   ├── replay/  
│   ├── regression/  
│   ├── contract/  
│   ├── e2e/  
│   └── fixtures/  
├── docs/  
│   ├── architecture/  
│   ├── adr/  
│   ├── data/  
│   ├── research/  
│   ├── risk/  
│   ├── operations/  
│   └── strategies/  
├── scripts/  
└── reports/

`reports/` 不得提交包含敏感帳戶資料、正式交易憑證或不可公開市場資料授權內容的檔案。

---

## **8\. 領域事件模型**

核心事件應採不可變、版本化模型。

所有事件至少必須包含：

event\_id  
schema\_version  
event\_type  
source  
asset\_class  
venue  
symbol  
event\_time\_utc  
ingest\_time\_utc  
sequence\_number  
correlation\_id  
causation\_id  
run\_id  
payload\_checksum

建議核心事件：

Quote  
TradeTick  
Bar  
CorporateAction  
InstrumentMetadataChanged  
MarketSessionChanged  
DataQualityAlert  
FeatureSnapshot  
Signal  
TargetPosition  
TradeProposal  
RiskDecision  
BacktestStarted  
BacktestCompleted  
ValidationStarted  
ValidationCompleted  
PaperOrderObserved  
PaperFillObserved  
ShadowDecisionObserved  
PositionSnapshot  
AccountSnapshot  
PnLSnapshot  
ExposureSnapshot  
ReconciliationDifference  
StrategyDriftAlert  
DataDriftAlert  
ModelDriftAlert  
HealthStatusChanged  
ConfigurationChanged  
AuditEvent

所有時間戳記必須：

* 使用 timezone-aware datetime。  
* 內部統一為 UTC。  
* 顯示層可以依使用者時區轉換。  
* 禁止使用無時區 datetime。

---

## **9\. 資料治理**

### **9.1 原始資料不可變**

原始市場資料必須以 append-only 或內容定址方式保存。

禁止：

* 為改善績效而修改歷史資料。  
* 無紀錄地覆寫原始資料。  
* 刪除造成不利回測結果的資料區間。  
* 將修正後資料冒充原始資料。  
* 混合不同供應商資料而不記錄來源。

每批資料必須保存：

* 來源。  
* 擷取時間。  
* 資料時間範圍。  
* schema version。  
* checksum。  
* 壓縮格式。  
* 筆數。  
* 缺失區間。  
* 重複筆數。  
* 修正紀錄。  
* 授權與使用限制。

### **9.2 資料品質檢查**

最低檢查項目：

* 缺失資料。  
* 重複資料。  
* 時間戳逆序。  
* 未來時間戳。  
* 異常價格。  
* 負價格。  
* 負成交量。  
* OHLC 關係錯誤。  
* Bid 大於 ask。  
* 價格跳動超出合理範圍。  
* 不合理 spread。  
* 交易時段外資料。  
* 股票公司行動未調整。  
* Symbol mapping 衝突。  
* 交易對 precision 衝突。  
* 多來源資料不一致。  
* 資料延遲。  
* 資料時間戳新鮮但內容過期。

### **9.3 Point-in-time 規則**

研究中禁止使用：

* 未來財報。  
* 未來成分股名單。  
* 未來下市資訊。  
* 未來公司行動。  
* 未來評級修正。  
* 回測結束後才可得的 metadata。  
* 以今天仍存在的股票清單回測過去市場。  
* 事後修正但未保留發布時間的經濟資料。

所有基本面、公司行動及 universe 資料都應包含：

effective\_at  
known\_at  
ingested\_at

---

## **10\. 策略介面**

TradeGuard 主要驗證既有策略，而不是強制使用單一策略框架。

策略 adapter 必須將外部策略轉換為統一介面。

建議介面：

class StrategyProtocol(Protocol):  
    strategy\_id: str  
    strategy\_version: str  
    supported\_asset\_classes: set\[str\]  
    required\_data: tuple\[str, ...\]

    def initialize(self, context: StrategyContext) \-\> None:  
        ...

    def on\_event(self, event: MarketEvent) \-\> list\[Signal\]:  
        ...

    def finalize(self) \-\> StrategySummary:  
        ...

策略禁止：

* 直接讀取未宣告資料。  
* 存取未來資料。  
* 直接修改市場事件。  
* 使用全域可變狀態而不保存。  
* 隱藏隨機種子。  
* 在回測與 paper 環境使用不同邏輯而不揭露。  
* 靜默下載外部資料。  
* 靜默呼叫大型語言模型。  
* 靜默改寫參數。  
* 直接呼叫交易 API。

策略必須宣告：

* 需要的資料頻率。  
* 支援市場。  
* 支援標的類型。  
* 暖機期。  
* 最大持倉週期。  
* 預期換手率。  
* 參數 schema。  
* 風險假設。  
* 成本假設。  
* 不適用情境。  
* 已知限制。

---

## **11\. 回測引擎要求**

### **11.1 確定性**

回測必須保證：

* 相同資料。  
* 相同策略版本。  
* 相同設定。  
* 相同種子。  
* 相同成本模型。  
* 相同執行模型。

應得到相同結果。

### **11.2 禁止偷看未來**

回測必須防止：

* Look-ahead bias。  
* Label leakage。  
* Feature leakage。  
* Corporate-action leakage。  
* Future universe leakage。  
* 使用當根 bar 收盤價產生訊號並以同一收盤價成交。  
* 以日內最高最低價假設理想成交。  
* 在事件到達前使用其內容。

### **11.3 成交模型**

成交模型至少應支援：

* Market order。  
* Limit order。  
* Partial fill。  
* Non-fill。  
* Queue uncertainty。  
* Spread。  
* Commission。  
* Tax。  
* Slippage。  
* Market impact。  
* Latency。  
* Minimum notional。  
* Tick size。  
* Step size。  
* Trading halt。  
* Venue maintenance。  
* Rejected order。

預設成交模型必須保守，禁止假設所有訂單都能以理想價格全部成交。

### **11.4 成本模型**

每份回測報告必須清楚列出：

* 手續費。  
* 交易稅。  
* Spread。  
* Slippage。  
* Market impact。  
* 借券成本。  
* Funding cost。  
* 資金成本。  
* 匯率成本。  
* 資料中未建模的成本。

成本未完整建模時，報告必須顯示明顯警告。

---

## **12\. 策略驗證標準**

每個策略至少必須經過下列驗證。

### **12.1 基準比較**

至少比較：

* Cash。  
* Buy and hold。  
* 市場 benchmark。  
* 等權重組合。  
* 簡單動能 baseline。  
* 簡單均值回歸 baseline。  
* 原策略上一版本。

禁止只展示策略本身而不展示基準。

### **12.2 樣本切分**

必須區分：

* Training。  
* Validation。  
* Test。  
* Out-of-sample。  
* Live-like paper／shadow。

禁止在測試集上反覆調參後仍將其稱為樣本外結果。

### **12.3 Walk-forward**

Walk-forward analysis 必須記錄：

* 訓練區間。  
* 驗證區間。  
* 測試區間。  
* Refit 頻率。  
* 參數選擇規則。  
* 每次切分績效。  
* 聚合績效。  
* 失敗切分。  
* 市場 regime。

### **12.4 穩健性測試**

最低測試：

* 參數擾動。  
* 起始日期擾動。  
* 結束日期擾動。  
* 標的 universe 擾動。  
* 成本增加。  
* 滑價增加。  
* 訊號延遲。  
* 成交延遲。  
* 資料缺口。  
* 隨機漏單。  
* Partial fill。  
* 極端行情。  
* 流動性下降。  
* 不同市場 regime。  
* 不同供應商資料。

### **12.5 過度擬合檢查**

應支援：

* 多重假設檢定警告。  
* Parameter search budget。  
* Experiment count。  
* Deflated Sharpe Ratio。  
* Probability of Backtest Overfitting。  
* Bootstrap。  
* Block bootstrap。  
* Combinatorial purged cross-validation。  
* Purging。  
* Embargo。  
* White’s Reality Check 或同類方法。  
* Strategy complexity penalty。

任何統計檢定必須說明假設、適用條件及限制。

### **12.6 最低報告指標**

每份策略報告至少包含：

* 累積報酬。  
* 年化報酬。  
* 年化波動率。  
* Sharpe ratio。  
* Sortino ratio。  
* Calmar ratio。  
* 最大回撤。  
* 回撤持續時間。  
* Value at Risk。  
* Expected Shortfall。  
* 勝率。  
* Profit factor。  
* 平均獲利。  
* 平均虧損。  
* Payoff ratio。  
* Turnover。  
* 交易次數。  
* 平均持有期間。  
* Exposure。  
* Concentration。  
* 成本前績效。  
* 成本後績效。  
* Benchmark-relative return。  
* Beta。  
* Alpha。  
* Tail behavior。  
* 最差日、週、月。  
* 連續虧損期間。  
* Regime 分解。  
* 標的貢獻。  
* 時間區間貢獻。

禁止只以勝率判斷策略品質。

---

## **13\. 風險管理**

### **13.1 風險引擎獨立性**

風險引擎必須獨立於策略。

策略只能提出目標或建議，風險引擎負責判斷：

* 接受。  
* 調整。  
* 拒絕。  
* 暫停。  
* 要求人工審查。

### **13.2 Pre-trade 研究風控**

即使在 paper 或 shadow 模式，也應檢查：

* 單一標的曝險。  
* 單一產業曝險。  
* 單一主題曝險。  
* 單一交易所曝險。  
* 單一 quote asset 曝險。  
* Gross exposure。  
* Net exposure。  
* 槓桿。  
* 流動性。  
* Participation rate。  
* 預估 market impact。  
* 最大訂單金額。  
* 最大日換手率。  
* 最大策略資本。  
* 最大單筆風險。  
* Drawdown gate。  
* Stale data gate。  
* Market session gate。

### **13.3 投資組合風險**

應支援：

* 波動率目標。  
* Covariance estimation。  
* Shrinkage covariance。  
* Correlation monitoring。  
* Factor exposure。  
* Sector exposure。  
* Cluster exposure。  
* Concentration limits。  
* Drawdown scaling。  
* Stress testing。  
* Scenario analysis。  
* Liquidity-adjusted risk。  
* Venue risk。  
* Stablecoin risk。  
* Currency risk。

### **13.4 風險指標限制**

風險報告不得只依賴：

* 標準差。  
* 常態分布 VaR。  
* 單一 Sharpe ratio。  
* 單一歷史區間。  
* 單一 covariance estimate。

必須同時考慮：

* Fat tails。  
* Correlation breakdown。  
* Volatility clustering。  
* Liquidity collapse。  
* Gap risk。  
* Venue failure。  
* Model risk。  
* Parameter uncertainty。  
* Estimation error。

---

## **14\. Paper 與 Shadow 監控**

### **14.1 Paper trading**

Paper trading 必須標示為模擬結果。

監控內容至少包含：

* 策略狀態。  
* 資料新鮮度。  
* 訊號。  
* 目標部位。  
* 模擬訂單。  
* 模擬成交。  
* 持倉。  
* 現金。  
* 已實現損益。  
* 未實現損益。  
* 回撤。  
* Exposure。  
* 拒單。  
* Partial fill。  
* 未成交訂單。  
* 健康度。  
* 告警。

### **14.2 Shadow monitoring**

Shadow 模式可以接收真實市場資料與真實帳戶的唯讀資訊，但不得送單。

Shadow 模式必須比較：

* 策略理論決策。  
* Paper 模擬決策。  
* 實際市場可成交價格。  
* 實際 spread。  
* 實際流動性。  
* 預估滑價。  
* 實際帳戶持倉。  
* 回測假設與即時狀況差異。

### **14.3 Drift monitoring**

最低 drift 類型：

* Data drift。  
* Feature drift。  
* Signal drift。  
* Position drift。  
* PnL drift。  
* Cost drift。  
* Slippage drift。  
* Latency drift。  
* Fill-rate drift。  
* Regime drift。  
* Parameter drift。  
* Strategy-version drift。

Drift 告警不得只顯示「異常」，必須提供：

* 比較基準。  
* 目前值。  
* 門檻。  
* 觀測期間。  
* 嚴重程度。  
* 可能原因。  
* 建議處置。

---

## **15\. 對帳**

TradeGuard 若讀取外部 paper 帳戶或真實帳戶唯讀資料，必須執行對帳。

對帳對象：

* 現金。  
* 資產餘額。  
* 持倉。  
* 未成交訂單。  
* 成交。  
* 手續費。  
* 已實現損益。  
* 未實現損益。  
* 交易日或結算狀態。

對帳狀態至少包含：

MATCHED  
MISMATCHED  
UNKNOWN  
STALE  
UNAVAILABLE

若狀態為 `UNKNOWN`、`STALE` 或 `UNAVAILABLE`，系統不得宣稱帳戶狀態正常。

---

## **16\. Web 儀表板**

Web 儀表板優先提供：

### **16.1 Overview**

* 總淨值。  
* 累積損益。  
* 當日損益。  
* 最大回撤。  
* 目前回撤。  
* Gross exposure。  
* Net exposure。  
* 策略健康度。  
* 資料健康度。  
* 告警摘要。

### **16.2 Strategies**

* 策略名稱。  
* 策略版本。  
* 市場。  
* 狀態。  
* 最新訊號。  
* 目標部位。  
* 當前部位。  
* 回測摘要。  
* Paper 摘要。  
* Drift。  
* 最近驗證日期。

### **16.3 Validation**

* 基準比較。  
* Walk-forward。  
* 樣本外結果。  
* 成本敏感度。  
* 參數敏感度。  
* Regime 分析。  
* Monte Carlo。  
* Bootstrap。  
* 過度擬合警告。  
* Promotion checklist。

### **16.4 Risk**

* Exposure。  
* Concentration。  
* VaR。  
* Expected Shortfall。  
* Drawdown。  
* Liquidity risk。  
* Venue risk。  
* Stablecoin risk。  
* Correlation stress。  
* Risk limit usage。

### **16.5 Data**

* 最新資料時間。  
* 延遲。  
* 缺口。  
* 異常值。  
* 來源。  
* Manifest。  
* Schema version。  
* Symbol mapping。  
* Corporate action 狀態。

### **16.6 Audit**

* 設定變更。  
* 策略版本變更。  
* 驗證結果。  
* Promotion 決策。  
* 使用者操作。  
* 告警處理。  
* 對帳差異。  
* 系統事故。

前端禁止：

* 儲存正式 API secret。  
* 直接連接券商或交易所交易端點。  
* 自行覆寫後端風控結果。  
* 隱藏失敗驗證。  
* 將模擬績效標示為真實績效。  
* 在未確認環境時顯示交易控制。

---

## **17\. 外部交易引擎整合**

TradeGuard 可以整合既有工具，例如：

* Freqtrade。  
* Hummingbot。  
* 自訂 Python 策略框架。  
* 券商 paper API。  
* 交易所 sandbox API。  
* CSV 或 Parquet 交易紀錄。  
* Read-only 帳戶 API。

所有整合必須透過 adapter。

Adapter 必須：

* 明確宣告能力。  
* 明確宣告環境。  
* 明確宣告是否唯讀。  
* 驗證回傳 schema。  
* 處理 rate limit。  
* 處理 timeout。  
* 處理 reconnect。  
* 處理重複事件。  
* 處理缺失 sequence。  
* 保留原始外部識別碼。  
* 不得將未知狀態推測為成功。

第一版 adapter 應優先唯讀或 paper-only。

---

## **18\. 設定系統**

所有設定必須：

* 版本化。  
* Schema 驗證。  
* 可產生 deterministic hash。  
* 區分敏感與非敏感欄位。  
* 支援 redacted display。  
* 保存變更原因。  
* 保存變更者。  
* 保存變更時間。  
* 保存生效環境。  
* 支援 rollback。

建議設定層級：

base  
environment  
market  
venue  
strategy  
portfolio  
risk  
cost  
monitoring  
alerting  
user override

合併後的最終設定必須可檢視。

設定驗證失敗時必須拒絕啟動。

---

## **19\. 權限與資訊安全**

### **19.1 最小權限**

所有 API key 必須遵守最小權限。

第一版只允許：

* Public market data。  
* Read-only account data。  
* Sandbox trading。  
* Paper trading。

禁止要求：

* 提款權限。  
* 資產轉移權限。  
* 子帳戶管理權限。  
* 建立新 API key 權限。  
* 未限制 IP 的高權限 key。  
* 正式交易權限，除非未來經獨立 RFC、法律審查與安全審查核准。

### **19.2 秘密管理**

禁止：

* 將 secret 寫入 Git。  
* 將 secret 寫入 README。  
* 將 secret 寫入測試 fixture。  
* 將 secret 寫入前端 bundle。  
* 將 secret 寫入 log。  
* 將完整 API key 顯示在錯誤訊息。  
* 將真實帳戶資料提交至公開 repository。

`.env.example` 只能使用假的 placeholder。

### **19.3 稽核紀錄**

稽核紀錄應採 append-only。

最低欄位：

audit\_id  
actor\_id  
actor\_type  
action  
resource\_type  
resource\_id  
environment  
reason  
before\_hash  
after\_hash  
timestamp\_utc  
correlation\_id  
result

禁止刪除或修改不利研究結果以美化績效。

---

## **20\. AI 與大型語言模型使用規則**

大型語言模型可以協助：

* 解釋研究報告。  
* 摘要風險。  
* 產生測試草稿。  
* 產生文件草稿。  
* 協助程式碼審查。  
* 協助分類告警。  
* 協助提出研究假設。  
* 協助產生非權威報告文字。

大型語言模型禁止：

* 直接送單。  
* 直接修改正式持倉。  
* 自動提高風險上限。  
* 自動取消風控。  
* 自動將策略晉級。  
* 直接將新聞文字轉為正式交易。  
* 將自然語言輸出視為確定性數值結果。  
* 未經測試便修改策略核心邏輯。  
* 捏造不存在的市場資料。  
* 捏造回測結果。  
* 捏造測試通過證據。

任何 LLM 產生的數值、統計結論或策略修改都必須由確定性程式驗證。

---

## **21\. 測試要求**

### **21.1 單元測試**

必須覆蓋：

* 金額與精度。  
* 時區。  
* 市場 session。  
* Corporate actions。  
* 成本模型。  
* Fill 模型。  
* 風險限制。  
* 設定驗證。  
* 資料品質。  
* 指標計算。  
* Strategy adapter。

### **21.2 Property-based tests**

應驗證：

* 現金守恆。  
* 資產守恆。  
* 成交後持倉一致性。  
* 費用非負。  
* Exposure 計算一致。  
* 不重複計入成交。  
* Event idempotency。  
* 時間順序不倒退。  
* 風險限制不可被繞過。  
* 對帳差異不會被靜默忽略。

### **21.3 Integration tests**

最低情境：

* 資料匯入至回測。  
* 策略至風控。  
* 風控至報告。  
* Paper event ingestion。  
* External adapter reconnect。  
* PostgreSQL persistence。  
* API contract。  
* Dashboard read path。

### **21.4 Replay tests**

最低 replay 情境：

* 資料缺口。  
* 重複事件。  
* 事件亂序。  
* 時間戳錯誤。  
* Partial fill。  
* 訂單拒絕。  
* Rate limit。  
* API timeout。  
* 交易所維護。  
* 股票暫停交易。  
* 股票分割。  
* Stablecoin 脫鉤。  
* Spread 急遽擴大。  
* 市場瞬間暴跌。  
* 資料來源錯價。

### **21.5 Regression tests**

每個已修復的重大缺陷必須新增：

* 最小重現 fixture。  
* Regression test。  
* 問題原因說明。  
* 防止再次發生的驗證。

---

## **22\. CI 要求**

每個 Pull Request 至少必須執行：

format  
lint  
typecheck  
unit tests  
property tests  
integration tests  
contract tests  
secret scan  
dependency scan  
container scan  
migration validation

變更涉及下列內容時，必須增加對應測試：

* 回測引擎：determinism 與 regression。  
* 成本模型：敏感度與邊界。  
* 風險引擎：property tests。  
* 外部 adapter：contract 與 reconnect。  
* Corporate action：point-in-time fixture。  
* 前端：E2E。  
* 資料 schema：migration 與 backward compatibility。  
* 權限：RBAC 與 audit。  
* 報告：golden-file 或 snapshot validation。

禁止透過下列方式讓 CI 通過：

* 刪除失敗測試。  
* 放寬風險限制。  
* 跳過安全掃描。  
* 將例外吞掉。  
* 將 assertion 改為 log。  
* 無理由增加容差。  
* 將 deterministic test 改為不穩定測試。  
* 偽造測試輸出。

---

## **23\. Agent 工作規則**

AI 代理開始任何任務前必須：

1. 閱讀本 `AGENTS.md`。  
2. 閱讀目標目錄內更具體的 `AGENTS.md`。  
3. 檢查相關文件。  
4. 檢查相關測試。  
5. 明確列出假設。  
6. 確認不會新增正式交易能力。  
7. 確認不會取得或暴露真實 secret。  
8. 確認變更不會降低風險控制。

### **23.1 修改前輸出**

代理應先簡短輸出：

Objective  
Assumptions  
Files expected to change  
Validation plan  
Risk impact

### **23.2 修改原則**

代理必須：

* 優先最小變更。  
* 保留 backward compatibility。  
* 為新行為新增測試。  
* 為風險行為新增負面測試。  
* 使用清楚型別。  
* 避免全域狀態。  
* 避免隱性 I/O。  
* 避免未記錄的隨機性。  
* 避免未驗證的外部輸入。  
* 保留可稽核紀錄。  
* 更新相關文件。

### **23.3 禁止事項**

代理禁止：

* 自行新增 live trading。  
* 建立 `make live`。  
* 寫入真實 API key。  
* 呼叫提款或轉帳 API。  
* 宣稱策略可獲利。  
* 捏造測試結果。  
* 捏造 benchmark。  
* 捏造市場資料。  
* 修改研究資料以改善結果。  
* 將驗證失敗改為警告而未經批准。  
* 關閉 look-ahead 檢查。  
* 關閉成本模型。  
* 將 paper 結果標示為 live。  
* 自行批准策略 promotion。  
* 在未讀取相關程式碼前大規模重構。

### **23.4 完成後輸出**

代理完成任務後必須提供：

Summary  
Files changed  
Behavior changes  
Risk impact  
Tests executed  
Test results  
Known limitations  
Rollback plan  
Follow-up work

若測試未執行，必須明確說明原因，不得暗示已通過。

---

## **24\. Pull Request 驗收清單**

\- \[ \] 變更目的與範圍清楚  
\- \[ \] 已閱讀並遵循 AGENTS.md  
\- \[ \] 無真實 secret、帳戶資料或受限市場資料  
\- \[ \] 無新增未授權 live trading 路徑  
\- \[ \] 型別檢查通過  
\- \[ \] Lint 通過  
\- \[ \] Unit tests 通過  
\- \[ \] Property tests 通過  
\- \[ \] Integration tests 通過  
\- \[ \] 相關 replay／regression tests 通過  
\- \[ \] 資料時間點一致性未被破壞  
\- \[ \] 無 look-ahead bias  
\- \[ \] 無 survivorship bias  
\- \[ \] 無 label 或 feature leakage  
\- \[ \] 成本、spread、滑價與 partial fill 已考慮  
\- \[ \] 風險限制未被繞過或放寬  
\- \[ \] 研究結果可重現  
\- \[ \] Run manifest 可產生  
\- \[ \] Benchmark 與基準比較完整  
\- \[ \] 成本前與成本後績效皆有說明  
\- \[ \] 不利結果未被隱藏  
\- \[ \] 文件已更新  
\- \[ \] Migration 可回滾  
\- \[ \] API contract 已更新  
\- \[ \] 前端未包含秘密或權威風控邏輯  
\- \[ \] 已提供 rollback plan  
\- \[ \] 已列出 known limitations

---

## **25\. 策略 Promotion Gates**

策略不得因單一回測結果良好而晉級。

建議流程：

IDEA  
  ↓  
RESEARCH  
  ↓  
BACKTEST  
  ↓  
ROBUSTNESS  
  ↓  
OUT\_OF\_SAMPLE  
  ↓  
REPLAY  
  ↓  
PAPER  
  ↓  
SHADOW  
  ↓  
APPROVED\_FOR\_EXTERNAL\_EXECUTION

TradeGuard 第一版最高僅支援至：

SHADOW

### **25.1 Research 至 Backtest**

必須具備：

* 策略規格。  
* 資料需求。  
* Benchmark。  
* 假設。  
* 失效條件。  
* 初始成本模型。  
* Look-ahead 檢查。

### **25.2 Backtest 至 Robustness**

必須具備：

* 成本後正績效或合理研究理由。  
* 完整交易紀錄。  
* 可重現 run manifest。  
* Benchmark 比較。  
* 無重大資料品質錯誤。  
* 無 look-ahead。  
* 無 survivorship bias。

### **25.3 Robustness 至 Out-of-sample**

必須具備：

* 參數敏感度。  
* 成本敏感度。  
* 時間區間敏感度。  
* Universe 敏感度。  
* Regime 分析。  
* 壓力測試。  
* 過度擬合檢查。

### **25.4 Out-of-sample 至 Paper**

必須具備：

* 完全未參與調參的測試資料。  
* 可接受回撤。  
* 可接受尾端風險。  
* 可接受換手率。  
* 可接受流動性。  
* 明確風險上限。  
* 明確停用條件。

### **25.5 Paper 至 Shadow**

必須具備：

* 足夠觀測期間。  
* 穩定資料品質。  
* 模擬成交與市場狀況合理。  
* 無重大對帳差異。  
* 告警可用。  
* Drift 指標可用。  
* 事故處理文件。  
* 人工審查。

任何 promotion 都必須保存：

promotion\_id  
strategy\_id  
strategy\_version  
from\_stage  
to\_stage  
evidence  
approver  
timestamp\_utc  
conditions  
expiration  
rollback\_conditions

---

## **26\. 報告標準**

每份正式研究報告至少包含：

1. Executive summary。  
2. 策略假設。  
3. 市場與 universe。  
4. 資料來源。  
5. 資料品質。  
6. Point-in-time 說明。  
7. 策略邏輯。  
8. 參數。  
9. Benchmark。  
10. 成本與成交假設。  
11. In-sample 結果。  
12. Out-of-sample 結果。  
13. Walk-forward 結果。  
14. Robustness tests。  
15. Stress tests。  
16. Risk analysis。  
17. Regime analysis。  
18. Capacity 與 liquidity。  
19. 已知限制。  
20. 失效條件。  
21. Promotion 建議。  
22. Run manifest。  
23. Git commit。  
24. 資料與設定 hash。

報告必須同時呈現有利及不利結果。

---

## **27\. 告警等級**

建議告警等級：

INFO  
WARNING  
HIGH  
CRITICAL

### **INFO**

* 研究完成。  
* 報告產生。  
* 非重大設定變更。  
* Paper session 開始或結束。

### **WARNING**

* 資料延遲。  
* 輕微 drift。  
* 成本上升。  
* 回撤接近門檻。  
* 部分資料缺失。

### **HIGH**

* 資料來源衝突。  
* 嚴重 drift。  
* 對帳不一致。  
* 風險限制接近耗盡。  
* 交易所 API 大量錯誤。  
* 股票 corporate action 未處理。  
* Stablecoin 顯著偏離。

### **CRITICAL**

* 帳戶狀態未知。  
* 持倉無法對帳。  
* 資料疑似錯價。  
* 系統錯誤地產生正式交易能力。  
* Secret 外洩。  
* 不可變研究資料遭修改。  
* 風控被繞過。  
* Paper 或 shadow 被誤標為 live。  
* 稽核紀錄遺失。

Critical 告警必須預設停止新的策略建議與 promotion。

---

## **28\. 事故處理**

任何重大事故至少必須：

1. 停止受影響的研究、paper 或 shadow 工作。  
2. 保存原始資料、log、事件、設定與版本資訊。  
3. 記錄事故時間線。  
4. 確認是否涉及 secret。  
5. 確認是否涉及帳戶或資產。  
6. 確認資料是否遭竄改。  
7. 確認結果是否受到影響。  
8. 標記所有受污染研究執行。  
9. 建立最小重現。  
10. 新增 regression test。  
11. 完成 root-cause analysis。  
12. 更新文件與 runbook。  
13. 經人工審查後才恢復。

禁止刪除事故證據或修改失敗結果。

---

## **29\. 初始 MVP**

第一個可用版本只需完成一條垂直路徑：

歷史資料匯入  
  ↓  
資料品質檢查  
  ↓  
一個股票 baseline 策略  
  ↓  
一個加密貨幣 baseline 策略  
  ↓  
確定性回測  
  ↓  
成本與滑價模型  
  ↓  
Walk-forward 與樣本外驗證  
  ↓  
策略報告  
  ↓  
Web 儀表板

第一版 baseline 可以包含：

### **股票**

* Buy and hold。  
* Moving-average trend。  
* Cross-sectional momentum。  
* Mean reversion。

### **加密貨幣**

* Buy and hold。  
* Volatility-scaled trend。  
* Breakout。  
* Regime-gated mean reversion。

Baseline 的目的不是宣稱可獲利，而是驗證研究與監控流程。

---

## **30\. 建議 Milestones**

### **Milestone 0 — Repository Bootstrap**

* Python typed project。  
* CI。  
* 設定 schema。  
* Domain events。  
* PostgreSQL。  
* FastAPI skeleton。  
* Dashboard skeleton。  
* Docker Compose。  
* Mock data。  
* Security baseline。

### **Milestone 1 — Data Foundation**

* 股票與加密貨幣 canonical schema。  
* Data manifest。  
* Checksum。  
* Data quality。  
* Instrument metadata。  
* Trading calendar。  
* Corporate actions。  
* Crypto precision metadata。

### **Milestone 2 — Deterministic Backtester**

* Event loop。  
* Strategy adapter。  
* Portfolio ledger。  
* Fill model。  
* Cost model。  
* Replay。  
* Run manifest。  
* Determinism tests。

### **Milestone 3 — Validation Engine**

* Benchmark comparison。  
* Walk-forward。  
* Out-of-sample。  
* Bootstrap。  
* Parameter sensitivity。  
* Cost sensitivity。  
* Regime analysis。  
* Overfitting warnings。

### **Milestone 4 — Risk Engine**

* Exposure。  
* Concentration。  
* Volatility targeting。  
* Drawdown limits。  
* Liquidity risk。  
* Venue risk。  
* Stablecoin risk。  
* Stress scenarios。

### **Milestone 5 — Reporting and Dashboard**

* Research reports。  
* Strategy comparison。  
* Risk dashboard。  
* Data health。  
* Audit log。  
* Promotion workflow。

### **Milestone 6 — Paper Monitoring**

* Paper adapter。  
* Position monitoring。  
* Order monitoring。  
* Reconciliation。  
* Drift monitoring。  
* Alerts。

### **Milestone 7 — Shadow Monitoring**

* Read-only account integration。  
* Real-time market comparison。  
* Expected versus observed costs。  
* Strategy drift。  
* Operational runbooks。

第一版不得因進度壓力跳過 Milestone 1 至 4 而直接整合正式帳戶。

---

## **31\. 初始 GitHub Issues**

1. `chore: bootstrap typed Python project`  
2. `chore: configure lint typecheck tests and CI`  
3. `feat: define immutable domain events`  
4. `feat: implement versioned configuration`  
5. `feat: implement dataset manifest and checksums`  
6. `feat: add market data quality validation`  
7. `feat: define instrument metadata model`  
8. `feat: add equity market calendar support`  
9. `feat: add point-in-time corporate actions`  
10. `feat: add crypto precision and notional rules`  
11. `feat: build deterministic event loop`  
12. `feat: implement portfolio ledger`  
13. `feat: implement conservative fill model`  
14. `feat: implement transaction cost models`  
15. `feat: add strategy adapter protocol`  
16. `feat: implement baseline equity strategies`  
17. `feat: implement baseline crypto strategies`  
18. `test: add look-ahead bias detection`  
19. `test: add survivorship-bias fixtures`  
20. `feat: implement walk-forward analysis`  
21. `feat: implement out-of-sample evaluation`  
22. `feat: add parameter sensitivity analysis`  
23. `feat: add cost and slippage stress tests`  
24. `feat: add bootstrap and Monte Carlo analysis`  
25. `feat: implement portfolio exposure engine`  
26. `feat: implement drawdown and liquidity limits`  
27. `feat: implement venue and quote-asset risk`  
28. `feat: generate reproducible research reports`  
29. `feat: add FastAPI control and reporting API`  
30. `feat: build strategy validation dashboard`  
31. `feat: add paper-trading event adapter`  
32. `feat: implement reconciliation service`  
33. `feat: implement strategy and cost drift monitoring`  
34. `ops: add metrics alerts and health checks`  
35. `security: add secret scanning and least privilege`  
36. `docs: add strategy specification template`  
37. `docs: add research report template`  
38. `docs: add incident response runbook`  
39. `release: define research-to-paper promotion checklist`  
40. `test: add end-to-end reproducibility fixture`

---

## **32\. 完成標準**

TradeGuard 第一個正式版本只有在下列條件全部滿足時才算完成：

* 可匯入至少一種股票資料。  
* 可匯入至少一種加密貨幣資料。  
* 可驗證資料品質。  
* 可處理股票交易時段。  
* 可處理股票公司行動。  
* 可處理加密貨幣 precision 與 minimum notional。  
* 可執行確定性回測。  
* 可模擬費用、spread、滑價及 partial fill。  
* 可執行 walk-forward。  
* 可執行樣本外驗證。  
* 可產生基準比較。  
* 可執行參數及成本敏感度測試。  
* 可產生完整 run manifest。  
* 可產生可重現報告。  
* 可顯示策略與投資組合風險。  
* 可顯示資料健康度。  
* 可保存不可變稽核紀錄。  
* 可執行 paper monitoring。  
* 可執行對帳。  
* 所有核心測試通過。  
* 無正式交易功能。  
* 無提款或資產轉移能力。  
* 無真實 secret。  
* 文件清楚標示不保證獲利。

---

## **33\. 最終原則**

TradeGuard 的成功標準不是：

> 找到一個回測報酬最高的策略。

TradeGuard 的成功標準是：

> 能夠以可驗證、可重現、風險透明且不誤導使用者的方式，判斷一個股票或加密貨幣策略是否值得繼續研究、進入 paper trading、進入 shadow monitoring，或應立即停止。

任何開發決策若無法提高下列至少一項，應重新評估其必要性：

* 研究可信度。  
* 資料完整性。  
* 結果可重現性。  
* 風險透明度。  
* 使用者安全。  
* 維運可靠性。  
* 稽核能力。  
* 決策品質。

