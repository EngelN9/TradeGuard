# **TradeGuard**

> 安全地研究、監控與驗證股票及加密貨幣交易策略。

TradeGuard 是一個以**可驗證、可重現、風險透明與安全優先**為核心的量化策略研究與監控平台。

它協助研究者與策略開發者回答以下問題：

* 這個策略的回測結果是否可信？  
* 是否存在 look-ahead bias、survivorship bias 或資料洩漏？  
* 扣除手續費、spread、滑價與 market impact 後，策略是否仍然成立？  
* 策略是否只在特定資料區間或特定參數下有效？  
* Paper trading 或 shadow monitoring 的結果是否偏離回測假設？  
* 策略目前的回撤、曝險、集中度與流動性風險是否可接受？  
* 這個策略應繼續研究、進入下一階段，還是停止使用？

TradeGuard 不以「保證獲利」為產品目標，而是提供一套更可靠的方法，判斷一個既有策略是否值得信任。

---

## **專案狀態**

EQUITY ADAPTER IMPLEMENTED / NOT TRADABLE

目前專案已完成 repository bootstrap、Prompt 2 核心資料合約、Prompt 3
離線資料基礎與 Prompt 4 的受限股票資料 adapter；尚未完成 connected
qualification，也未進入策略或回測階段。

* 已建立 typed Python package、FastAPI health endpoints、worker、mock market-data、deterministic paper broker skeleton 與唯讀 dashboard placeholder。
* 已建立鎖定依賴、測試、靜態檢查、GitHub Actions、Dockerfile、Docker Compose 與 bootstrap evidence 骨架。
* 已建立 immutable domain events、canonical checksum、versioned configuration、secret redaction、RunManifest 與 JSON Schema snapshots。
* 已建立 canonical equity/crypto records、point-in-time metadata、DatasetManifest、content-addressed storage、品質閘門、synthetic fixtures、lineage 與離線 data CLI。
* 已建立受限 Twelve Data 股票資料 adapter；connected session 仍待人工審閱，promotion 為 `BLOCKED`。
* 尚未提供任何策略、投資建議或可供投資判斷的驗證結果。
* 尚未連接正式券商、交易所帳戶或外部市場資料服務。
* 執行環境只接受 `research`、`backtest`、`replay`、`paper`、`shadow`；其他值會 fail closed。
* `shadow` 只代表允許的唯讀設計上限，不表示目前已有帳戶連線。
* 專案沒有 `live`、正式下單、提款或轉帳能力。
* 不需要，也不得提交真實 API key。

重要文件：

