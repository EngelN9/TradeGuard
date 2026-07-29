# **TradeGuard Codex Prompts — Connected Release with Reproducible Evidence**

## **0\. Connected Release 定義**

本提示詞組中的 **Connected Release** 是指：

1. 可從乾淨 clone 建立一致的開發與執行環境。  
2. 可連接至少一個真實股票公開市場資料來源。  
3. 可連接至少一個真實加密貨幣公開市場資料來源。  
4. 可透過內部 deterministic paper broker 執行股票與加密貨幣模擬交易。  
5. 至少具備一個外部非正式交易整合：  
   * 券商 paper account；  
   * 交易所 sandbox／testnet；  
   * 或 read-only account adapter。  
6. 支援：  
   * 資料品質驗證；  
   * 確定性回測；  
   * 成本與成交模型；  
   * baseline 策略；  
   * walk-forward；  
   * 樣本外驗證；  
   * 風險分析；  
   * paper／shadow 監控；  
   * 對帳；  
   * API；  
   * Web dashboard。  
7. 所有 connected integration 均不得具備正式交易、提款或資產轉移權限。  
8. Release 必須包含可重現證據包。  
9. Release 必須能在沒有外部秘密的情況下，以 fixtures、recorded responses 或 mock adapters 完成主要 CI。  
10. 需要秘密的 connected smoke tests 必須：  
    * 明確標記為 opt-in；  
    * 使用最小權限；  
    * 不在 fork Pull Request 執行；  
    * 不輸出秘密；  
    * 不成為一般 CI 的必要條件。

第一個 Connected Release 建議版本：

v0.1.0

最高允許環境：

shadow

禁止環境：

canary  
live

---

# **每次 Codex 任務共同前置提示詞**

每次開始新的 Codex 任務時，先將以下內容與對應 Prompt 一起交給 Codex。

你正在開發 TradeGuard。

開始前必須完整閱讀：

1\. 根目錄 AGENTS.md  
2\. README.md  
3\. CONTRIBUTING.md  
4\. SECURITY.md  
5\. 目標目錄內所有更具體的 AGENTS.md  
6\. 與本次修改相關的程式碼、測試、ADR、RFC 與文件

本次工作的共同限制：

\- 使用獨立 Git branch 或 worktree。  
\- 不要直接修改 main。  
\- 不要 push、merge 或建立 release，除非本 Prompt 明確要求。  
\- 不得新增 canary 或 live trading。  
\- 不得建立 make live、live.yaml 或任何可送出正式訂單的隱藏路徑。  
\- 不得要求、產生、提交或輸出正式 API key。  
\- 不得使用具有提款、轉帳、子帳戶管理或 API key 管理權限的憑證。  
\- 不得將外部未知狀態推測為成功。  
\- 不得為了讓測試通過而刪除測試、放寬風控、忽略成本、增加不合理容差或吞掉例外。  
\- 不得捏造測試結果、資料、回測績效、connected smoke-test 證據或 release 證據。  
\- 若必要前置條件不存在，請標記 BLOCKED，提供缺口與最小解除方式，不要虛構完成。  
\- 優先採用模組化單體，不要過早拆分微服務。  
\- 所有新行為都必須有測試。  
\- 所有 bug 修復都必須有 regression test。  
\- 所有外部輸入都必須經 schema validation。  
\- 所有權威財務數值使用 Decimal 或資料庫明確 decimal 型別。  
\- 所有權威時間使用 timezone-aware UTC。  
\- 所有研究、回測、replay 與 validation 必須可產生 run manifest。  
\- Connected tests 必須與 offline deterministic tests 分離。  
\- Release 證據不得包含秘密、帳戶識別資訊或不可公開資料。

修改前先輸出：

Objective  
Current repository status  
Assumptions  
Human decisions required  
Files expected to change  
Validation plan  
Risk impact  
Rollback approach

完成後輸出：

Summary  
Files changed  
Behavior changes  
Architecture decisions  
Risk impact  
Security impact  
Tests executed  
Test results  
Evidence generated  
Known limitations  
Rollback plan  
Remaining work  
Promotion gate result: PASS / FAIL / BLOCKED

---

# **Prompt 0 — Repository Assessment 與 Connected Release Contract**

本次任務只進行 repository assessment、release contract 定義與工作拆分。

不要修改應用程式程式碼。  
不要安裝新的 runtime dependency。  
不要連接任何外部市場、券商或交易所。  
不要要求任何 API key。

請完成以下工作：

1\. 完整盤點 repository：  
   \- 檔案與目錄  
   \- Git 狀態  
   \- 現有程式碼  
   \- 測試  
   \- CI  
   \- Docker  
   \- 設定  
   \- 文件  
   \- 資料模型  
   \- API  
   \- Web dashboard  
   \- adapters  
   \- security controls

2\. 將目前狀態對照：  
   \- AGENTS.md  
   \- README.md  
   \- CONTRIBUTING.md  
   \- SECURITY.md  
   \- Connected Release 定義

3\. 建立：

   docs/release/connected-release-v1.md  
   docs/status/implementation-matrix.md  
   docs/architecture/system-context.md  
   docs/adr/0001-connected-release-scope.md

4\. connected-release-v1.md 必須定義：

   \- release 名稱與版本  
   \- 支援市場  
   \- 支援環境  
   \- 明確非目標  
   \- 必要功能  
   \- 必要 adapters  
   \- offline CI 要求  
   \- opt-in connected test 要求  
   \- security gates  
   \- reproducibility gates  
   \- data-quality gates  
   \- validation gates  
   \- risk gates  
   \- API 與 dashboard gates  
   \- release artifact  
   \- evidence bundle  
   \- rollback 條件  
   \- 不得宣稱的能力

5\. 對 adapters 提出候選方案，但不得直接決定未經核准的供應商。

   分別列出：

   \- 股票公開市場資料來源候選  
   \- 加密貨幣公開 REST／WebSocket 來源候選  
   \- 股票 paper／read-only adapter 候選  
   \- 加密貨幣 sandbox／read-only adapter 候選

   對每個候選評估：

   \- 是否需要憑證  
   \- 是否有免費或測試環境  
   \- 授權與使用限制  
   \- rate limit  
   \- 歷史資料能力  
   \- 即時資料能力  
   \- paper／sandbox 能力  
   \- Python 支援  
   \- 維護風險  
   \- 地區限制  
   \- 是否適合公開 CI

6\. 建立可執行的工作拆分：

   \- Issue title  
   \- 目的  
   \- 範圍  
   \- 不在範圍內  
   \- 前置依賴  
   \- 預計修改檔案  
   \- 驗收標準  
   \- 測試  
   \- 可重現證據  
   \- 安全風險  
   \- rollback  
   \- promotion gate

7\. implementation-matrix.md 對每項標記：

   \- COMPLETE  
   \- PARTIAL  
   \- MISSING  
   \- BLOCKED  
   \- NOT APPLICABLE

