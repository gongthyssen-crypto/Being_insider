import { useEffect, useMemo, useState } from "react";

const API_ROOT = "/api";
const DEFAULT_RUNTIME_SETTINGS = {
  deepseek_max_tokens: 4096,
  deepseek_thinking_enabled: true,
  turn_knowledge_max_matches: 4,
  turn_knowledge_max_excerpt_chars: 720,
};

const SCENARIO_DECOR = {
  yuan_shikai_korea: {
    crest: "袁",
    label: "清末外交",
    description: "朝鲜宫廷、宗主体系与日本试探交错的前线局势",
    tone: "yuan",
    cover: "/images/yuan-bg.png",
    portrait: "/images/yuan-portrait.png",
    coverPosition: "center 62%",
    portraitPosition: "center top",
    guide: {
      roleBrief:
        "你不是单纯驻外使臣，而是清廷在朝鲜的前线执行者。你手里的牌包括宗主名义、宫廷影响力、驻军威慑与对局势节奏的操盘能力，但每张牌都不能打得过头。",
      situationBriefs: [
        "朝鲜宫廷亲清、亲日与本地派系互相掣肘，任何一方失衡都可能引发连锁反应。",
        "日本正在通过外交、贸易与军事试探不断加码，表面交涉背后是实质渗透。",
        "清廷希望维持影响力，却又不愿轻易全面摊牌，这让你的操作空间始终带着上限。",
      ],
      keyFigures: [
        "朝鲜王室：需要清廷支撑，但对外部控制也保持警惕。",
        "亲日派：希望借改革与外援改写朝局，是最活跃的突破口。",
        "日本公使与军方：持续试探你的底线，一旦误判就可能迅速升级。",
        "清廷中枢：给你合法性，却未必给你足够资源与明确边界。",
      ],
      playerFocus: [
        "短期先稳住宫廷秩序，避免朝鲜内部先乱。",
        "中期压住日本扩张节奏，但不要过早把局势推到公开摊牌。",
        "始终留意清廷的授权边界，别让自己陷入前线背锅位置。",
      ],
      starterConcepts: [
        "先稳宫廷，再压外部试探。",
        "先争授权，再决定出手强度。",
        "先立威，但别把退路全部封死。",
      ],
    },
  },
  zhang_juzheng_reform: {
    crest: "张",
    label: "明廷改革",
    description: "紫禁城秩序深处，改革与权力节奏相互牵动",
    tone: "zhang",
    cover: "/images/zhang-bg.png",
    portrait: "/images/zhang-portrait.png",
    coverPosition: "center 74%",
    portraitPosition: "center top",
    guide: {
      roleBrief:
        "你站在张居正一侧，但真正面对的是一个幼主初立、内廷外朝互相试探的复杂结构。你要做的不是喊口号，而是替改革争出第一口能落地的气。",
      situationBriefs: [
        "国库吃紧、行政拖沓、积弊已久，改革势在必行，但谁都不愿先承担成本。",
        "幼主新立意味着权威尚未坐稳，任何过猛动作都可能被解释成权臣专断。",
        "内阁、司礼监、言官与地方官场之间彼此防范，改革必须先处理节奏问题。",
      ],
      keyFigures: [
        "张居正：真正的主心骨，但也最容易成为众矢之的。",
        "万历皇帝与宫廷：是改革合法性的来源，也是不稳定因素。",
        "言官群体：能替改革造势，也能迅速把它定义成权力工程。",
        "地方官僚系统：真正执行政策的人，但往往也是最先消解政策的人。",
      ],
      playerFocus: [
        "先判断是稳权力结构，还是先推可见的制度抓手。",
        "让第一步看起来像治事，而不是单纯扩权。",
        "给后续改革留下连续性，别把所有反弹集中到第一回合。",
      ],
      starterConcepts: [
        "先抓执行，再推深水改革。",
        "先稳朝局，再动钱粮命脉。",
        "先树秩序，再谈全面翻新。",
      ],
    },
  },
  li_quan_red_turban: {
    crest: "李",
    label: "乱世扩张",
    description: "山东与淮海之间，流民、粮道与军势同时翻涌",
    tone: "li",
    cover: "/images/li-bg.png",
    portrait: "/images/li-portrait.png",
    coverPosition: "center 68%",
    portraitPosition: "center top",
    guide: {
      roleBrief:
        "你扮演的李全不是简单的草莽首领，而是夹在金、宋、蒙古与地方豪强之间求活路的乱世军事创业者。能不能活下来，往往比能不能打赢更重要。",
      situationBriefs: [
        "山东与淮海之间的流民、溃兵与地方武装不断汇聚，机会和失控同时增长。",
        "金廷衰弱但仍有围剿能力，南宋能提供名分却未必真心托底，蒙古则是更大的变量。",
        "队伍越做越大，就越难只靠义气维系，粮秣、归属与内部控制会迅速浮上台面。",
      ],
      keyFigures: [
        "李全部众：能打，但也最容易因分赃、归附和路线问题离心。",
        "南宋方面：可能给你合法性和补给，也可能把你当消耗品。",
        "金廷与地方官军：短期敌人，长期也可能成为你谈判的对象。",
        "地方豪强与寨主：是扩张的资源池，也是内部失控的来源。",
      ],
      playerFocus: [
        "先解决粮道、补给和人心，不要只顾着扩兵。",
        "想清楚你是要独立做大，还是借更大政权的势先活下来。",
        "每次吞并和结盟都要考虑后续忠诚与反噬问题。",
      ],
      starterConcepts: [
        "先抓粮道，再谈扩张。",
        "先借名分，再争主动。",
        "先整内部，再吞并周边。",
      ],
    },
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
      cover: "",
      portrait: "",
      coverPosition: "center center",
      portraitPosition: "center top",
    }
  );
}