* [`AGENTS.md`](AGENTS.md)：最高層級工程、安全、研究與風險規格。
* [`PROMPTS.md`](PROMPTS.md)：依序執行的交付階段與人工審查閘門。
* [`SECURITY.md`](SECURITY.md)：安全政策與私密通報方式。
* [`CONTRIBUTING.md`](CONTRIBUTING.md)：開發、測試與 Pull Request 規範。
* [`docs/data/data-foundation.md`](docs/data/data-foundation.md)：資料模型、manifest、lineage 與品質閘門。
* [`docs/release/connected-release-v1.md`](docs/release/connected-release-v1.md)：Connected Release v1 合約。
* [`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md)：逐項實作狀態與缺口。

---

## **核心定位**

TradeGuard 是：

* 量化策略研究平台。  
* 確定性回測與 replay 平台。  
* Walk-forward 與樣本外驗證工具。  
* 回測偏誤與資料洩漏檢查工具。  
* 交易成本與滑價壓力測試平台。  
* 策略風險與投資組合風險監控平台。  
* Paper trading 與 shadow monitoring 平台。  
* 策略版本、實驗與研究報告管理工具。  
* Freqtrade、Hummingbot、自訂策略與外部 paper API 的監控層。

TradeGuard 不是：

* 保證獲利的交易機器人。  
* 代客操盤服務。  
* 投資建議或投資顧問服務。  
* 跟單或訊號販售平台。  
* 資產保管平台。  
* 券商或交易所。  
* 超低延遲或高頻交易引擎。  
* 自動替使用者管理正式資金的系統。  
* 由大型語言模型直接決定正式買賣的系統。

---

## **為什麼需要 TradeGuard？**

一個可以執行策略的交易機器人，不代表該策略具有正期望值。

許多看似優秀的回測結果，可能來自：

* 使用未來資料。  
* Survivorship bias。  
* 未納入下市標的。  
* 公司行動處理錯誤。  
* 在測試集上反覆調參。  
* 忽略手續費、spread 與滑價。  
* 假設所有 limit order 都能成交。  
* 以不可能取得的價格成交。  
* 過度選擇最佳參數。  
* 只展示有利期間。  
* 忽略市場 regime 改變。  
* 忽略流動性與容量限制。  
* 忽略交易所、券商或資料來源故障。  
* 將 paper trading 結果誤認為真實可實現績效。

TradeGuard 將研究、驗證、風控與監控整合成同一套可稽核流程，讓使用者能夠檢查：

資料是否可信

    ↓

回測是否正確

    ↓

策略是否穩健

    ↓

成本後是否仍有效

    ↓

樣本外是否成立

    ↓

Paper／Shadow 是否偏離

    ↓

目前風險是否可接受

---

## **支援市場**

TradeGuard 的長期範圍包含：

### **股票**

預計支援：

* 股票現貨。  
* ETF。  
* 大型股。  
* Long-only。  
* Cash-only。  
* 日線與分鐘級研究。  
* 交易所日曆。  
* 休市與半日市。  
* 盤前與盤後。  
* 暫停交易。  
* 股票分割與反向分割。  
* 股利與其他公司行動。  
* 代號變更。  
* 下市。  
* Point-in-time universe。  
* 交易稅與手續費。  
* Lot size 與 tick size。

### **加密貨幣**

預計支援：

* 高流動性現貨交易對。  
* Long／flat。  
* 24/7 市場資料。  
* 交易所維護狀態。  
* Tick size。  
* Step size。  
* Minimum quantity。  
* Minimum notional。  
* Maker／taker fee。  
* Stablecoin 與 quote asset 風險。  
* Venue exposure。  
* Rate limit。  
* API 斷線與 reconnect。  
* 交易對下架。  
* 流動性與 spread 異常。

第一版不支援：

* 槓桿。  
* 保證金交易。  
* 永續合約。  
* 期貨。  
* 選擇權。  
* 自動借貸。  
* 自動放空。  
* 未經人工核准的正式交易。

---

## **核心功能**

以下功能為預定開發範圍，不代表目前已全部完成。

### **資料治理**

* 股票與加密貨幣 canonical schema。  
* Append-only 原始資料。  
* Dataset manifest。  
* Checksum。  
* Schema version。  
* 資料來源與授權紀錄。  
* 缺口、重複、亂序與異常價格檢查。  
* 股票公司行動處理。  
* Symbol mapping。  
* Point-in-time 資料驗證。  
* 多來源資料一致性檢查。

### **策略接入**

* 統一策略 adapter。  
* 自訂 Python 策略。  
* Freqtrade 策略。  
* Hummingbot 策略。  
* CSV／Parquet 交易紀錄。  
* 券商或交易所 paper API。  
* Read-only 帳戶資料。  
* 策略版本管理。  
* 策略參數 schema。  
* 策略適用市場與資料需求宣告。

### **回測**

* 確定性事件驅動回測。  
* Replay。  
* Market order。  
* Limit order。  
* Partial fill。  
* Non-fill。  
* Spread。  
* 手續費。  
* 交易稅。  
* 滑價。  
* Market impact。  
* Latency。  
* Minimum notional。  
* Tick size 與 step size。  
* 交易暫停與 venue maintenance。  
* 可重現 run manifest。

### **策略驗證**

* Benchmark comparison。  
* Training／validation／test 分離。  
* Out-of-sample evaluation。  
* Walk-forward analysis。  
* 參數敏感度。  
* 起訖日期敏感度。  
* Universe 敏感度。  
* 成本與滑價壓力測試。  
* Regime analysis。  
* Bootstrap。  
* Block bootstrap。  
* Monte Carlo。  
* Purging 與 embargo。  
* 多重假設檢定警告。  
* 過度擬合風險評估。  
* Look-ahead bias 檢查。  
* Survivorship bias 檢查。  
* Feature／label leakage 檢查。

### **風險管理**

* Gross exposure。  
* Net exposure。  
* 單一標的集中度。  
* 產業與因子曝險。  
* Venue exposure。  
* Quote asset exposure。  
* Volatility targeting。  
* Drawdown limits。  
* Liquidity risk。  
* Correlation stress。  
* Value at Risk。  
* Expected Shortfall。  
* Tail-risk scenarios。  
* Stablecoin depeg 風險。  
* 策略與投資組合風險限制。

### **Paper 與 Shadow 監控**

* 訊號與目標部位。  
* 模擬訂單與成交。  
* 持倉與現金。  
* 已實現與未實現損益。  
* 回撤。  
* Exposure。  
* 拒單。  
* Partial fill。  
* 未成交訂單。  
* 資料延遲。  
* API 健康度。  
* 對帳差異。  
* Data drift。  
* Signal drift。  
* PnL drift。  
* Cost drift。  
* Slippage drift。  
* Fill-rate drift。  
* Regime drift。

### **報告與稽核**

* 可重現研究報告。  
* 策略版本比較。  
* Benchmark comparison。  
* 成本前與成本後績效。  
* Walk-forward 報告。  
* 樣本外報告。  
* Regime 分解。  
* 風險分析。  
* Run manifest。  
* Git commit 與設定 hash。  
* Append-only audit log。  
* Promotion evidence。  
* 事故與告警處理紀錄。

---

## **安全邊界**

TradeGuard 預設只允許：

research

backtest

replay

paper

shadow

TradeGuard 第一版不得提供：

canary

live

策略模組只能產生：

Signal

TargetPosition

TradeProposal

策略不得直接：

* 呼叫正式券商或交易所下單 API。  
* 存取正式交易憑證。  
* 提款或轉移資產。  
* 修改帳戶權限。  
* 繞過風險引擎。  
* 覆寫不可變稽核紀錄。  
* 自動提高風險上限。  
* 自動將策略晉級至更高環境。

任何未知、過期或無法確認的狀態，必須 fail closed。

---

## **系統架構**

TradeGuard 預計優先採用模組化單體，避免在早期開發階段過度拆分微服務。

股票／加密貨幣資料來源

            ↓

資料擷取與標準化

            ↓

資料品質與 Point-in-time 閘門

            ↓

策略 Adapter 與策略執行器

            ↓

確定性回測與 Replay

            ↓

成交、成本與投資組合模型

            ↓

驗證、壓力測試與風險引擎

            ↓

Paper／Shadow 事件監控

            ↓

報告、告警、API 與 Web 儀表板

系統預計分為三個邏輯平面：

### **Research Plane**

* 歷史資料。  
* 資料品質。  
* 回測。  
* Replay。  
* Walk-forward。  
* 樣本外驗證。  
* 實驗追蹤。  
* 報告產生。

### **Monitoring Plane**

* Paper／shadow 事件。  
* 持倉與曝險。  
* 損益。  
* 對帳。  
* Drift。  
* 健康檢查。  
* 告警。

### **Control Plane**

* 設定查詢。  
* 策略版本管理。  
* Promotion workflow。  
* 稽核查詢。  
* 唯讀監控。  
* 受控 paper／shadow 操作。

瀏覽器不是交易或研究工作的唯一執行環境。長時間回測、資料處理與監控工作必須在後端程序執行。

---

## **預定技術棧**

### **後端**

* Python 3.12+  
* FastAPI  
* Pydantic  
* SQLAlchemy  
* Alembic  
* PostgreSQL  
* Polars 或 Pandas  
* NumPy  
* SciPy  
* PyArrow  
* DuckDB

### **前端**

* TypeScript  
* React  
* Next.js  
* OpenAPI-generated types  
* Responsive Web UI

### **工程品質**

* `uv`  
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

---

## **預定儲存庫結構**

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

├── configs/

│   ├── base.yaml

│   ├── research.yaml

│   ├── backtest.yaml

│   ├── replay.yaml

│   ├── paper.yaml

│   ├── shadow.yaml

│   ├── markets/

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

│       ├── monitoring/

│       ├── portfolio/

│       ├── reconciliation/

│       ├── reports/

│       ├── risk/

│       ├── strategies/

│       ├── validation/

│       └── workers/

├── web/

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

├── scripts/

└── reports/

---

## **開發環境**

以下指令已由 Prompt 1 bootstrap 提供。Windows 沒有 GNU Make 時，可以直接執行
Makefile 中對應的 `uv`、`npm` 或 `docker compose` 指令。

### **必要工具**

需要：

* Git  
* Python 3.12+  
* `uv`  
* Docker  
* Docker Compose  
* Node.js  
* npm

### **取得程式碼**

git clone https://github.com/EngelN9/TradeGuard.git

cd TradeGuard

### **安裝後端依賴**

uv sync

### **建立本機設定**

cp .env.example .env

`.env.example` 只能包含假的 placeholder。不得將任何真實 API key、帳戶資料或 secret 提交至 Git。

### **執行本機服務**

make dev-up

啟動的本機 skeleton：

* PostgreSQL  
* FastAPI  
* 後端 worker  
* Mock market-data service  
* Deterministic paper broker skeleton
* Web dashboard

停止服務：

make dev-down

---

## **常用開發指令**

已提供的 Makefile 介面：

make setup

make format

make lint

make typecheck

make test

make test-unit

make test-integration

make test-property

make test-replay

make test-e2e

make test-connected

make evidence

make schemas

make data-fixtures

make prompt3-evidence

make prompt4-evidence

make dev-up

make dev-down

make api

make worker

make web

專案不得建立：

make live

---

## **設定環境**

允許環境：

| 環境 | 用途 | 外部資料 | 帳戶資料 | 下單 |
| ----- | ----- | ----- | ----- | ----- |
| `research` | 研究與資料分析 | 歷史或模擬 | 否 | 否 |
| `backtest` | 確定性回測 | 歷史資料 | 否 | 否 |
| `replay` | 重播歷史或事故情境 | 歷史事件 | 否 | 否 |
| `paper` | 模擬訂單與成交 | 即時或歷史 | 模擬 | 模擬 |
| `shadow` | 真實市場與唯讀帳戶監控 | 即時 | 唯讀 | 否 |
| `canary` | 第一版不支援 | 不適用 | 不適用 | 禁止 |
| `live` | 第一版不支援 | 不適用 | 不適用 | 禁止 |

啟動時必須顯示目前環境，且設定驗證失敗時必須拒絕啟動。

---

## **策略驗證流程**

TradeGuard 預定使用下列策略生命週期：

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

第一版最高只支援至：

SHADOW

策略不得因單一回測結果良好而晉級。

每次晉級必須保存：

* 策略版本。  
* 資料版本。  
* Git commit。  
* 設定 hash。  
* Benchmark。  
* 成本模型。  
* 樣本外結果。  
* 壓力測試結果。  
* 風險限制。  
* 人工審查紀錄。  
* 退回條件。  
* 停用條件。

---

## **回測結果標準**

每份完整策略報告預計至少包含：

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
* Gross exposure。  
* Net exposure。  
* Concentration。  
* 成本前績效。  
* 成本後績效。  
* Benchmark-relative return。  
* Beta。  
* Alpha。  
* Tail behavior。  
* 最差日、週與月。  
* Regime 分解。  
* 標的與時間區間貢獻。

禁止只使用勝率或單一 Sharpe ratio 判斷策略品質。

---

## **可重現性**

每次研究、回測、replay 或驗證都必須產生 run manifest。

最低內容：

run\_id

strategy\_id

strategy\_version

git\_commit

config\_hash

dataset\_id

dataset\_manifest

date\_range

universe

random\_seed

python\_version

dependency\_lock\_hash

cost\_model\_version

slippage\_model\_version

execution\_model\_version

started\_at

completed\_at

result\_checksum

warnings

validation\_failures

相同資料、策略、設定、種子與執行模型，應產生相同結果。

---

## **安全規則**

### **API Key**

第一版只允許：

* Public market-data key。  
* Read-only account key。  
* Sandbox key。  
* Paper trading key。

禁止使用：

* 提款權限。  
* 轉帳權限。  
* 子帳戶管理權限。  
* 未限制用途的高權限 key。  
* 正式交易權限。

### **Secrets**

禁止將 secret 放入：

* Git commit。  
* README。  
* Issue。  
* Pull Request。  
* 測試 fixture。  
* Log。  
* 前端 bundle。  
* Screenshot。  
* 範例設定。

若發現 secret 外洩，必須立即：

1. 撤銷憑證。  
2. 建立新憑證。  
3. 檢查 Git 歷史。  
4. 記錄事故。  
5. 評估帳戶影響。  
6. 新增防止重發的測試或掃描規則。

安全問題請依 [`SECURITY.md`](SECURITY.md) 使用 GitHub Private Vulnerability
Reporting 私密回報。請勿在公開 Issue 張貼任何：

* API key。  
* 帳戶資訊。  
* 可利用的漏洞細節。  
* 個人識別資訊。  
* 未公開交易資料。

---

## **測試原則**

核心測試預計包含：

### **Unit tests**

* 時區。  
* Decimal 精度。  
* 市場 session。  
* 公司行動。  
* 成本模型。  
* Fill 模型。  
* 風險限制。  
* 資料品質。  
* 指標計算。  
* 設定驗證。

### **Property-based tests**

* 現金守恆。  
* 資產守恆。  
* 成交不可重複計入。  
* 費用不可為負。  
* Event idempotency。  
* 曝險計算一致。  
* 風險限制不可被繞過。  
* 對帳差異不可被靜默忽略。

### **Replay tests**

* 資料缺口。  
* 事件重複。  
* 事件亂序。  
* API timeout。  
* Rate limit。  
* Partial fill。  
* 訂單拒絕。  
* 股票暫停交易。  
* 股票分割。  
* 交易所維護。  
* Stablecoin 脫鉤。  
* Spread 急遽擴大。  
* 市場瞬間暴跌。  
* 資料來源錯價。

### **Regression tests**

每個重大缺陷修復後必須新增：

* 最小重現 fixture。  
* Regression test。  
* Root cause 說明。  
* 防止再次發生的驗證。

---

## **開發里程碑**

### **Milestone 0 — Repository Bootstrap**

* Python typed project。  
* Dependency lock。  
* Lint、typecheck 與 tests。  
* GitHub Actions。  
* Docker Compose。  
* PostgreSQL。  
* FastAPI skeleton。  
* Dashboard skeleton。  
* Mock services。  
* Domain events。  
* Versioned configuration。  
* Security baseline。

### **Milestone 1 — Data Foundation**

* Canonical market schema。  
* Dataset manifest。  
* Checksum。  
* Data quality pipeline。  
* Instrument metadata。  
* 股票交易日曆。  
* 股票公司行動。  
* 加密貨幣 precision 與 notional 規則。

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
* Out-of-sample evaluation。  
* Parameter sensitivity。  
* Cost sensitivity。  
* Bootstrap。  
* Monte Carlo。  
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

### **Milestone 5 — Reports and Dashboard**

* Research reports。  
* Strategy comparison。  
* Validation dashboard。  
* Risk dashboard。  
* Data-health dashboard。  
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

---

## **MVP 成功標準**

第一個 MVP 只需要完成一條可驗證的垂直路徑：

歷史資料匯入

  ↓

資料品質檢查

  ↓

股票 baseline 策略

  ↓

加密貨幣 baseline 策略

  ↓

確定性回測

  ↓

成本與滑價模型

  ↓

Walk-forward

  ↓

樣本外驗證

  ↓

風險摘要

  ↓

可重現研究報告

  ↓

Web 儀表板

MVP 不需要：

* 正式下單。  
* 多券商正式整合。  
* 多交易所正式整合。  
* 原生手機 App。  
* 高頻交易。  
* 複雜微服務。  
* 機器學習黑箱策略。  
* 自動參數自我修改。  
* 自動管理使用者資金。

---

## **貢獻方式**

TradeGuard 尚在早期開發階段；目前只有 repository bootstrap，尚無策略或外部服務 adapter。

提交變更前，請先閱讀：

1. [`AGENTS.md`](AGENTS.md)
2. [`CONTRIBUTING.md`](CONTRIBUTING.md)
3. 目標目錄內較具體的 `AGENTS.md`  
4. 相關測試與文件

Pull Request 必須：

* 清楚說明目的與範圍。  
* 不包含任何真實 secret。  
* 不新增未授權的正式交易路徑。  
* 為新行為新增測試。  
* 保留可重現性。  
* 不降低資料品質檢查。  
* 不關閉 look-ahead 或成本檢查。  
* 不放寬風險限制以讓測試通過。  
* 說明風險影響。  
* 提供 rollback plan。  
* 列出 known limitations。

---

## **AI 程式設計代理**

本 repository 可以使用 Codex 或其他 AI 程式設計代理協助開發，但代理必須遵守 [`AGENTS.md`](AGENTS.md)。

AI 代理不得：

* 自行新增 live trading。  
* 輸入或要求真實 API key。  
* 捏造回測結果。  
* 捏造測試通過紀錄。  
* 修改資料以改善績效。  
* 關閉失敗測試。  
* 降低風險限制。  
* 將 paper 結果描述為真實績效。  
* 自動批准策略 promotion。  
* 使用 LLM 輸出作為權威數值結果。

---

## **已知限制**

專案初期預期具有以下限制：

* 支援的資料來源有限。  
* 不同市場資料格式仍需標準化。  
* 成本與滑價模型不可能完全還原真實成交。  
* Paper trading 無法完整重現 queue position。  
* Shadow monitoring 不代表策略可正式交易。  
* 統計檢定不能消除所有資料探勘偏誤。  
* 歷史績效不能保證未來績效。  
* 市場 regime、流動性與交易規則可能改變。  
* 不同交易所、券商及司法管轄區可能有額外限制。  
* 使用者仍需自行確認法規、稅務與資料授權要求。

---

## **免責聲明**

TradeGuard 僅供：

* 軟體工程。  
* 量化研究。  
* 教育。  
* 回測。  
* Paper trading。  
* Shadow monitoring。  
* 風險分析。

本專案：

* 不構成投資建議。  
* 不構成證券、期貨、虛擬資產或其他金融商品之推薦。  
* 不保證任何策略獲利。  
* 不保證歷史或模擬績效可在真實市場實現。  
* 不應在使用者不了解程式碼、策略假設與風險的情況下連接任何帳戶。  
* 不應使用無法承受損失的資金。  
* 不得將回測、paper 或 shadow 結果描述為確定的未來收益。

市場交易可能造成部分或全部本金損失。

使用者應自行承擔使用本軟體、資料、策略與研究結果所產生的風險。

---

## **授權**

本專案採用 [Apache License 2.0](LICENSE)。

---

## **專案原則**

TradeGuard 的成功標準不是：

> 找到回測報酬最高的策略。

TradeGuard 的成功標準是：

> 以可驗證、可重現、風險透明且不誤導使用者的方式，判斷一個股票或加密貨幣策略是否值得繼續研究、進入 paper trading、進入 shadow monitoring，或應立即停止。

任何新功能若無法改善至少一項下列能力，應重新評估其必要性：

* 研究可信度。  
* 資料完整性。  
* 結果可重現性。  
* 風險透明度。  
* 使用者安全。  
* 維運可靠性。  
* 稽核能力。  
* 決策品質。