8\. 定義 release evidence 目錄：

   artifacts/evidence/\<release-version\>/

   至少規劃：

   \- build/  
   \- tests/  
   \- data/  
   \- backtests/  
   \- validation/  
   \- risk/  
   \- adapters/  
   \- api/  
   \- dashboard/  
   \- security/  
   \- reproducibility/  
   \- sbom/  
   \- release/

9\. 輸出：

   Repository status  
   Compliance matrix  
   Critical gaps  
   Adapter decision matrix  
   Human decisions required  
   Proposed issues  
   Dependency graph  
   Recommended first implementation issue  
   Connected Release exit criteria

本 Prompt 的 promotion gate：

\- Connected Release contract 完整。  
\- 所有未決外部供應商決策明確列出。  
\- 工作可被拆成小型、可獨立審查的 Issues。  
\- 不得宣稱 repository 已 connected、可交易或 production-ready。

---

# **Prompt 1 — Repository Bootstrap、工具鏈與 CI 基線**

只有在 Prompt 0 完成並審查後執行。

本次任務建立可重現的 repository bootstrap，不實作交易策略，不連接外部服務。

請完成：

1\. 建立 Python 3.12 typed project：  
   \- pyproject.toml  
   \- uv.lock  
   \- src/tradeguard/  
   \- tests/  
   \- package metadata

2\. 設定：  
   \- ruff  
   \- mypy 或 pyright  
   \- pytest  
   \- hypothesis  
   \- coverage  
   \- pre-commit

3\. 建立 Makefile，至少提供：

   make setup  
   make format  
   make lint  
   make typecheck  
   make test  
   make test-unit  
   make test-property  
   make test-integration  
   make test-contract  
   make test-replay  
   make test-connected  
   make evidence  
   make dev-up  
   make dev-down

4\. make test-connected：  
   \- 必須為 opt-in。  
   \- 未設定必要環境變數時應安全地 skip。  
   \- 不得默默改用正式 endpoint。  
   \- 不得在一般 CI 或 fork PR 執行。

5\. 建立：  
   \- .gitignore  
   \- .env.example  
   \- CODEOWNERS  
   \- pull request template  
   \- issue templates  
   \- Dockerfile  
   \- docker-compose.yml

6\. Docker Compose 至少包含：  
   \- PostgreSQL  
   \- backend API skeleton  
   \- worker skeleton  
   \- mock market-data service  
   \- deterministic paper broker skeleton  
   \- dashboard placeholder

7\. 建立 GitHub Actions：  
   \- format  
   \- lint  
   \- typecheck  
   \- unit tests  
   \- property tests  
   \- integration tests  
   \- contract tests  
   \- secret scan  
   \- dependency scan  
   \- container scan  
   \- workflow permission validation

8\. GitHub Actions 必須：  
   \- 使用最小 permissions。  
   \- 不讓不可信 PR 取得 secrets。  
   \- 固定第三方 Actions 至完整 commit SHA。  
   \- 不使用高權限 pull\_request\_target 執行 PR 程式碼。

9\. 建立最小 health endpoint：  
   \- /health/live  
   \- /health/ready  
   \- 只回傳 mock 或系統狀態  
   \- 不暴露 secrets 或內部 stack trace

10\. 建立 evidence 產生骨架：  
    \- 測試結果  
    \- coverage  
    \- tool versions  
    \- dependency lock hash  
    \- Git SHA  
    \- container build metadata

11\. 提供 fresh-clone 驗證腳本：  
    scripts/verify\_clean\_bootstrap.sh

驗收標準：

\- 從乾淨 clone 可完成 dependency install。  
\- format、lint、typecheck、tests 通過。  
\- Docker Compose 可啟動 skeleton。  
\- health endpoints 可用。  
\- evidence skeleton 可產生。  
\- 無 live 功能。  
\- 無真實 secret。

---

# **Prompt 2 — Domain Events、設定系統與 Run Manifest**

本次任務只實作核心 domain models、versioned configuration 與 run manifest。

不要實作策略。  
不要實作外部 adapters。  
不要實作正式下單。

請完成：

1\. 建立 immutable、versioned domain events。

至少包含：

\- Quote  
\- TradeTick  
\- Bar  
\- CorporateAction  
\- InstrumentMetadataChanged  
\- MarketSessionChanged  
\- DataQualityAlert  
\- FeatureSnapshot  
\- Signal  
\- TargetPosition  
\- TradeProposal  
\- RiskDecision  
\- PaperOrder  
\- PaperFill  
\- PositionSnapshot  
\- AccountSnapshot  
\- PnLSnapshot  
\- ExposureSnapshot  
\- ReconciliationDifference  
\- DriftAlert  
\- HealthStatusChanged  
\- ConfigurationChanged  
\- AuditEvent

2\. 共同欄位至少包含：

\- event\_id  
\- schema\_version  
\- event\_type  
\- source  
\- asset\_class  
\- venue  
\- symbol  
\- event\_time\_utc  
\- ingest\_time\_utc  
\- sequence\_number  
\- correlation\_id  
\- causation\_id  
\- run\_id  
\- payload\_checksum

3\. 實作：

\- canonical serialization  
\- deterministic checksum  
\- timezone-aware UTC validation  
\- Decimal validation  
\- schema-version validation  
\- backward-compatible event parsing policy

4\. 建立 versioned configuration：

\- base  
\- environment  
\- market  
\- venue  
\- data  
\- strategy  
\- portfolio  
\- risk  
\- cost  
\- monitoring  
\- alerting

5\. 支援環境只能是：

\- research  
\- backtest  
\- replay  
\- paper  
\- shadow

其他值必須驗證失敗。

6\. 建立 redacted configuration：  
   \- deterministic config hash  
   \- secret field redaction  
   \- effective config inspection  
   \- configuration audit event

7\. 實作 RunManifest，至少包含：

\- run\_id  
\- run\_type  
\- strategy\_id  
\- strategy\_version  
\- Git SHA  
\- dirty-worktree flag  
\- config hash  
\- dataset manifests  
\- date range  
\- universe  
\- random seed  
\- Python version  
\- platform  
\- dependency lock hash  
\- cost-model version  
\- execution-model version  
\- started\_at  
\- completed\_at  
\- result checksum  
\- warnings  
\- validation failures

8\. 若 Git worktree 不乾淨：  
   \- manifest 必須明確記錄。  
   \- release qualification 必須拒絕使用該結果。

9\. 建立 property tests：  
   \- 相同輸入產生相同 canonical representation。  
   \- 相同輸入產生相同 checksum。  
   \- secret 不出現在 redacted output。  
   \- naive datetime 被拒絕。  
   \- 未允許環境被拒絕。

10\. 建立 machine-readable JSON Schema 或 OpenAPI-compatible schema artifacts。

驗收證據：

\- event schema snapshot  
\- config schema snapshot  
\- deterministic checksum test  
\- redaction test  
\- sample run manifest