function compactIntro(text, limit = 78) {
  if (!text) {
    return "";
  }

  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= limit) {
    return normalized;
  }

  return `${normalized.slice(0, limit).replace(/[，、；,; ]+$/u, "")}...`;
}

export default function App() {
  const [page, setPage] = useState("home");
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState(null);
  const [scenarioSeed, setScenarioSeed] = useState(null);
  const [sessionSnapshot, setSessionSnapshot] = useState(null);
  const [history, setHistory] = useState([]);
  const [health, setHealth] = useState(null);
  const [runtimeSettings, setRuntimeSettings] = useState(DEFAULT_RUNTIME_SETTINGS);
  const [settingsDraft, setSettingsDraft] = useState(DEFAULT_RUNTIME_SETTINGS);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [draftAction, setDraftAction] = useState("");
  const [selectedOptionId, setSelectedOptionId] = useState(null);
  const [selectedTurnIndex, setSelectedTurnIndex] = useState(null);
  const [actionGuideTab, setActionGuideTab] = useState("briefing");
  const [error, setError] = useState("");

  useEffect(() => {
    async function bootstrap() {
      try {
        const [scenarioData, healthData, runtimeSettingsData] = await Promise.all([
          readJson("/scenarios"),
          readJson("/health"),
          readJson("/runtime-settings"),
        ]);
        setScenarios(scenarioData);
        setHealth(healthData);
        setRuntimeSettings(runtimeSettingsData);
        setSettingsDraft(runtimeSettingsData);
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
    setSelectedTurnIndex(null);
    setActionGuideTab("briefing");

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

  function updateSettingsField(field, value) {
    setSettingsDraft((previous) => ({
      ...previous,
      [field]: value,
    }));
  }

  async function saveRuntimeSettings() {
    setSettingsSaving(true);
    setError("");

    try {
      const payload = {
        deepseek_max_tokens: Number(settingsDraft.deepseek_max_tokens),
        deepseek_thinking_enabled: Boolean(settingsDraft.deepseek_thinking_enabled),
        turn_knowledge_max_matches: Number(settingsDraft.turn_knowledge_max_matches),
        turn_knowledge_max_excerpt_chars: Number(settingsDraft.turn_knowledge_max_excerpt_chars),
      };
      const saved = await readJson("/runtime-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setRuntimeSettings(saved);
      setSettingsDraft(saved);
    } catch (err) {
      setError("Runtime settings save failed.");
    } finally {
      setSettingsSaving(false);
    }
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
        latest_narration: result.turn.ai_narration,
        next_prompt_hint: result.next_prompt_hint,
        suggested_options: result.suggested_options,
        runtime_mode: result.runtime_mode,
        ending: result.ending ?? null,
        ending_summary: result.ending_summary ?? null,
      }));
      setHistory((previous) => [...previous, result.turn]);
      setSelectedTurnIndex(result.turn.turn_index);
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
  const currentGuide = currentDecor.guide ?? null;
  const sessionEnded = sessionSnapshot?.session?.status === "ended";
  const currentEnding = sessionSnapshot?.ending ?? null;
  const currentEndingSummary = sessionSnapshot?.ending_summary ?? null;
  const latestTurn = history.at(-1) ?? null;
  const activeTurn =
    history.find((entry) => entry.turn_index === selectedTurnIndex) ?? latestTurn ?? null;
  const isViewingLatest = activeTurn?.turn_index === latestTurn?.turn_index;

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
            <h1 className="home-title">身在局中</h1>
            <p className="home-tagline">置身时代局势之中，做出你的抉择</p>
            <p className="home-summary">
              在关键的历史节点，你将扮演特定的角色，面对复杂的局势与抉择。每一次选择，
              都可能改变历史的走向。
            </p>
          </header>

          {error ? <section className="home-message error">{error}</section> : null}

          <main className="home-main">
            <section className="runtime-settings-panel">
              <div className="panel-head">
                <span className="panel-kicker">Runtime Settings</span>
                <span className="session-meta">Applies on the next turn without restart</span>
              </div>

              <div className="runtime-settings-grid">
                <label className="runtime-field">
                  <span>DeepSeek max tokens</span>
                  <input
                    type="number"
                    min="512"
                    max="8192"
                    value={settingsDraft.deepseek_max_tokens}
                    onChange={(event) =>
                      updateSettingsField("deepseek_max_tokens", event.target.value)
                    }
                  />
                  <small>Suggested: 4096-8192. Higher means more cost and latency.</small>
                </label>

                <label className="runtime-field">
                  <span>RAG reference count</span>
                  <input
                    type="number"
                    min="1"
                    max="8"
                    value={settingsDraft.turn_knowledge_max_matches}
                    onChange={(event) =>
                      updateSettingsField("turn_knowledge_max_matches", event.target.value)
                    }
                  />
                  <small>More references improve coverage, but also lengthen the prompt.</small>
                </label>

                <label className="runtime-field">
                  <span>Excerpt chars per reference</span>
                  <input
                    type="number"
                    min="160"
                    max="2400"
                    value={settingsDraft.turn_knowledge_max_excerpt_chars}
                    onChange={(event) =>
                      updateSettingsField(
                        "turn_knowledge_max_excerpt_chars",
                        event.target.value,
                      )
                    }
                  />
                  <small>Suggested: 480-1200. Too high increases truncation risk.</small>
                </label>

                <label className="runtime-field runtime-toggle">
                  <span>Thinking mode</span>
                  <button
                    className={`toggle-button ${
                      settingsDraft.deepseek_thinking_enabled ? "active" : ""
                    }`}
                    onClick={() =>
                      updateSettingsField(
                        "deepseek_thinking_enabled",
                        !settingsDraft.deepseek_thinking_enabled,
                      )
                    }
                    type="button"
                  >
                    {settingsDraft.deepseek_thinking_enabled ? "Enabled" : "Disabled"}
                  </button>
                  <small>
                    Better reasoning quality, but it can consume output tokens and cause truncation.
                  </small>
                </label>
              </div>

              <div className="runtime-settings-actions">
                <span className="hint-chip">
                  {`Live: ${runtimeSettings.deepseek_max_tokens} tokens / RAG ${runtimeSettings.turn_knowledge_max_matches} / ${
                    runtimeSettings.deepseek_thinking_enabled ? "thinking on" : "thinking off"
                  }`}
                </span>
                <button
                  className="primary-button"
                  disabled={settingsSaving}
                  onClick={saveRuntimeSettings}
                  type="button"
                >
                  {settingsSaving ? "Saving..." : "Save Runtime Settings"}
                </button>
              </div>
            </section>

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
                        <div
                          className="scenario-home-art"
                          style={
                            decor.cover
                              ? {
                                  backgroundImage: `url(${decor.cover})`,
                                  backgroundPosition: decor.coverPosition,
                                }
                              : undefined
                          }
                        >
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
              <span>身在局中 v1.0.0</span>
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
                  {currentDecor.cover ? (
                    <div
                      className="detail-hero-backdrop"
                      style={{
                        backgroundImage: `url(${currentDecor.cover})`,
                        backgroundPosition: currentDecor.coverPosition,
                      }}
                    />
                  ) : null}

                  <div className="detail-hero-copy">
                    <div className="detail-hero-overline">
                      <p className="eyebrow">当前剧本</p>
                      <span className="detail-hero-label">{currentDecor.label}</span>
                    </div>
                    <div className="detail-hero-title-row">
                      <h2>{scenarioSeed.title}</h2>
                      <span className="hero-era">{scenarioSeed.era}</span>
                    </div>
                    <p className="detail-hero-role">
                      <span>你的角色</span>
                      <strong>{scenarioSeed.player_role}</strong>
                    </p>
                    <p className="detail-hero-summary">{scenarioSeed.summary}</p>

                    <div className="hero-facts">
                      <div className="hero-fact">
                        <span>核心任务</span>
                        <p>{scenarioSeed.primary_goal}</p>
                      </div>
                      <div className="hero-fact">
                        <span>当前阶段</span>
                        <p>{sessionSnapshot.session.world_summary.time_label}</p>
                      </div>
                      <div className="hero-fact">
                        <span>主要风险</span>
                        <p>{compactIntro(scenarioSeed.failure_risk, 48)}</p>
                      </div>
                    </div>

                    <article className="hero-editorial">
                      <div className="hero-editorial-head">
                        <span className="hero-editorial-kicker">当前叙事</span>
                        <span className="hero-editorial-meta">{currentDecor.label}</span>
                      </div>
                      <p className="hero-narration">{sessionSnapshot.latest_narration}</p>
                    </article>
                  </div>

                  <div className="detail-hero-side">
                    <div className="detail-hero-side-head">
                      <span className="panel-kicker">人物档案</span>
                      <span className="session-pill">
                        {sessionEnded
                          ? "阶段结尾"
                          : `第 ${sessionSnapshot.session.turn_index} 回合`}
                      </span>
                    </div>

                    {currentDecor.portrait ? (
                      <div className="detail-portrait-stage">
                        <img
                          className="detail-portrait-image"
                          src={currentDecor.portrait}
                          alt={`${scenarioSeed.player_role}立绘`}
                          style={{ objectPosition: currentDecor.portraitPosition }}
                        />
                      </div>
                    ) : (
                      <div className="detail-hero-badge">{currentDecor.crest}</div>
                    )}

                    <div className="detail-dossier">
                      <div className="detail-dossier-head">
                        <h3>{scenarioSeed.player_role}</h3>
                        <p className="detail-dossier-note">{currentDecor.description}</p>
                      </div>

                      <div className="detail-dossier-grid">
                        <div className="detail-dossier-item">
                          <span>人物介绍</span>
                          <p>{compactIntro(currentGuide?.roleBrief, 92)}</p>
                        </div>
                        <div className="detail-dossier-item">
                          <span>历史位置</span>
                          <p>{compactIntro(scenarioSeed.historical_anchor, 92)}</p>
                        </div>
                      </div>

                      <div className="detail-dossier-callout">
                        <span>入局提醒</span>
                        <p>{currentGuide?.playerFocus?.[0]}</p>
                      </div>

                      <div className="detail-dossier-focus">
                        {currentGuide?.starterConcepts?.map((item) => (
                          <span className="detail-focus-chip" key={item}>
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
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
                      <div className="guide-panel">
                        <div className="guide-tabs">
                          <button
                            className={`guide-tab ${
                              actionGuideTab === "briefing" ? "active" : ""
                            }`}
                            onClick={() => setActionGuideTab("briefing")}
                            type="button"
                          >
                            局势导览
                          </button>
                          <button
                            className={`guide-tab ${
                              actionGuideTab === "starters" ? "active" : ""
                            }`}
                            onClick={() => setActionGuideTab("starters")}
                            type="button"
                          >
                            推荐起手
                          </button>
                        </div>

                        {actionGuideTab === "briefing" ? (
                          <div className="guide-scroll">
                            <div className="subsection-head">
                              <h3>入局情报</h3>
                              <p>先理解人物、局势与目标，再决定这一回合怎么走。</p>
                            </div>

                            <div className="guide-block">
                              <h4>你是谁</h4>
                              <p>{currentGuide?.roleBrief}</p>
                            </div>

                            <div className="guide-block">
                              <h4>局势速览</h4>
                              <ul className="guide-list">
                                {currentGuide?.situationBriefs.map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="guide-block">
                              <h4>关键人物 / 势力</h4>
                              <ul className="guide-list guide-list-tight">
                                {currentGuide?.keyFigures.map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="guide-block">
                              <h4>这局先抓什么</h4>
                              <ul className="guide-list guide-list-tight">
                                {currentGuide?.playerFocus.map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="guide-mini">
                              <span className="guide-mini-label">读法建议</span>
                              <p>如果你不熟悉这段历史，优先看“局势速览”和“这局先抓什么”，再决定是稳局、借势还是抢先手。</p>
                            </div>
                          </div>
                        ) : (
                          <div className="guide-scroll">
                            <div className="subsection-head">
                              <h3>本轮建议行动</h3>
                              <p>{sessionSnapshot.next_prompt_hint}</p>
                            </div>

                            <div className="guide-concepts">
                              {currentGuide?.starterConcepts.map((item) => (
                                <span className="guide-concept-chip" key={item}>
                                  {item}
                                </span>
                              ))}
                            </div>

                            <div className="opening-option-list">
                              {(sessionSnapshot.suggested_options ?? scenarioSeed.initial_options).map((option) => (
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
                        )}
                      </div>
                    </div>

                    <div className="draft-panel">
                      <div className="subsection-head">
                        <h3>你的决策</h3>
                        <p>
                          {selectedOptionId
                            ? `已绑定本轮建议：${selectedOptionId}`
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
                            : actionGuideTab === "briefing"
                              ? "先看左侧入局情报，再决定这回合怎么走"
                              : "你可以直接采用左侧推荐起手，或自行发挥"}
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
                      <span className="panel-kicker">
                        {isViewingLatest ? "最新推演结果" : "历史回合战报"}
                      </span>
                      <h2>{activeTurn ? `第 ${activeTurn.turn_index} 回合战报总览` : "本轮战报总览"}</h2>
                    </div>
                    <span className="result-time">
                      {activeTurn
                        ? `${isViewingLatest ? "最新回合" : "当前选中"} · ${formatTimestamp(activeTurn.timestamp)}`
                        : "等待首个回合"}
                    </span>
                  </div>

                  {sessionEnded && currentEnding ? (
                    <article className="ending-card">
                      <div className="ending-head">
                        <span className="ending-kicker">阶段性结局</span>
                        <span className="ending-turns">
                          本局已走完 {sessionSnapshot.session.turn_index} / 10 回合
                        </span>
                      </div>
                      {currentEndingSummary ? (
                        <div className="ending-grid">
                          <div className="ending-cell ending-cell-full">
                            <h3>本局总评</h3>
                            <p>{currentEndingSummary.appraisal}</p>
                          </div>
                          <div className="ending-cell">
                            <h3>本局路线</h3>
                            <p>{currentEndingSummary.route}</p>
                          </div>
                          <div className="ending-cell">
                            <h3>阶段成果</h3>
                            <p>{currentEndingSummary.achievement}</p>
                          </div>
                          <div className="ending-cell">
                            <h3>遗留风险</h3>
                            <p>{currentEndingSummary.risk}</p>
                          </div>
                          <div className="ending-cell">
                            <h3>历史走向</h3>
                            <p>{currentEndingSummary.outlook}</p>
                          </div>
                        </div>
                      ) : null}
                      <p className="ending-paragraph">{currentEnding}</p>
                    </article>
                  ) : null}

                  {activeTurn ? (
                    <article className="latest-turn">
                      <div className="latest-turn-index">
                        <span>第</span>
                        <strong>{String(activeTurn.turn_index).padStart(2, "0")}</strong>
                        <span>回合</span>
                      </div>

                      <div className="latest-turn-content">
                        <div className="latest-grid">
                          <div className="latest-cell">
                            <h3>回合编号</h3>
                            <p>第 {activeTurn.turn_index} 回合</p>
                          </div>
                          <div className="latest-cell">
                            <h3>玩家决策</h3>
                            <p>{activeTurn.player_action}</p>
                          </div>
                          <div className="latest-cell">
                            <h3>系统裁定模式</h3>
                            <p>{formatRuntimeMode(activeTurn.resolution_mode)}</p>
                          </div>
                          <div className="latest-cell">
                            <h3>结果摘要</h3>
                            <p>{activeTurn.outcome_summary}</p>
                          </div>
                          <div className="latest-cell latest-wide">
                            <h3>世界变化</h3>
                            <p>{activeTurn.world_update}</p>
                          </div>
                          <div className="latest-cell latest-wide accent-cell">
                            <h3>推演结果</h3>
                            <p>{activeTurn.ai_narration}</p>
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
                    <span className="panel-kicker">历史推演轨迹</span>
                    <span className="session-meta">
                      {history.length === 0 ? "尚无历史回合" : `累计 ${history.length} 条记录`}
                    </span>
                  </div>

                  <div className="history-summary">
                    <p>点击下方时间轴节点，即可在上方战报区查看对应回合的完整记录。</p>
                    {activeTurn ? (
                      <span className="history-active-badge">
                        当前查看：第 {String(activeTurn.turn_index).padStart(2, "0")} 回合
                      </span>
                    ) : null}
                  </div>

                  <div className="timeline-rail">
                    {history.length === 0 ? (
                      <div className="timeline-empty">
                        当前还没有提交任何回合。
                      </div>
                    ) : (
                      <div className="timeline-scroll">
                        <div className="timeline-track" aria-label="历史回合时间轴">
                          {history.map((entry) => {
                            const isActive = entry.turn_index === activeTurn?.turn_index;
                            const isLatest = entry.turn_index === latestTurn?.turn_index;
                            return (
                              <button
                                key={entry.turn_index}
                                className={`timeline-node ${isActive ? "active" : ""}`}
                                onClick={() => setSelectedTurnIndex(entry.turn_index)}
                                type="button"
                              >
                                <span className="timeline-node-dot" />
                                <span className="timeline-node-index">
                                  第 {String(entry.turn_index).padStart(2, "0")} 回
                                </span>
                                <strong>{entry.player_action}</strong>
                                <small>{entry.outcome_summary}</small>
                                <em>{isLatest ? "最新回合" : formatRuntimeMode(entry.resolution_mode)}</em>
                              </button>
                            );
                          })}
                        </div>
                      </div>
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
