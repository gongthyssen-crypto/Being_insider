import { useEffect, useMemo, useState } from "react";

const API_ROOT = "/api";

async function readJson(path, options) {
  const response = await fetch(`${API_ROOT}${path}`, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function formatRuntimeMode(mode) {
  if (!mode) {
    return "等待连接";
  }
  if (mode.startsWith("deepseek-official:")) {
    return `DeepSeek 官方模型 · ${mode.replace("deepseek-official:", "")}`;
  }
  if (mode.includes("local-fallback") || mode.includes("local-adjudicator")) {
    return "历史推演模式";
  }
  return mode;
}

function formatScenarioIndex(index) {
  return String(index + 1).padStart(2, "0");
}

function formatTimestamp(value) {
  if (!value) {
    return "待命";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "待命";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

export default function App() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState(null);
  const [scenarioSeed, setScenarioSeed] = useState(null);
  const [sessionSnapshot, setSessionSnapshot] = useState(null);
  const [history, setHistory] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [draftAction, setDraftAction] = useState("");
  const [selectedOptionId, setSelectedOptionId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function bootstrap() {
      try {
        const [scenarioData, healthData] = await Promise.all([
          readJson("/scenarios"),
          readJson("/health"),
        ]);
        setScenarios(scenarioData);
        setHealth(healthData);
        if (scenarioData.length > 0) {
          await openScenario(scenarioData[0].id, scenarioData);
        }
      } catch (err) {
        setError("后端未启动，或依赖尚未安装。");
      } finally {
        setLoading(false);
      }
    }

    bootstrap();
  }, []);

  async function openScenario(scenarioId, source = scenarios) {
    setScenarioLoading(true);
    setError("");
    setSelectedScenarioId(scenarioId);
    setDraftAction("");
    setSelectedOptionId(null);
    setHistory([]);

    try {
      const [seed, snapshot] = await Promise.all([
        readJson(`/scenarios/${scenarioId}`),
        readJson("/sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario_id: scenarioId }),
        }),
      ]);
      setScenarioSeed(seed);
      setSessionSnapshot(snapshot);
    } catch (err) {
      setError("章节初始化失败。");
      const fallbackSelected =
        source.find((item) => item.id === scenarioId) ??
        scenarios.find((item) => item.id === scenarioId) ??
        null;
      if (!fallbackSelected) {
        setSelectedScenarioId(null);
      }
    } finally {
      setScenarioLoading(false);
    }
  }

  function applyOpeningOption(option) {
    setSelectedOptionId(option.id);
    setDraftAction(option.brief);
    setError("");
  }

  async function submitTurn() {
    if (!sessionSnapshot?.session?.session_id) {
      setError("当前会话尚未建立。");
      return;
    }

    const actionText = draftAction.trim();
    if (!actionText) {
      setError("先写下这一回合的决策。");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const result = await readJson(
        `/sessions/${sessionSnapshot.session.session_id}/turns`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action_text: actionText,
            source_option_id: selectedOptionId,
          }),
        },
      );

      setSessionSnapshot((previous) => ({
        ...previous,
        session: result.session,
        latest_narration: result.ending ?? result.turn.ai_narration,
        next_prompt_hint: result.next_prompt_hint,
        runtime_mode: result.runtime_mode,
      }));
      setHistory((previous) => [...previous, result.turn]);
      setDraftAction("");
      setSelectedOptionId(null);
    } catch (err) {
      setError("推演提交失败。");
    } finally {
      setSubmitting(false);
    }
  }

  const selectedScenario = useMemo(
    () => scenarios.find((item) => item.id === selectedScenarioId) ?? null,
    [scenarios, selectedScenarioId],
  );

  const sessionEnded = sessionSnapshot?.session?.status === "ended";
  const latestTurn = history.at(-1) ?? null;
  const previousTurns = history.slice(0, -1).reverse();
  const pageSummary = useMemo(() => {
    if (!scenarioSeed) {
      return "在关键的岔路口，做出你的抉择，改写历史的走向。";
    }
    return scenarioSeed.summary;
  }, [scenarioSeed]);

  return (
    <div className="app-shell">
      <div className="paper-grain" />

      <header className="topband">
        <div className="brand-block">
          <div className="brand-mark">
            <p className="eyebrow">AI 中国古代历史情景推演系统</p>
            <div className="brand-title-row">
              <h1>历史岔路</h1>
              <span className="seal-badge">推演</span>
            </div>
          </div>
          <p className="brand-summary">{pageSummary}</p>
        </div>

        <div className="status-card">
          <div className="status-row">
            <span className="status-label">后端状态</span>
            <span className="status-value status-online">
              <i className="status-dot" />
              {health?.status === "ok" ? "运行中" : "离线"}
            </span>
          </div>
          <div className="status-row">
            <span className="status-label">服务配置</span>
            <span className="status-value">API 服务 + 模型服务 + 数据层</span>
          </div>
          <div className="status-row">
            <span className="status-label">端口信息</span>
            <span className="status-value">API 18421 · WEB 18422</span>
          </div>
          <div className="status-row">
            <span className="status-label">模型模式</span>
            <span className="status-value">{formatRuntimeMode(health?.model_mode)}</span>
          </div>
        </div>
      </header>

      <div className="workspace">
        <aside className="scenario-rail">
          <div className="rail-title">
            <span className="panel-kicker">章节导航</span>
            <h2>章节选择</h2>
          </div>

          <div className="scenario-list">
            {scenarios.map((item, index) => (
              <button
                key={item.id}
                className={`scenario-tab ${
                  selectedScenarioId === item.id ? "active" : ""
                }`}
                onClick={() => openScenario(item.id)}
                disabled={scenarioLoading || submitting}
                type="button"
              >
                <span className="scenario-index">{formatScenarioIndex(index)}</span>
                <div className="scenario-copy">
                  <strong>{item.title}</strong>
                  <span>{item.era}</span>
                  <em>{item.summary}</em>
                </div>
              </button>
            ))}
          </div>

          <div className="rail-footer">
            <p className="rail-note">当前版本以既有历史情景推演为主，保留全部原始信息结构。</p>
            <p className="rail-version">版本：v1.0.0</p>
          </div>
        </aside>

        <main className="story-stage">
          {loading || scenarioLoading ? (
            <section className="scene-panel empty-panel">正在载入章节与会话...</section>
          ) : error ? (
            <section className="scene-panel error">{error}</section>
          ) : scenarioSeed && sessionSnapshot ? (
            <>
              <section className="hero-panel">
                <div className="panel-head">
                  <span className="panel-kicker">当前推演</span>
                  <span className="session-pill">
                    {sessionEnded
                      ? "阶段结尾"
                      : `第 ${sessionSnapshot.session.turn_index} 回合`}
                  </span>
                </div>

                <div className="hero-title-row">
                  <h2>{scenarioSeed.title}</h2>
                  <span className="hero-era">{scenarioSeed.era}</span>
                </div>

                <p className="hero-role">你的角色：{scenarioSeed.player_role}</p>
                <p className="hero-narration">{sessionSnapshot.latest_narration}</p>
              </section>

              <section className="insight-section">
                <article className="info-card">
                  <div className="info-head">
                    <span className="info-icon">壹</span>
                    <h3>开局局势</h3>
                  </div>
                  <p>{scenarioSeed.opening_situation}</p>
                </article>

                <article className="info-card">
                  <div className="info-head">
                    <span className="info-icon">贰</span>
                    <h3>历史锚点</h3>
                  </div>
                  <p>{scenarioSeed.historical_anchor}</p>
                </article>

                <article className="info-card">
                  <div className="info-head">
                    <span className="info-icon">叁</span>
                    <h3>主目标</h3>
                  </div>
                  <p>{scenarioSeed.primary_goal}</p>
                </article>

                <article className="info-card warning-card">
                  <div className="info-head">
                    <span className="info-icon">肆</span>
                    <h3>失败风险</h3>
                  </div>
                  <p>{scenarioSeed.failure_risk}</p>
                </article>
              </section>

              <section className="summary-panel">
                <div className="panel-head">
                  <span className="panel-kicker">当前局势摘要</span>
                  <span className="session-meta">
                    会话 {sessionSnapshot.session.session_id.slice(0, 8)}
                  </span>
                </div>

                <div className="summary-grid">
                  <div className="summary-item">
                    <h3>时间阶段</h3>
                    <p>{sessionSnapshot.session.world_summary.time_label}</p>
                  </div>
                  <div className="summary-item">
                    <h3>当前位置</h3>
                    <p>{sessionSnapshot.session.world_summary.location}</p>
                  </div>
                  <div className="summary-item">
                    <h3>最新变化</h3>
                    <p>{sessionSnapshot.session.world_summary.recent_shift}</p>
                  </div>
                  <div className="summary-item">
                    <h3>当前引擎</h3>
                    <p>{formatRuntimeMode(sessionSnapshot.runtime_mode)}</p>
                  </div>
                  <div className="summary-item summary-wide">
                    <h3>主要压力</h3>
                    <ul className="pressure-list">
                      {sessionSnapshot.session.world_summary.pressure_points.map(
                        (item) => (
                          <li key={item}>{item}</li>
                        ),
                      )}
                    </ul>
                  </div>
                  <div className="summary-item summary-wide">
                    <h3>局势综述</h3>
                    <p>{sessionSnapshot.session.world_summary.situation}</p>
                  </div>
                </div>
              </section>

              <section className="action-panel">
                <div className="panel-head">
                  <span className="panel-kicker">你的行动</span>
                  <span className="action-hint">{sessionSnapshot.next_prompt_hint}</span>
                </div>

                <div className="action-layout">
                  <div className="action-options">
                    <div className="subsection-head">
                      <h3>参考起手选项</h3>
                      <p>{scenarioSeed.opening_prompt_hint}</p>
                    </div>

                    <div className="opening-option-list">
                      {scenarioSeed.initial_options.map((option) => (
                        <button
                          key={option.id}
                          className={`opening-option ${
                            selectedOptionId === option.id ? "active" : ""
                          }`}
                          onClick={() => applyOpeningOption(option)}
                          disabled={submitting || sessionEnded}
                          type="button"
                        >
                          <strong>{option.label}</strong>
                          <span>{option.brief}</span>
                          <em>{option.strategic_hint}</em>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="draft-panel">
                    <div className="subsection-head">
                      <h3>你的决策</h3>
                      <p>{selectedOptionId ? `已绑定参考起手：${selectedOptionId}` : "可直接输入自由行动"}</p>
                    </div>

                    <label className="draft-label" htmlFor="action-input">
                      本回合决策
                    </label>
                    <textarea
                      id="action-input"
                      className="action-textarea"
                      value={draftAction}
                      onChange={(event) => setDraftAction(event.target.value)}
                      disabled={submitting || sessionEnded}
                      placeholder="请写入你的决策，例如：我决定先稳住粮道，整顿军纪，同时联络周边势力争取缓冲时间。"
                      rows={7}
                    />

                    <div className="action-toolbar">
                      <span className="hint-chip">
                        {sessionEnded ? "本局已进入阶段性结尾" : "你可以自由发挥，也可以参考左侧起手"}
                      </span>
                      <div className="action-buttons">
                        <button
                          className="ghost-button"
                          onClick={() => {
                            setDraftAction("");
                            setSelectedOptionId(null);
                          }}
                          disabled={submitting || sessionEnded}
                          type="button"
                        >
                          清空决策
                        </button>
                        <button
                          className="primary-button"
                          onClick={submitTurn}
                          disabled={submitting || sessionEnded}
                          type="button"
                        >
                          {submitting ? "推演中..." : "提交决策"}
                        </button>
                      </div>
                    </div>

                    {sessionEnded ? (
                      <button
                        className="restart-button"
                        onClick={() => openScenario(selectedScenarioId)}
                        type="button"
                      >
                        重新开始本章
                      </button>
                    ) : null}
                  </div>
                </div>
              </section>

              <section className="result-panel">
                <div className="panel-head result-head">
                  <div>
                    <span className="panel-kicker">最新推演结果</span>
                    <h2>本轮战报总览</h2>
                  </div>
                  <span className="result-time">
                    推演时间：{formatTimestamp(latestTurn?.timestamp)}
                  </span>
                </div>

                {latestTurn ? (
                  <article className="latest-turn">
                    <div className="latest-turn-index">
                      <span>第</span>
                      <strong>{String(latestTurn.turn_index).padStart(2, "0")}</strong>
                      <span>回合</span>
                    </div>

                    <div className="latest-turn-content">
                      <div className="latest-grid">
                        <div className="latest-cell">
                          <h3>回合编号</h3>
                          <p>第 {latestTurn.turn_index} 回合</p>
                        </div>
                        <div className="latest-cell">
                          <h3>玩家决策</h3>
                          <p>{latestTurn.player_action}</p>
                        </div>
                        <div className="latest-cell">
                          <h3>系统裁定模式</h3>
                          <p>{formatRuntimeMode(latestTurn.resolution_mode)}</p>
                        </div>
                        <div className="latest-cell">
                          <h3>结果摘要</h3>
                          <p>{latestTurn.outcome_summary}</p>
                        </div>
                        <div className="latest-cell latest-wide">
                          <h3>世界变化</h3>
                          <p>{latestTurn.world_update}</p>
                        </div>
                        <div className="latest-cell latest-wide accent-cell">
                          <h3>推演结果</h3>
                          <p>{latestTurn.ai_narration}</p>
                        </div>
                      </div>
                    </div>
                  </article>
                ) : (
                  <div className="latest-turn empty-latest">
                    <div className="latest-turn-index">
                      <span>待</span>
                      <strong>00</strong>
                      <span>回合</span>
                    </div>
                    <div className="latest-turn-content">
                      <div className="latest-grid">
                        <div className="latest-cell latest-wide accent-cell">
                          <h3>推演结果</h3>
                          <p>当前还没有提交任何回合。完成上方决策后，最新推演结果会在此处以高亮战报形式展示。</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </section>

              <section className="history-panel">
                <div className="panel-head">
                  <span className="panel-kicker">历史回合记录</span>
                  <span className="session-meta">
                    {history.length === 0 ? "尚无历史回合" : `累计 ${history.length} 条记录`}
                  </span>
                </div>

                <div className="timeline-list">
                  {history.length === 0 ? (
                    <div className="timeline-item empty">
                      当前还没有提交任何回合。
                    </div>
                  ) : (
                    <>
                      {previousTurns.map((entry) => (
                        <div className="timeline-item" key={entry.turn_index}>
                          <span>{String(entry.turn_index).padStart(2, "0")}</span>
                          <strong>{entry.player_action}</strong>
                          <small className="timeline-mode">
                            {formatRuntimeMode(entry.resolution_mode)}
                          </small>
                          <p>{entry.outcome_summary}</p>
                          <em>{entry.world_update}</em>
                        </div>
                      ))}
                      {latestTurn ? (
                        <div className="timeline-item latest">
                          <span>{String(latestTurn.turn_index).padStart(2, "0")}</span>
                          <strong>{latestTurn.player_action}</strong>
                          <small className="timeline-mode">
                            {formatRuntimeMode(latestTurn.resolution_mode)}
                          </small>
                          <p>{latestTurn.outcome_summary}</p>
                          <em>{latestTurn.world_update}</em>
                        </div>
                      ) : null}
                    </>
                  )}
                </div>
              </section>
            </>
          ) : (
            <section className="scene-panel empty-panel">
              {selectedScenario ? "未能初始化章节。" : "暂无可用章节。"}
            </section>
          )}
        </main>
      </div>
    </div>
  );
}