---

# **Prompt 3 — 資料基礎、Manifest 與品質閘門**

本次任務建立股票與加密貨幣共享資料基礎，不連接真實外部供應商。

請完成：

1\. 建立 canonical market-data models：  
   \- Quote  
   \- Trade  
   \- OHLCV Bar  
   \- Instrument metadata  
   \- Market session  
   \- Corporate action

2\. Instrument metadata 至少包含：  
   \- asset\_class  
   \- venue  
   \- symbol  
   \- canonical\_symbol  
   \- currency 或 quote\_asset  
   \- tick\_size  
   \- step\_size  
   \- lot\_size  
   \- minimum\_quantity  
   \- minimum\_notional  
   \- timezone  
   \- session\_calendar  
   \- active\_from  
   \- active\_to  
   \- known\_at  
   \- metadata\_version

3\. 建立 DatasetManifest：  
   \- dataset\_id  
   \- source  
   \- schema\_version  
   \- asset\_class  
   \- symbols  
   \- date range  
   \- row count  
   \- partition information  
   \- checksums  
   \- created\_at  
   \- ingested\_at  
   \- licensing notes  
   \- missing intervals  
   \- corrections  
   \- parent dataset  
   \- transformation graph

4\. 原始資料採 append-only 或 content-addressed 方式。

5\. 建立資料品質檢查：

通用：  
\- missing  
\- duplicate  
\- out-of-order  
\- future timestamp  
\- stale content  
\- invalid OHLC  
\- negative volume  
\- abnormal price jump  
\- inconsistent schema  
\- symbol mapping conflict

股票：  
\- trading-session violation  
\- half-day handling  
\- corporate-action mismatch  
\- split discontinuity  
\- delisted-symbol handling  
\- point-in-time universe violation

加密貨幣：  
\- 24/7 gap  
\- precision mismatch  
\- minimum-notional mismatch  
\- venue-maintenance interval  
\- bid greater than ask  
\- spread anomaly  
\- quote-asset inconsistency

6\. 品質結果至少包含：

\- PASS  
\- WARN  
\- FAIL  
\- QUARANTINED

7\. FAIL 或 QUARANTINED 資料不得進入正式 validation evidence。

8\. 建立 synthetic fixtures：  
   \- 正常資料  
   \- 缺口  
   \- duplicate  
   \- out-of-order  
   \- bad tick  
   \- stock split  
   \- symbol change  
   \- delisting  
   \- crypto maintenance  
   \- stale timestamp  
   \- fresh timestamp with stale content

9\. 建立資料轉換 lineage。

10\. 建立 CLI：

tradeguard data validate  
tradeguard data manifest  
tradeguard data inspect

驗收證據：

\- fixture manifests  
\- quality reports  
\- quarantined dataset example  
\- deterministic transformed-dataset checksum  
\- lineage graph

---

# **Prompt 4 — 股票市場資料 Connected Adapter**

只有在 Prompt 0 的股票資料來源決策完成後執行。

本次任務實作一個股票公開市場資料 adapter。

不得加入正式券商交易功能。  
不得假設免費資料可用於未經授權的商業再散布。  
不得將 provider-specific schema 洩漏至核心 domain。

請完成：

1\. 建立 provider-neutral EquityMarketDataAdapter protocol。

能力至少包含：

\- instrument metadata  
\- historical bars  
\- latest quote 或 latest bar  
\- market calendar  
\- timezone  
\- symbol normalization  
\- corporate-action retrieval 或明確 unsupported capability

2\. 實作選定股票資料來源 adapter。

3\. 建立 capability declaration：  
   \- public  
   \- authenticated  
   \- historical  
   \- delayed  
   \- real-time  
   \- corporate actions  
   \- rate limits  
   \- licensing constraints

4\. 實作：  
   \- timeout  
   \- bounded retry  
   \- backoff  
   \- rate-limit handling  
   \- schema validation  
   \- endpoint allowlist  
   \- response-size limit  
   \- symbol normalization  
   \- UTC conversion  
   \- provider request ID logging  
   \- redacted error handling

5\. 不得：  
   \- 無限 retry  
   \- 驗證失敗後仍使用資料  
   \- 將缺失資料補成零  
   \- 將未知交易日狀態視為開市  
   \- 自動切換至未核准 provider

6\. 建立：  
   \- recorded contract fixtures  
   \- offline contract tests  
   \- opt-in connected smoke test  
   \- provider schema-drift test

7\. connected smoke test 至少驗證：  
   \- 可取得一個核准標的的資料  
   \- timestamp 合法  
   \- schema 合法  
   \- manifest 可產生  
   \- data-quality gate 通過  
   \- 無 secret 輸出

8\. 若 provider 需要 credential：  
   \- 只接受 read-only 或 data-only credential。  
   \- 未設定時安全 skip。  
   \- 不得將 connected test 設為一般 CI 必要條件。

9\. 建立文件：  
   docs/adapters/equity-market-data.md

驗收證據：

\- adapter capability report  
\- recorded response checksum  
\- offline contract-test result  
\- connected smoke-test result或明確 BLOCKED 記錄  
\- sample dataset manifest  
\- licensing and usage notes

---

# **Prompt 5 — 加密貨幣 REST／WebSocket Connected Adapter**

只有在 Prompt 0 的加密貨幣資料來源決策完成後執行。

本次任務實作一個加密貨幣公開市場資料 adapter。

不得要求交易權限。  
不得要求提款權限。  
不得新增正式下單。

請完成：

1\. 建立 CryptoMarketDataAdapter protocol。

能力至少包含：

\- instrument metadata  
\- supported trading pairs  
\- historical bars  
\- public trades  
\- best bid／ask  
\- REST health  
\- WebSocket stream  
\- venue maintenance status  
\- rate-limit metadata

2\. 實作選定 venue 的 public REST adapter。

3\. 實作選定 venue 的 public WebSocket adapter。

4\. WebSocket 必須處理：  
   \- reconnect  
   \- bounded backoff  
   \- duplicate events  
   \- missing sequence  
   \- out-of-order events  
   \- heartbeat  
   \- stale stream  
   \- resubscription  
   \- schema drift  
   \- controlled shutdown

5\. 實作 trading-pair metadata：  
   \- base asset  
   \- quote asset  
   \- tick size  
   \- step size  
   \- minimum quantity  
   \- minimum notional  
   \- trading status  
   \- metadata timestamp

6\. 未知 sequence、stale stream 或 metadata 衝突時：  
   \- 產生 DataQualityAlert。  
   \- 將該 stream 標記 NOT\_TRADABLE。  
   \- 不得推測缺失事件。

7\. 建立：  
   \- recorded REST fixtures  
   \- recorded WebSocket fixtures  
   \- offline contract tests  
   \- reconnect tests  
   \- sequence-gap replay  
   \- opt-in connected smoke tests

