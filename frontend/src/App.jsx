import { useEffect, useMemo, useState } from "react";

const API_ROOT = "/api";

const SCENARIO_DECOR = {
  yuan_shikai_korea: {
    crest: "袁",
    label: "清末外交",
    description: "朝鲜宫廷、宗主体系与日本试探交错的前线局势",
    tone: "yuan",
  },
  zhang_juzheng_reform: {
    crest: "张",
    label: "明廷改革",
    description: "紫禁城秩序深处，改革与权力节奏相互牵动",
    tone: "zhang",
  },
  li_quan_red_turban: {
    crest: "李",
    label: "乱世扩张",
    description: "山东与淮海之间，流民、粮道与军势同时翻涌",
    tone: "li",
  },
};

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

function getScenarioDecor(scenarioId) {
  return (
    SCENARIO_DECOR[scenarioId] ?? {
      crest: "史",
      label: "历史剧本",
      description: "围绕关键节点展开的历史推演。",
      tone: "default",
    }
  );
}

export default function App() {
  const [page, setPage] = useState("home");
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
      setPage("detail");
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

  function backToHome() {
    setPage("home");
    setError("");
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

  const currentDecor = getScenarioDecor(selectedScenarioId);
  const sessionEnded = sessionSnapshot?.session?.status === "ended";
  const latestTurn = history.at(-1) ?? null;
  const previousTurns = history.slice(0, -1).reverse();

  return (
    <div className={`app-shell ${page === "home" ? "shell-home" : "shell-detail"}`}>
      <div className="paper-grain" />

      {page === "home" ? (
        <>
          <header className="home-hero">
            <div className="home-status">
              <span className="home-status-item">
                <i className="status-dot" />
                后端{health?.status === "ok" ? "已连接" : "离线"}
              </span>
              <span className="home-status-divider" />
              <span className="home-status-item">
                模型模式：{formatRuntimeMode(health?.model_mode)}
              </span>
            </div>

            <p className="eyebrow">AI 中国古代历史情景推演系统</p>
            <h1 className="home-title">历史岔路</h1>
            <p className="home-tagline">选择你的时代，改写一段历史</p>
            <p className="home-summary">
              在关键的历史节点，你将扮演特定的角色，面对复杂的局势与抉择。每一次选择，
              都可能改变历史的走向。
            </p>
          </header>

          {error ? <section className="home-message error">{error}</section> : null}

          <main className="home-main">
            <section className="home-card-grid">
              {loading
                ? Array.from({ length: 3 }).map((_, index) => (
                    <article className="scenario-home-card skeleton-card" key={index}>
                      <div className="scenario-home-art" />
                      <div className="scenario-home-copy">
                        <div className="skeleton-line skeleton-line--lg" />
                        <div className="skeleton-line" />
                        <div className="skeleton-line" />
                      </div>
                    </article>
                  ))
                : scenarios.map((item) => {
                    const decor = getScenarioDecor(item.id);
                    const isBusy = scenarioLoading && selectedScenarioId === item.id;
                    return (
                      <article
                        key={item.id}
                        className={`scenario-home-card tone-${decor.tone}`}
                      >
                        <div className="scenario-home-art">
                          <span className="scenario-home-seal">{decor.crest}</span>
                        </div>

                        <div className="scenario-home-copy">
                          <span className="scenario-home-label">{decor.label}</span>
                          <h2>{item.title}</h2>
                          <p className="scenario-home-era">时代：{item.era}</p>
                          <p className="scenario-home-summary">{item.summary}</p>
                          <p className="scenario-home-note">{decor.description}</p>

                          <button
                            className="primary-button home-enter-button"
                            onClick={() => openScenario(item.id)}
                            disabled={scenarioLoading}
                            type="button"
                          >
                            {isBusy ? "载入推演..." : "进入推演"}
                          </button>
                        </div>
                      </article>
                    );
                  })}
            </section>

            <footer className="home-footer">
              <span>选择一个历史剧本，进入你的时代，书写属于你的历史。</span>
              <span>历史岔路 v1.0.0</span>
            </footer>
          </main>
        </>
      ) : (
        <>
          <header className="detail-topbar">
            <button className="back-button" onClick={backToHome} type="button">
              返回剧本选择
            </button>

            <div className="detail-status">
              <span className="detail-status-item">
                <i className="status-dot" />
                后端{health?.status === "ok" ? "已连接" : "离线"}
              </span>
              <span className="detail-status-item">
                模型模式：{formatRuntimeMode(health?.model_mode)}
              </span>
            </div>
          </header>

          <main className="detail-main">
            {scenarioLoading ? (
              <section className="scene-panel empty-panel">正在为你开启新的历史剧本...</section>
            ) : error ? (
              <section className="scene-panel error">{error}</section>
            ) : scenarioSeed && sessionSnapshot ? (
              <>
                <section className={`detail-hero tone-${currentDecor.tone}`}>
                  <div className="detail-hero-copy">
                    <p className="eyebrow">当前剧本</p>
                    <div className="detail-hero-title-row">
                      <h2>{scenarioSeed.title}</h2>
                      <span className="hero-era">{scenarioSeed.era}</span>
                    </div>
                    <p className="detail-hero-role">你的角色：{scenarioSeed.player_role}</p>
                    <p className="detail-hero-summary">{scenarioSeed.summary}</p>
                    <p className="hero-narration">{sessionSnapshot.latest_narration}</p>
                  </div>

                  <div className="detail-hero-side">
                    <div className="detail-hero-badge">{currentDecor.crest}</div>
                    <p>{currentDecor.description}</p>
                    <span className="session-pill">
                      {sessionEnded
                        ? "阶段结尾"
                        : `第 ${sessionSnapshot.session.turn_index} 回合`}
                    </span>
                  </div>
                </section>

                <section className="detail-info-grid">
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
                        <p>
                          {selectedOptionId
                            ? `已绑定参考起手：${selectedOptionId}`
                            : "可直接输入自由行动"}
                        </p>
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
                          {sessionEnded
                            ? "本局已进入阶段性结尾"
                            : "你可以自由发挥，也可以参考左侧起手"}
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
                            <p>
                              当前还没有提交任何回合。完成上方决策后，最新推演结果会在此处以高亮战报形式展示。
                            </p>
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
                        <div className="timeline-item latest">
                          <span>{String(latestTurn.turn_index).padStart(2, "0")}</span>
                          <strong>{latestTurn.player_action}</strong>
                          <small className="timeline-mode">
                            {formatRuntimeMode(latestTurn.resolution_mode)}
                          </small>
                          <p>{latestTurn.outcome_summary}</p>
                          <em>{latestTurn.world_update}</em>
                        </div>
                      </>
                    )}
                  </div>
                </section>
              </>
            ) : (
              <section className="scene-panel empty-panel">
                {selectedScenario ? "未能初始化剧本。" : "请先从首页选择一个剧本。"}
              </section>
            )}
          </main>
        </>
      )}
    </div>
  );
}