8\. connected smoke test 至少驗證：  
   \- instrument metadata  
   \- REST market snapshot  
   \- WebSocket 至少若干事件  
   \- timestamp 與 sequence  
   \- manifest  
   \- data-quality result  
   \- clean shutdown

9\. 建立文件：  
   docs/adapters/crypto-market-data.md

驗收證據：

\- venue capability report  
\- REST fixture checksum  
\- WebSocket fixture checksum  
\- reconnect evidence  
\- sequence-gap rejection evidence  
\- connected smoke-test result或明確 BLOCKED 記錄

---

# **Prompt 6 — Deterministic Backtester、帳本與成交模型**

本次任務建立確定性事件驅動回測核心。

不要加入策略最佳化。  
不要連接正式帳戶。  
不要使用理想化成交讓績效變好。

請完成：

1\. 建立 deterministic event loop。

排序規則必須明確處理：  
\- event time  
\- ingest time  
\- sequence number  
\- deterministic tie-breaker

2\. 建立 portfolio ledger：  
   \- cash  
   \- positions  
   \- average cost  
   \- realized PnL  
   \- unrealized PnL  
   \- fees  
   \- taxes  
   \- corporate actions  
   \- asset and currency balances

3\. 建立 execution models：  
   \- market order  
   \- limit order  
   \- partial fill  
   \- non-fill  
   \- rejection  
   \- latency  
   \- spread  
   \- slippage  
   \- market impact  
   \- minimum notional  
   \- tick size  
   \- step size  
   \- market halt  
   \- venue maintenance

4\. 股票與加密貨幣成本模型必須分離。

股票模型至少考慮：  
\- commission  
\- tax  
\- session  
\- gap  
\- lot size  
\- corporate action

加密貨幣模型至少考慮：  
\- maker/taker fee  
\- 24/7 session  
\- spread  
\- precision  
\- minimum notional  
\- venue maintenance

5\. 建立 conservative defaults。

6\. 禁止：  
   \- 同一收盤資料產生訊號並以同一收盤價無延遲成交。  
   \- limit order 無條件成交。  
   \- 超出 bar range 的理想成交。  
   \- 忽略 partial fill。  
   \- 忽略費用。

7\. 建立：  
   \- cash-conservation property tests  
   \- asset-conservation property tests  
   \- duplicate-fill idempotency tests  
   \- corporate-action tests  
   \- deterministic replay tests  
   \- look-ahead prevention tests  
   \- precision boundary tests

8\. 建立 CLI：

tradeguard backtest run  
tradeguard replay run  
tradeguard backtest inspect

9\. 每次執行產生：  
   \- run manifest  
   \- order ledger  
   \- fill ledger  
   \- position ledger  
   \- PnL series  
   \- result checksum  
   \- warnings

驗收證據：

\- 重複執行結果 checksum 相同  
\- cash and asset conservation reports  
\- look-ahead rejection example  
\- partial-fill replay  
\- stock split replay  
\- crypto maintenance replay

---

# **Prompt 7 — 策略 Adapter 與 Baseline Strategies**

本次任務建立既有策略的統一 adapter，並加入可審查的 baseline strategies。

Baseline 的用途是驗證系統，不得宣稱可獲利。

請完成：

1\. 建立 StrategyProtocol：  
   \- strategy\_id  
   \- strategy\_version  
   \- supported\_asset\_classes  
   \- required\_data  
   \- parameter schema  
   \- warmup requirement  
   \- initialize  
   \- on\_event  
   \- finalize

2\. 策略只能輸出：  
   \- Signal  
   \- TargetPosition  
   \- TradeProposal

3\. 策略不得：  
   \- 直接送單  
   \- 存取 broker 或 exchange credentials  
   \- 靜默下載資料  
   \- 靜默呼叫 LLM  
   \- 修改風險設定  
   \- 使用未宣告資料  
   \- 使用未來資料

4\. 建立股票 baseline：  
   \- buy and hold  
   \- moving-average trend  
   \- simple mean reversion

5\. 建立加密貨幣 baseline：  
   \- buy and hold  
   \- volatility-scaled trend  
   \- breakout

6\. 每個策略提供：  
   \- strategy specification  
   \- parameters  
   \- assumptions  
   \- applicable market  
   \- unsupported market  
   \- benchmark  
   \- known limitations  
   \- failure modes  
   \- tests

7\. 建立策略 contract tests。

8\. 建立參數 canonicalization 與 strategy-version hashing。

9\. 建立 strategy registry，但不得允許未審查的任意 Python package 自動執行。

10\. 若支援自訂策略：  
    \- 第一版只允許 trusted local code。  
    \- 明確標示不存在安全 Python sandbox。  
    \- 不得讓上傳策略取得 secrets。

驗收證據：

\- strategy contract report  
\- baseline backtest manifests  
\- strategy-version checksums  
\- deterministic strategy results  
\- unsupported-market rejection test

---

# **Prompt 8 — Validation Engine 與過度擬合防護**

本次任務建立策略驗證引擎。

不得以單一回測績效作為通過依據。  
不得自動批准 strategy promotion。

請完成：

1\. Dataset split：  
   \- training  
   \- validation  
   \- test  
   \- out-of-sample

2\. Walk-forward：  
   \- expanding window  
   \- rolling window  
   \- configurable train/validation/test periods  
   \- refit schedule  
   \- split manifest

3\. 防止：  
   \- look-ahead  
   \- label leakage  
   \- feature leakage  
   \- future-universe leakage  
   \- repeated tuning on test set

4\. 實作：  
   \- benchmark comparison  
   \- parameter sensitivity  
   \- start-date sensitivity  
   \- end-date sensitivity  
   \- universe sensitivity  
   \- fee sensitivity  
   \- slippage sensitivity  
   \- signal-delay sensitivity  
   \- missing-data stress  
   \- regime segmentation

5\. 統計工具至少包含：  
   \- bootstrap  
   \- block bootstrap  
   \- confidence intervals  
   \- multiple-testing warning  
   \- experiment-count tracking

6\. 進階方法可在適用時實作：  
   \- purging  
   \- embargo  
   \- deflated Sharpe ratio  
   \- probability of backtest overfitting  
   \- combinatorial purged cross-validation

7\. 每項統計方法必須記錄：  
   \- assumptions  
   \- parameters  
   \- limitations  
   \- failure conditions

8\. 建立 validation result：  
   \- PASS  
   \- CONDITIONAL  
   \- FAIL  
   \- INSUFFICIENT\_EVIDENCE

9\. FAIL 或 INSUFFICIENT\_EVIDENCE 不得進入 paper promotion。

10\. 建立 CLI：

tradeguard validate run  
tradeguard validate inspect  
tradeguard validate compare

11\. 產生 machine-readable 與 human-readable 報告。

驗收證據：

\- walk-forward split manifest  
\- untouched out-of-sample evidence  
\- cost-sensitivity report  
\- parameter-stability report  
\- multiple-testing warning example  
\- intentionally overfit strategy rejection fixture

---

# **Prompt 9 — Independent Risk Engine**

本次任務建立獨立於策略的風險引擎。

策略提出建議，風險引擎負責接受、縮減、拒絕或要求人工審查。

請完成：

1\. RiskDecision：  
   \- ACCEPT  
   \- ADJUST  
   \- REJECT  
   \- HALT  
   \- HUMAN\_REVIEW\_REQUIRED

2\. Pre-trade research／paper risk checks：  
   \- single-symbol exposure  
   \- gross exposure  
   \- net exposure  
   \- strategy capital limit  
   \- turnover  
   \- concentration  
   \- sector or cluster exposure  
   \- venue exposure  
   \- quote-asset exposure  
   \- liquidity  
   \- participation  
   \- stale data  
   \- market session  
   \- minimum notional  
   \- precision  
   \- drawdown gate

3\. Portfolio risk：  
   \- volatility  
   \- covariance  
   \- shrinkage covariance  
   \- correlation  
   \- VaR  
   \- Expected Shortfall  
   \- drawdown  
   \- stressed correlation  
   \- liquidity-adjusted exposure  
   \- venue concentration  
   \- stablecoin risk  
   \- currency risk

4\. 不得只依賴：  
   \- normal-distribution VaR  
   \- Sharpe ratio  
   \- single covariance estimate

5\. 建立壓力情境：  
   \- equity opening gap  
   \- trading halt  
   \- market crash  
   \- volatility spike  
   \- correlation to one  
   \- liquidity collapse  
   \- crypto venue outage  
   \- stablecoin depeg  
   \- spread expansion  
   \- stale data  
   \- conflicting data sources

6\. 所有 risk limits 必須：  
   \- versioned  
   \- schema validated  
   \- fail closed  
   \- audited  
   \- included in config hash

7\. 建立 property tests：  
   \- limit 不可被策略繞過  
   \- stale data 不得 ACCEPT  
   \- unknown market state 不得增加風險  
   \- exposure calculation consistency  
   \- risk scaling monotonicity where applicable

8\. 建立 CLI：

tradeguard risk evaluate  
tradeguard risk stress  
tradeguard risk report

驗收證據：

\- risk-limit matrix  
\- stress-scenario reports  
\- stale-data rejection  
\- venue-risk rejection  
\- stablecoin-depeg response  
\- property-test results

---

# **Prompt 10 — Experiment Store、報告與 Evidence Pipeline**

本次任務建立研究執行紀錄、報告與 release evidence pipeline。

請完成：

1\. 建立 Experiment model：  
   \- experiment\_id  
   \- parent\_experiment\_id  
   \- strategy  
   \- parameters  
   \- dataset  
   \- run manifests  
   \- validation result  
   \- risk result  
   \- artifacts  
   \- status  
   \- timestamps

2\. 建立 artifact store abstraction。  
   第一版可使用本機 filesystem，但必須：  
   \- content-addressed  
   \- checksum verified  
   \- immutable after finalization  
   \- no secret content  
   \- path traversal safe

3\. 建立研究報告：

至少包含：  
\- executive summary  
\- strategy specification  
\- data source  
\- data-quality result  
\- point-in-time statement  
\- benchmark  
\- cost model  
\- execution model  
\- in-sample  
\- out-of-sample  
\- walk-forward  
\- robustness  
\- stress tests  
\- risk  
\- limitations  
\- failure conditions  
\- run manifest  
\- checksums

4\. 報告必須同時呈現：  
   \- favorable results  
   \- unfavorable results  
   \- failed splits  
   \- warnings  
   \- missing evidence

5\. 建立 evidence command：

tradeguard evidence collect  
tradeguard evidence verify  
tradeguard evidence index

6\. Evidence index 至少包含：  
   \- artifact path  
   \- artifact type  
   \- checksum  
   \- producer  
   \- run ID  
   \- Git SHA  
   \- created\_at  
   \- validation status

7\. 建立 release evidence schema。

8\. 建立 golden-file tests 或 equivalent snapshot validation。

9\. 建立 evidence tampering test：  
   \- 修改 artifact 後驗證必須失敗。

驗收證據：

\- sample experiment  
\- complete report  
\- evidence index  
\- checksum verification  
\- tampering rejection  
\- report reproducibility result

---

# **Prompt 11 — Deterministic Paper Broker 與外部非正式交易 Adapter**

本次任務建立內部 deterministic paper broker，以及一個經核准的外部 paper、sandbox 或 read-only adapter。

不得使用正式交易權限。  
不得使用提款或轉帳權限。

第一部分：Internal Paper Broker

1\. 建立 deterministic paper broker：  
   \- submit  
   \- acknowledge  
   \- reject  
   \- partial fill  
   \- cancel  
   \- expire  
   \- market halt  
   \- venue maintenance  
   \- rate-limit simulation  
   \- connection-loss simulation  
   \- unknown-state simulation

2\. 建立 order state machine：  
   \- CREATED  
   \- VALIDATED  
   \- REJECTED  
   \- SUBMITTED  
   \- ACKNOWLEDGED  
   \- PARTIALLY\_FILLED  
   \- FILLED  
   \- CANCEL\_PENDING  
   \- CANCELED  
   \- EXPIRED  
   \- UNKNOWN

3\. 實作 idempotency keys。

4\. UNKNOWN 狀態不得自動重送相同風險。

5\. 建立 restart and replay tests。

第二部分：External Non-Live Adapter

6\. 實作 Prompt 0 核准的其中一個：  
   \- broker paper adapter  
   \- exchange sandbox adapter  
   \- read-only account adapter

7\. Adapter 必須：  
   \- capability declaration  
   \- explicit environment verification  
   \- credential-scope validation where possible  
   \- endpoint allowlist  
   \- timeout  
   \- bounded retry  
   \- idempotency  
   \- external ID preservation  
   \- schema validation  
   \- redacted logs  
   \- unknown-state handling

8\. 若憑證權限超過允許範圍：  
   \- 拒絕啟動。  
   \- 不保存該憑證。  
   \- 顯示撤銷建議。

9\. 建立 offline recorded contract tests。

10\. 建立 opt-in connected smoke test。

11\. Connected smoke test 不得：  
    \- 送出正式訂單。  
    \- 使用真實資金。  
    \- 使用提款權限。  
    \- 在 fork PR 執行。

驗收證據：

\- paper order lifecycle  
\- duplicate-submit prevention  
\- restart recovery  
\- unknown-state handling  
\- external adapter capability report  
\- offline contract test  
\- connected smoke test或明確 BLOCKED 記錄

---

# **Prompt 12 — Paper／Shadow Monitoring、對帳與 Drift**

本次任務建立 paper／shadow monitoring、對帳與 drift detection。

請完成：

1\. Monitoring ingestion：  
   \- market events  
   \- strategy signals  
   \- target positions  
   \- paper orders  
   \- paper fills  
   \- positions  
   \- balances  
   \- PnL  
   \- risk decisions  
   \- health events

2\. 建立 reconciliation：

比較：  
\- internal cash  
\- external or paper cash  
\- positions  
\- orders  
\- fills  
\- fees  
\- realized PnL  
\- unrealized PnL

狀態：  
\- MATCHED  
\- MISMATCHED  
\- UNKNOWN  
\- STALE  
\- UNAVAILABLE

3\. UNKNOWN、STALE、UNAVAILABLE：  
   \- 不得顯示系統正常。  
   \- 不得允許 promotion。  
   \- 必須產生告警。

4\. Drift 至少包含：  
   \- data drift  
   \- feature drift  
   \- signal drift  
   \- position drift  
   \- PnL drift  
   \- cost drift  
   \- slippage drift  
   \- latency drift  
   \- fill-rate drift  
   \- regime drift  
   \- strategy-version drift

5\. 告警必須包含：  
   \- baseline  
   \- current value  
   \- threshold  
   \- observation window  
   \- severity  
   \- possible causes  
   \- recommended action

6\. 建立 alert levels：  
   \- INFO  
   \- WARNING  
   \- HIGH  
   \- CRITICAL

7\. CRITICAL 必須阻止新的 promotion。

8\. 建立 replay tests：  
   \- duplicate fill  
   \- missing fill  
   \- stale account snapshot  
   \- external mismatch  
   \- delayed market data  
   \- strategy-version mismatch  
   \- cost drift  
   \- venue outage

9\. 建立 CLI：

tradeguard monitor status  
tradeguard reconcile run  
tradeguard drift report  
tradeguard alerts list

驗收證據：

\- reconciliation report  
\- mismatch example  
\- stale-state example  
\- drift report  
\- critical-alert promotion block  
\- restart recovery evidence

---

# **Prompt 13 — FastAPI、OpenAPI 與 Web Dashboard**

本次任務建立 connected release 所需的 API 與 Web dashboard。

前端不得保存秘密。  
前端不得直接連接交易所或券商。  
前端不得自行覆寫權威風控結果。

第一部分：API

1\. 建立 FastAPI endpoints：

\- health  
\- environments  
\- datasets  
\- data-quality reports  
\- strategies  
\- experiments  
\- backtests  
\- validation reports  
\- risk reports  
\- paper orders  
\- paper fills  
\- positions  
\- reconciliation  
\- drift  
\- alerts  
\- evidence  
\- release status

2\. 所有寫入操作必須：  
   \- schema validated  
   \- authenticated where applicable  
   \- authorized  
   \- audited  
   \- idempotent where applicable

3\. 第一版高風險操作只允許：  
   \- start research run  
   \- start backtest  
   \- start validation  
   \- start paper run  
   \- stop paper run  
   \- acknowledge alert

4\. 禁止：  
   \- live order  
   \- withdrawal  
   \- transfer  
   \- risk-limit bypass  
   \- delete audit evidence

5\. 產生並固定 OpenAPI contract snapshot。

第二部分：Web Dashboard

6\. 建立頁面：  
   \- Overview  
   \- Data  
   \- Strategies  
   \- Backtests  
   \- Validation  
   \- Risk  
   \- Paper  
   \- Reconciliation  
   \- Drift  
   \- Alerts  
   \- Evidence  
   \- Release Readiness

7\. 所有頁面必須明確顯示環境：  
   \- research  
   \- backtest  
   \- replay  
   \- paper  
   \- shadow

8\. 顯示：  
   \- data freshness  
   \- latest run  
   \- manifest status  
   \- validation status  
   \- risk status  
   \- reconciliation status  
   \- connected adapter status  
   \- evidence completeness

9\. 不得將：  
   \- backtest  
   \- paper  
   \- shadow

標示為 live。

10\. 建立：  
    \- API contract tests  
    \- authorization tests  
    \- E2E tests  
    \- stale and unknown UI-state tests  
    \- responsive tests  
    \- accessibility baseline tests

驗收證據：

\- OpenAPI snapshot  
\- API contract-test report  
\- E2E report  
\- dashboard screenshots with synthetic data  
\- explicit environment-label evidence  
\- unknown-state UI evidence

---

# **Prompt 14 — Security、Observability 與 Release Engineering**

本次任務進行 connected release 的安全與營運強化。

請完成：

1\. Threat model：

至少涵蓋：  
\- secret leakage  
\- malicious strategy code  
\- SSRF  
\- untrusted market-data response  
\- dependency compromise  
\- GitHub Actions compromise  
\- cross-environment confusion  
\- paper/live endpoint confusion  
\- audit tampering  
\- evidence tampering  
\- prompt injection if LLM components exist

2\. 建立文件：  
   \- docs/security/threat-model.md  
   \- docs/operations/connected-adapter-runbook.md  
   \- docs/operations/incident-response.md  
   \- docs/operations/backup-and-restore.md  
   \- docs/release/release-process.md  
   \- docs/release/rollback-process.md

3\. 實作：  
   \- structured logs  
   \- correlation IDs  
   \- secret redaction  
   \- metrics  
   \- readiness  
   \- liveness  
   \- adapter health  
   \- data freshness  
   \- queue health  
   \- database health

4\. 建立：  
   \- SBOM  
   \- dependency inventory  
   \- container scan report  
   \- secret scan report  
   \- license inventory  
   \- GitHub Actions permission report

5\. Container：  
   \- non-root  
   \- read-only filesystem where feasible  
   \- no Docker socket  
   \- no embedded secret  
   \- minimal capabilities  
   \- pinned base image digest  
   \- resource limits documented

6\. Database：  
   \- migration validation  
   \- backup script  
   \- restore script  
   \- restore test  
   \- least-privilege application role

7\. 建立 security regression tests：  
   \- secret redaction  
   \- unsafe environment rejection  
   \- unauthorized endpoint  
   \- path traversal  
   \- malicious filename  
   \- oversized upload if uploads exist  
   \- SSRF allowlist  
   \- evidence tampering

8\. 建立 release build：  
   \- Python package or application artifact  
   \- container image  
   \- dashboard build  
   \- checksums  
   \- SBOM  
   \- provenance metadata where supported

驗收證據：

\- threat model  
\- security test report  
\- secret scan  
\- dependency scan  
\- container scan  
\- SBOM  
\- backup restore evidence  
\- release build checksums

---

# **Prompt 15 — Connected End-to-End Qualification**

本次任務不新增主要功能。

本次任務只執行 Connected Release qualification、修復必要缺陷，並產生完整可重現證據。

不要建立正式 release tag。  
不要隱藏失敗結果。  
若任何必要 gate 未通過，結論必須為 FAIL 或 BLOCKED。

請完成：

1\. 從乾淨 clone 建立兩個獨立環境：

   Environment A  
   Environment B

2\. 在兩個環境中使用相同：  
   \- Git SHA  
   \- dependency lock  
   \- configuration  
   \- dataset manifests  
   \- random seeds

3\. 執行 offline full qualification：

   \- format  
   \- lint  
   \- typecheck  
   \- unit  
   \- property  
   \- integration  
   \- contract  
   \- replay  
   \- E2E  
   \- security  
   \- migration  
   \- build  
   \- SBOM  
   \- evidence verification

4\. 執行股票 end-to-end：

   connected public data  
   → canonical normalization  
   → data-quality gate  
   → dataset manifest  
   → baseline strategy  
   → deterministic backtest  
   → validation  
   → risk  
   → report  
   → dashboard  
   → evidence

5\. 執行加密貨幣 end-to-end：

   connected REST／WebSocket data  
   → canonical normalization  
   → data-quality gate  
   → dataset manifest  
   → baseline strategy  
   → deterministic backtest  
   → validation  
   → risk  
   → paper broker  
   → monitoring  
   → reconciliation  
   → dashboard  
   → evidence

6\. 執行外部非正式 adapter smoke test：  
   \- paper  
   \- sandbox  
   \- 或 read-only

7\. 若 connected test 因憑證、地區、供應商或網路限制無法執行：  
   \- 標記 BLOCKED。  
   \- 保留 offline contract-test evidence。  
   \- 不得將 blocked connected test 宣稱為 PASS。

8\. Reproducibility 比對：

兩個環境中的以下結果必須一致或符合明確容差：

\- canonical dataset checksum  
\- strategy version  
\- config hash  
\- run manifest  
\- order ledger  
\- fill ledger  
\- PnL series  
\- performance metrics  
\- validation status  
\- risk status  
\- report checksum

9\. 不應強求 connected market snapshot 完全相同。

即時外部資料應保存：  
\- observation window  
\- raw response checksum  
\- normalized data checksum  
\- timestamp  
\- provider request ID  
\- data-quality result

10\. 執行 failure drills：

\- equity provider timeout  
\- crypto WebSocket disconnect  
\- stale data  
\- schema drift  
\- duplicate event  
\- missing sequence  
\- partial fill  
\- unknown order  
\- reconciliation mismatch  
\- stablecoin depeg fixture  
\- evidence tampering  
\- database restart

11\. 建立：

artifacts/evidence/v0.1.0/

並產生 index.json 與 README.md。

12\. 建立 release-readiness report：

docs/release/v0.1.0-readiness.md

必須包含：

\- gate  
\- required evidence  
\- actual evidence  
\- status  
\- owner  
\- unresolved issue  
\- waiver  
\- expiration

13\. Waiver 規則：  
   \- Security、secret、live-boundary、data-integrity、reproducibility 核心 gate 不得 waiver。  
   \- 非核心 UI 缺陷可以在明確風險評估後 waiver。  
   \- 所有 waiver 必須有 owner 與 expiration。

14\. 最終輸出：

Qualification summary  
Offline test matrix  
Connected test matrix  
Reproducibility comparison  
Failure-drill matrix  
Security gate  
Data-quality gate  
Validation gate  
Risk gate  
API/dashboard gate  
Evidence completeness  
Blocking issues  
Release recommendation: GO / NO-GO

本 Prompt 只有在所有不可 waiver gate 通過時，才可輸出 GO。

---

# **Prompt 16 — Release Candidate、Tag 與 GitHub Release 準備**

只有在 Prompt 15 結論為 GO，且所有證據由人類審查後執行。

本次任務準備 v0.1.0 Connected Release。

除非使用者明確授權，不要 push tag，不要發布 GitHub Release。

請完成：

1\. 確認：  
   \- worktree clean  
   \- target Git SHA fixed  
   \- branch approved  
   \- all required CI passed  
   \- connected qualification passed  
   \- evidence bundle verified  
   \- no unresolved critical/high security issue  
   \- no live capability  
   \- no secret  
   \- documentation current

2\. 更新：  
   \- README project status  
   \- CHANGELOG.md  
   \- docs/release/v0.1.0.md  
   \- supported capabilities  
   \- known limitations  
   \- adapter status  
   \- installation instructions  
   \- connected test instructions  
   \- rollback instructions

3\. 建立 release artifact：

   \- source archive  
   \- Python package or application bundle  
   \- container image metadata  
   \- dashboard build metadata  
   \- SBOM  
   \- checksums  
   \- evidence index  
   \- OpenAPI snapshot  
   \- migration revision  
   \- release notes

4\. 建立 RELEASE\_MANIFEST.json：

至少包含：  
\- version  
\- Git SHA  
\- build timestamp  
\- dependency lock hash  
\- container digest  
\- SBOM checksum  
\- OpenAPI checksum  
\- migration revision  
\- evidence index checksum  
\- supported environments  
\- supported adapters  
\- known limitations  
\- security status  
\- reproducibility status

5\. 建立 tag 建議：

v0.1.0

6\. 建立 annotated tag message 草稿，但不要實際建立 tag，除非使用者明確授權。

7\. 建立 GitHub Release body 草稿，必須清楚說明：

\- 這是 connected research／paper／shadow release。  
\- 不支援 live trading。  
\- 不保證獲利。  
\- 支援的股票與加密貨幣 adapters。  
\- connected test 的限制。  
\- 安全限制。  
\- 已知限制。  
\- 升級方式。  
\- 驗證 checksums。  
\- rollback。  
\- evidence bundle。

8\. 執行最後 verification：

tradeguard evidence verify  
release-manifest verification  
artifact checksum verification  
fresh-install smoke test  
container startup smoke test  
database migration smoke test  
dashboard smoke test

9\. 最終輸出：

Release candidate summary  
Target version  
Target Git SHA  
Artifacts  
Checksums  
Evidence location  
Supported capabilities  
Unsupported capabilities  
Known limitations  
Security status  
Reproducibility status  
Tag command requiring human approval  
GitHub Release draft  
Final recommendation: READY\_TO\_TAG / NOT\_READY

只有在所有驗證通過時，才能輸出 READY\_TO\_TAG。

---

# **Prompt 17 — 建立 Tag 與發布 Release**

此 Prompt 只在維護者已人工審查並明確授權發布時使用。

你已獲得明確授權，發布 TradeGuard v0.1.0 Connected Release。

開始前再次確認：

\- Prompt 15 結論為 GO。  
\- Prompt 16 結論為 READY\_TO\_TAG。  
\- 目前 Git SHA 與 RELEASE\_MANIFEST.json 完全一致。  
\- Worktree clean。  
\- 所有 CI 通過。  
\- Evidence bundle verification 通過。  
\- 沒有秘密。  
\- 沒有 live、withdrawal 或 transfer capability。  
\- 沒有未處理 Critical 或 High security issue。

請完成：

1\. 建立 annotated tag：

v0.1.0

2\. Tag message 必須包含：  
   \- Connected Release  
   \- target Git SHA  
   \- supported environments  
   \- no live trading  
   \- evidence index checksum  
   \- release manifest checksum

3\. Push tag 前再次顯示：  
   \- exact tag command  
   \- target remote  
   \- target SHA

4\. 只有在本次授權明確包含 push 時才 push。

5\. 建立 GitHub Release：  
   \- 使用已審查 release notes  
   \- 附加 release artifacts  
   \- 附加 checksums  
   \- 附加 SBOM  
   \- 附加 RELEASE\_MANIFEST.json  
   \- 附加 evidence index 或 evidence archive

6\. 發布後驗證：  
   \- tag points to expected SHA  
   \- release assets checksums  
   \- installation from release artifact  
   \- container startup  
   \- health endpoints  
   \- dashboard  
   \- offline sample workflow

7\. 不要在發布後自動啟用任何 connected credential 或長時間執行工作。

8\. 建立：  
   docs/release/v0.1.0-post-release-verification.md

9\. 最終輸出：

Published version  
Tag  
Git SHA  
Release assets  
Checksums  
Post-release verification  
Known limitations  
Rollback command  
Security contact  
Final status: RELEASED / RELEASE\_FAILED

若任一發布後驗證失敗：  
\- 標記 RELEASE\_FAILED。  
\- 不得隱藏失敗。  
\- 提供撤回 release、標記 deprecated 或建立修正版的建議。

---

# **Connected Release 必要證據清單**

`v0.1.0` 至少應保存以下證據：

artifacts/evidence/v0.1.0/  
├── index.json  
├── README.md  
├── build/  
│   ├── build-metadata.json  
│   ├── package-checksums.txt  
│   └── container-digest.txt  
├── tests/  
│   ├── unit.xml  
│   ├── property.xml  
│   ├── integration.xml  
│   ├── contract.xml  
│   ├── replay.xml  
│   ├── e2e.xml  
│   └── coverage.xml  
├── data/  
│   ├── equity-dataset-manifest.json  
│   ├── crypto-dataset-manifest.json  
│   ├── equity-quality-report.json  
│   └── crypto-quality-report.json  
├── backtests/  
│   ├── equity-run-manifest.json  
│   ├── crypto-run-manifest.json  
│   ├── equity-result-checksum.txt  
│   └── crypto-result-checksum.txt  
├── validation/  
│   ├── equity-validation-report.json  
│   ├── crypto-validation-report.json  
│   ├── walk-forward-report.json  
│   └── robustness-report.json  
├── risk/  
│   ├── equity-risk-report.json  
│   ├── crypto-risk-report.json  
│   └── stress-scenarios.json  
├── adapters/  
│   ├── equity-capabilities.json  
│   ├── crypto-capabilities.json  
│   ├── external-non-live-capabilities.json  
│   ├── offline-contract-results.json  
│   └── connected-smoke-results.json  
├── api/  
│   ├── openapi.json  
│   └── contract-test-results.json  
├── dashboard/  
│   ├── e2e-results.json  
│   └── screenshots/  
├── security/  
│   ├── secret-scan.json  
│   ├── dependency-scan.json  
│   ├── container-scan.json  
│   ├── workflow-permissions.json  
│   └── threat-model-checklist.json  
├── reproducibility/  
│   ├── environment-a.json  
│   ├── environment-b.json  
│   ├── comparison.json  
│   └── clean-clone-result.json  
├── sbom/  
│   ├── sbom.json  
│   └── sbom-checksum.txt  
└── release/  
    ├── RELEASE\_MANIFEST.json  
    ├── CHANGELOG.md  
    ├── release-notes.md  
    └── rollback.md

---

# **不可 Waive 的 Release Gates**

以下 gate 任一失敗，都不得發布 Connected Release：

1. Repository 含真實 secret。  
2. 存在 live、withdrawal 或 transfer 路徑。  
3. 一般 CI 需要正式或高權限 credential。  
4. 核心財務帳本守恆測試失敗。  
5. Deterministic replay 失敗。  
6. Run manifest 不完整。  
7. Dataset checksum 無法驗證。  
8. Data-quality FAIL 資料被用於正式證據。  
9. Look-ahead 或 point-in-time 檢查失敗。  
10. Out-of-sample 資料曾被用於調參。  
11. Risk engine 可被策略繞過。  
12. UNKNOWN 外部訂單狀態會自動重送風險。  
13. Reconciliation mismatch 被標示為正常。  
14. Secret redaction 測試失敗。  
15. Evidence tampering 無法被偵測。  
16. Fresh-clone build 失敗。  
17. 兩個乾淨環境無法重現核心離線結果。  
18. OpenAPI contract 與實作不一致。  
19. Critical 或 High security issue 未解決。  
20. connected smoke test 被捏造、未執行卻標示 PASS。

---

# **建議執行順序**

Prompt 0  
  ↓  
Prompt 1  
  ↓  
Prompt 2  
  ↓  
Prompt 3  
  ↓  
Prompt 4 ─┐  
          ├─→ Prompt 6  
Prompt 5 ─┘  
  ↓  
Prompt 7  
  ↓  
Prompt 8  
  ↓  
Prompt 9  
  ↓  
Prompt 10  
  ↓  
Prompt 11  
  ↓  
Prompt 12  
  ↓  
Prompt 13  
  ↓  
Prompt 14  
  ↓  
Prompt 15  
  ↓  
人工 GO／NO-GO 審查  
  ↓  
Prompt 16  
  ↓  
人工發布授權  
  ↓  
Prompt 17

Prompt 4 與 Prompt 5 可以在不同 branch 或 worktree 平行開發，但必須在 Prompt 6 之前完成介面整合與 contract review。

---

# **每一階段的人類審查點**

至少應在以下階段進行人工審查：

1. **Prompt 0 後**  
   * 決定資料供應商。  
   * 決定 paper／sandbox／read-only adapter。  
   * 決定授權。  
   * 確認 Connected Release 範圍。  
2. **Prompt 3 後**  
   * 審查 canonical schema。  
   * 審查 point-in-time 規則。  
   * 審查資料授權。  
3. **Prompt 6 後**  
   * 審查帳本。  
   * 審查成交模型。  
   * 審查 look-ahead 防護。  
4. **Prompt 9 後**  
   * 審查風險限制。  
   * 審查壓力情境。  
   * 確認策略無法繞過風控。  
5. **Prompt 11 後**  
   * 檢查外部 adapter 權限。  
   * 確認沒有正式交易 endpoint。  
   * 確認憑證為最小權限。  
6. **Prompt 14 後**  
   * Security review。  
   * Threat-model review。  
   * Supply-chain review。  
7. **Prompt 15 後**  
   * GO／NO-GO。  
   * 驗證 connected 證據。  
   * 驗證 reproducibility。  
8. **Prompt 16 後**  
   * 確認 tag SHA。  
   * 確認 release assets。  
   * 明確授權發布。

